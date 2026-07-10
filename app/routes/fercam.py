import json
import copy
from decimal import Decimal
from flask import Blueprint, redirect, render_template, flash, request, url_for, current_app, jsonify
from config.constants import ITALY_TZ, ZEBRA_IP
from utils.utils import send_to_zebra, sanitize_phone_data
from config.secrets_manager import secrets_manager
from datetime import datetime, timedelta
from utils.label_factory import generate_dachser_label
from dachser_edi import CountryCode, Product, MeasurementName, UnitCode, MeasurementType
from utils.xml_builder import create_xml, generate_doc_id
from utils.RedisMexalCache import RedisMexalCache
from config.constants import PACKING_TYPE_MAP, PACKING_TYPE_ICONS, LABEL_TYPE_MAP, ID_PAGAMENTI_ALLA_CONSEGNA
from utils.database import db, SpedizionePreliminare, SpedizioneIdentificativo

DAYS_TO_FETCH = 5
mexal_cache = RedisMexalCache()
fercam_bp = Blueprint("fercam", __name__, url_prefix="/fercam")

@fercam_bp.route("/", methods=["GET"])
def fercam():
    identificativi = (
        SpedizioneIdentificativo.query
        .join(SpedizionePreliminare, SpedizioneIdentificativo.spedizione_id == SpedizionePreliminare.id)
        .all()
    )
    identificativi_sent = {
        f"{i.sigla} {i.serie}/{i.numero}"
        for i in identificativi
        if i.spedizione.sent is True
    }
    identificativi_non_sent = {
        f"{i.sigla} {i.serie}/{i.numero}"
        for i in identificativi
        if i.spedizione.sent is not True
    }

    mexal = secrets_manager.get_mexal()
    if not mexal:
        flash("Errore nelle credenziali Mexal.", "danger")
        return render_template("fercam.html", fatture=[])

    starting_date_str = (datetime.now() - timedelta(days=DAYS_TO_FETCH)).strftime('%Y%m%d')
    filters = [
       ("data_documento", ">=", starting_date_str),
    #    ("nr_tracking", "<>", "SPEDITO"), #Replaced with local db check to avoid missing documents that have been sent but not yet marked as SPEDITO in Mexal
       ("cod_vettore", "contiene", ["606.00002", "606.00501"]),
       ("sigla_doc_orig", "contiene", ["FT", "BS", "BC"]),
       ("cod_modulo", "<>", "F"), #Escludere le FTF
       ("id_causale", "<>", 11), #Rimuovi fatture anticipe
       ("id_causale", "<>", 12), #Rimuovi fatture acconto
       ("utente_ult_mod", "<>", "0") # Filtro per escludere i movimenti duplicati
    ]

    properties = [
        "data_ult_mod",
        "sigla", "serie", "numero", "cod_conto",
        "data_documento", "nr_colli_sped", "peso_spedizione",
        "asp_est_beni", "cod_anag_sped", "id_pagamento"
    ]

    #Ottengo i movimenti filtrati
    current_app.logger.warning("MX: Recupero movimenti di magazzino.")
    fatture = mexal.find_warehouse_movements(str(datetime.now().year), properties=properties, filters=filters)
    codici_conto = [f["cod_conto"] for f in fatture]

    #Ottengo le ragioni sociali dei clienti delle fatture ottenute
    clienti = mexal_cache.get_customers(mexal, codici_conto)
    ragioni_sociali = {k: v["ragione_sociale"] for k, v in clienti.items()}

    fatture_filtrate = []
    for f in fatture:
        f["id"] = f"{f['sigla']}+{f['serie']}+{f['numero']}+{f['cod_conto']}"
        f["identificativo"] = f"{f['sigla']} {f['serie']}/{f['numero']}"

        if f["identificativo"] in identificativi_sent:
            continue

        f["data_documento"] = datetime.strptime(f["data_documento"], "%Y%m%d").strftime("%d/%m/%Y")

        f["ragione_sociale_cliente"] = ragioni_sociali.get(f["cod_conto"]) or "Cliente non trovato"

        f["aspetto"] = mexal_cache.get_aspetto_esteriore(mexal, f["asp_est_beni"]) or "???"
        f["aspetto_icon"] = PACKING_TYPE_ICONS.get(PACKING_TYPE_MAP.get(int(f["asp_est_beni"])), "bi bi-question-circle text-muted")

        f["cod"] = f["id_pagamento"] in ID_PAGAMENTI_ALLA_CONSEGNA

        f["presente"] = f["identificativo"] in identificativi_non_sent
        f["completo"] = f["aspetto"] != "???" and f["nr_colli_sped"] != "0" and f["peso_spedizione"] != "0.0"
        fatture_filtrate.append(f)

    fatture = sorted(fatture_filtrate, key=lambda x: (
        x["data_ult_mod"] # Parlando con Erika, ha preferito un ordinamento per come le ha create lei su mexal per attaccare le etichette più velocemente
        # datetime.strptime(x["data_documento"], "%d/%m/%Y"),
        # x["sigla"],
        # x["serie"],
        # int(x["numero"]) if str(x["numero"]).isdigit() else x["numero"]
    ))
    return render_template("fercam.html", fatture=fatture)

def _safe_json_load(raw_string):
    try: return json.loads(raw_string) if raw_string else {}
    except ValueError: return {}


def create_spedizione_preliminare(doc_id, fattura_unica, xml, identificativi):
    db.session.add(SpedizionePreliminare(
        id=doc_id,
        ragione_sociale_cliente=fattura_unica["cliente"]["ragione_sociale"],
        nr_colli=fattura_unica["nr_colli_sped"][0][1],
        peso=fattura_unica["peso_spedizione"][0][1],
        cash_on_delivery=fattura_unica["cod_amount"],
        xml=xml,
        identificativi_rel=[
            SpedizioneIdentificativo(
                sigla=sigla,
                serie=serie,
                numero=numero,
                cod_conto=cod_conto
            ) for sigla, serie, numero, cod_conto in identificativi
        ]
    ))

@fercam_bp.route("/invia", methods=["POST"])
def invia():
    fatture_ids = request.form.getlist("fatture_selezionate")
    if not fatture_ids:
        flash("Nessun documento selezionato per l'invio.", "danger")
        return redirect(url_for("fercam.fercam"))

    telefoni_overrides = _safe_json_load(request.form.get("telefono_overrides", "{}"))
    nr_colli_overrides = _safe_json_load(request.form.get("nr_colli_overrides", "{}"))
    peso_overrides = _safe_json_load(request.form.get("peso_overrides", "{}"))
    cod_amount_overrides = _safe_json_load(request.form.get("cod_amount_overrides", "{}"))
    raggruppamenti = _safe_json_load(request.form.get("raggruppamenti", "{}"))

    try:
        mexal = secrets_manager.get_mexal()
        if not mexal:
            raise ValueError("Errore nelle credenziali Mexal.")

        sscc_generator = secrets_manager.get_sscc_generator()
        if not sscc_generator:
            raise ValueError("Errore nelle credenziali per la generazione degli SSCC.")

        groups = {}
        for fattura_id in fatture_ids:
            telefono_override = telefoni_overrides.get(fattura_id)
            nr_colli_override = int(nr_colli_overrides.get(fattura_id)) if nr_colli_overrides.get(fattura_id) else None
            peso_override = parse_float_amount(peso_overrides.get(fattura_id))
            cod_override = parse_float_amount(cod_amount_overrides.get(fattura_id))
            info = (fattura_id, telefono_override, nr_colli_override, peso_override, cod_override)
            group = raggruppamenti.get(fattura_id)
            groups.setdefault(group if group else fattura_id, []).append(info)

        errors = []
        elaborati = 0
        for _, fatture_batch in groups.items():
            try:
                doc_id, fattura_unica, xml, identificativi = process_fatture_group(mexal, sscc_generator, fatture_batch)
                create_spedizione_preliminare(doc_id, fattura_unica, xml, identificativi)
                elaborati += 1
            except Exception as e:
                current_app.logger.error(f"Errore : {e}")
                errors.append((f"", str(e)))

        if not errors:
            db.session.commit()

        for fattura_id, error_msg in errors:
            flash(f"Errore fattura {fattura_id}: {error_msg}", "danger")
        
        if not errors and elaborati:
            flash(f"Fatture elaborate, etichette stampate e spedizioni preliminari create.", "success")

    except Exception as e:
        current_app.logger.error(f"Errore critico durante l'integrazione con Fercam: {e}")
        flash(f"Errore critico durante l'integrazione con Fercam: {e}", "danger")

    return redirect(url_for("fercam.fercam"))

@fercam_bp.route("/preview-invio", methods=["POST"])
def preview_invio():
    payload = request.get_json(silent=True) or {}
    fatture_ids = payload.get("fatture_ids") or []

    if not fatture_ids:
        return jsonify({"message": "Nessun documento selezionato per l'anteprima."}), 400

    try:
        mexal = secrets_manager.get_mexal()
        if not mexal:
            raise ValueError("Errore nelle credenziali Mexal.")

        preview = []
        for fattura_id in fatture_ids:
            sigla, serie, numero, cod_conto = fattura_id.split("+")
            fattura = load_fattura_for_send(mexal, sigla, serie, numero, cod_conto, parziale=True)
            is_cod = str(fattura["id_pagamento"]) in ID_PAGAMENTI_ALLA_CONSEGNA
            preview.append({
                "id": fattura_id,
                "riferimento": fattura["riferimento"],
                "ragione_sociale_cliente": fattura["indirizzo_spedizione"]["descrizione"],
                "is_cod": is_cod,
                "sponda": fattura.get("note", {}).get("sponda") == "S",
                "facchinaggio": fattura.get("note", {}).get("facchinaggio") == "S",
                "GDO": fattura.get("note", {}).get("GDO") == "S",
                "sbancalamento": fattura.get("note", {}).get("sbancalamento") == "S",
                "preavviso": fattura.get("note", {}).get("preavviso") == "S",
                "telefono": sanitize_phone_data(fattura["cliente"].get("telefono")),
                "cod_amount": str(fattura.get("cod_amount") or "") if is_cod else "",
                "nr_colli_sped": fattura["nr_colli_sped"][0][1],
                "peso_spedizione": fattura["peso_spedizione"][0][1],
            })
        return jsonify({"items": preview})
    except Exception as e:
        current_app.logger.error(f"Errore anteprima invio Fercam: {e}")
        return jsonify({"message": str(e)}), 400

def print_label(ssccs, fattura):
    label_total = int(fattura["nr_colli_sped"][0][1]) if fattura.get("nr_colli_sped") else 1
    datetime_str = datetime.now(ITALY_TZ).strftime("%d/%m/%y %H:%M")

    ragione_sociale = fattura["indirizzo_spedizione"]["descrizione"]
    via = fattura["indirizzo_spedizione"]["indirizzo"]
    cap_citta_prov = f'{fattura["indirizzo_spedizione"]["cap"]} {fattura["indirizzo_spedizione"]["localita"]} {fattura["indirizzo_spedizione"]["provincia"]}'
    stato = fattura["indirizzo_spedizione"]["cod_paese"]
    contrassegno = f"Contrassegno {fattura['note']['incasso'][0]}" if "incasso" in fattura["note"] else ""

    show_personal_zucchero = LABEL_TYPE_MAP.get(fattura.get("tipologia_etichetta"), True)
    for idx in range(label_total, 0, -1):
        label = generate_dachser_label(
            ssccs[idx - 1], fattura["riferimento"], datetime_str, idx, label_total,
            ragione_sociale, via, cap_citta_prov, stato, contrassegno,
            show_personal_zucchero
        )
        send_to_zebra(ZEBRA_IP, label)

def get_indirizzo_spedizione(mexal, fattura, cliente):
    '''
    Se è presente un indirizzo di spedizione nell'anagrafica specifica, uso quello, altrimenti uso le informazioni dell'anagrafica cliente.
    I campi indirizzo, cap, localita, provincia e cod_paese sono presenti in entrambi i casi.
    '''
    indirizzo_spedizione = None
    if fattura["cod_anag_sped"]:
        current_app.logger.warning("MX: Recupero indirizzo di spedizione.")
        indirizzo_spedizione = mexal.get_indirizzo_di_spedizione(fattura["cod_anag_sped"][0][1])
    else:
        indirizzo_spedizione = {
            "descrizione": cliente.get("ragione_sociale", "") if cliente else None,
            "indirizzo": cliente.get("indirizzo", "") if cliente else None,
            "cap": cliente.get("cap", "") if cliente else None,
            "localita": cliente.get("localita", "") if cliente else None,
            "provincia": cliente.get("provincia", "") if cliente else None,
            "cod_paese": cliente.get("cod_paese", "") if cliente else None
        }

    #Se l'indirizzo è una sosta tecnica, le info sull'indirizzo di spedizione non sono valide/presenti, quindi non eseguo i controlli
    # Le informazioni saranno già nelle note sosta_tecnica_*
    if "SOSTA TECNICA" in indirizzo_spedizione.get("descrizione", "").upper():
        return indirizzo_spedizione

    required_fields = ["indirizzo", "cap", "localita", "provincia", "cod_paese"]
    missing = [f for f in required_fields if not indirizzo_spedizione.get(f)]
    if missing:
        raise ValueError(f"Campi mancanti nell'indirizzo: {', '.join(missing)}")
        
    is_paese_it = (indirizzo_spedizione["cod_paese"] == "IT")
    is_prov_ee = (indirizzo_spedizione["provincia"] == "EE")
    if is_paese_it == is_prov_ee:
        raise ValueError(f"Contraddizione Paese/Provincia: {indirizzo_spedizione['cod_paese']} / {indirizzo_spedizione['provincia']}")

    return indirizzo_spedizione

def get_note(mexal, fattura: dict) -> dict | None:
    cod_sped = fattura.get("cod_anag_sped")
    is_indirizzo = bool(cod_sped)
    
    if is_indirizzo:
        current_app.logger.warning("MX: Recupero note indirizzo di spedizione.")
        sorgente = mexal.get_note_indirizzi_spedizione_by_address_id(cod_sped[0][1])
    else:
        current_app.logger.warning("MX: Recupero note di consegna cliente.")
        sorgente = mexal.get_note_consegna_by_customer_id(fattura.get("cod_conto"))

    if not sorgente:
        return None

    get_val = lambda key_indirizzo, key_cliente: sorgente.get(key_indirizzo if is_indirizzo else key_cliente) or ""
    note = {
        "giorno_di_chiusura":   get_val("7", "2"),
        "orario_di_consegna":   get_val("2", "3"),
        "orario_vietato":       get_val("3", "4"),
        "avviso_da_corriere":   get_val("8", "5"),
        "contatto_telefonico":  get_val("9", "6"),
        "referente_scarico":    get_val("10", "7"),
        "dislocazione_consegna": get_val("4", "8"),
        "aggiuntiva_1":         get_val("5", "9"),
        "aggiuntiva_2":         get_val("6", "10"),
        "preavviso":            get_val("11", "11"),
        "facchinaggio":         get_val("12", "12"),
        "sponda":               get_val("13", "13"),
        "GDO":                  get_val("14", "14"),
        "sbancalamento":        get_val("15", "15")
    }
    if is_indirizzo:
        note["sosta_tecnica_ragione_sociale"] = get_val("16", "16")
        note["sosta_tecnica_cap"] = get_val("17", "17")
        note["sosta_tecnica_indirizzo"] = get_val("18", "18")
        note["sosta_tecnica_localita"] = get_val("19", "19")
        note["sosta_tecnica_provincia"] = get_val("20", "20")
        note["sosta_tecnica_cod_paese"] = get_val("21", "21")
    return note

def get_altre_note(mexal, cliente: dict) -> str:
    if not cliente:
        return None

    current_app.logger.warning("MX: Recupero altre note cliente.")
    altre_note = mexal.get_altre_note_gestionali_by_customer_id(cliente.get("codice"))
    if not altre_note:
        return None

    return altre_note.get("3") or ""

def build_xml(fattura, ssccs):
    doc_id = generate_doc_id(fattura["numero"], fattura["sigla"], int(fattura["data_documento"][:4]))

    # Note e servizi accessori
    notes = [
            f"{k.capitalize()}: {v}" 
            for k, v in fattura.get("note", {}).items() 
            if v and v not in ["S", "N"] and "sosta_tecnica" not in k # Escludiamo le note boolean che indicherebbero la presenza di un servizio, che inserisco successivamente in modo più leggibile e evito di inserire le note relative alla sosta tecnica, che come indirizzo
        ]

    if fattura.get("note", {}).get("facchinaggio") == "S":
        notes.append("Servizio di Facchinaggio richiesto")

    if fattura.get("note", {}).get("GDO") == "S":
        notes.append("Consegna GDO richiesta")

    if fattura.get("note", {}).get("sbancalamento") == "S":
        notes.append("Servizio di Sbancalamento richiesto")

    if "SOSTA TECNICA" in fattura.get("indirizzo_spedizione", {}).get("descrizione", "").upper():
        name = fattura.get("note", {}).get("sosta_tecnica_ragione_sociale")
        street = fattura.get("note", {}).get("sosta_tecnica_indirizzo")
        city = fattura.get("note", {}).get("sosta_tecnica_localita")
        postal_code = fattura.get("note", {}).get("sosta_tecnica_cap")
        country_code = fattura.get("note", {}).get("sosta_tecnica_cod_paese")
    else:
        name = fattura.get("indirizzo_spedizione", {}).get("descrizione", "")
        street = fattura["indirizzo_spedizione"]["indirizzo"]
        city = fattura["indirizzo_spedizione"]["localita"]
        postal_code = fattura["indirizzo_spedizione"]["cap"]
        country_code = fattura["indirizzo_spedizione"]["cod_paese"]

    spedizione = {
            "doc_id": doc_id,
            "reference": f"{fattura['sigla']} {fattura['serie']}/{fattura['numero']}",
            "consignee": {
                "name": name[:90], #90 char is the limitation for PartnerName in Dachser's system, splitted in 3 lines of 30 char each, so we take the first 90 char to avoid errors
                "street": street,
                "city": city,
                "postal_code": postal_code,
                "country_code": CountryCode(country_code),
                "contact": {"email": fattura["cliente"].get("email"), "phone": fattura["cliente"].get("telefono")}, #1: note, 2: anagrafica spedizione o cliente
                "type": "AT" if fattura.get("note", {}).get("preavviso") == "S" else None #Impostato AT perchè gli altri non ancora attivi (11/06/26)
            },
            "forwarder": {
                "id": "956" # Codice fisso fornito da loro
            },
            "product": Product.TARGOFLEX, # O targospeed in alcuni rari casi, da verificare sul codice vettore
            "items": [
                {
                    "quantity": fattura["nr_colli_sped"][0][1], #numeri di cartoni, pallet a perdere o pallet a scambio, a seconda del packing type
                    "type": PACKING_TYPE_MAP.get(fattura["asp_est_beni"][0][1]), #variabile, info presente in fattura
                    "description": "Prodotti personalizzati per la ristorazione.",
                    "measurements": [
                        { "name": MeasurementName.WEIGHT, "value": fattura["peso_spedizione"][0][1], "unit": UnitCode.KILOGRAM, "code": MeasurementType.GROSS_WEIGHT }, #presente in fattura
                    ]
                },
            ],
            "notes": notes,
            "tail_lift_required": fattura.get("note", {}).get("sponda") == "S",
            "cod_amount": fattura.get("cod_amount"),
            "ssccs": ssccs,
        }
    xml = create_xml(spedizione)
    return doc_id, xml


def parse_float_amount(value):
    if value in (None, ""):
        return None

    if isinstance(value, (int, float, Decimal)):
        return Decimal(str(value))

    normalized = str(value).strip().replace(",", ".")
    try:
        return Decimal(normalized)
    except Exception:
        current_app.logger.error(f"Importo float non valido: {value}")
        raise ValueError("Importo float non valido.")


def load_fattura_for_send(mexal, sigla, serie, numero, cod_conto, parziale=False):
    current_app.logger.warning("MX: Recupero dettaglio singolo movimenti di magazzino.")
    fattura = mexal.get_single_warehouse_movement(str(datetime.now().year), sigla, serie, numero, cod_conto)
    if not fattura:
        raise Exception("Errore nel recupero dei dati della fattura.")
    fattura["riferimento"] = f"{fattura['sigla']} {fattura['serie']}/{fattura['numero']}"

    cliente = mexal_cache.get_customers(mexal, [fattura["cod_conto"]]).get(fattura["cod_conto"])
    if not cliente:
        raise Exception("Errore nel recupero dei dati cliente.")
    fattura["cliente"] = cliente

    fattura["note"] = get_note(mexal, fattura) or {}

    #Rimpiazzo il numero di telefono dell'anagrafica cliente con quello presente nelle note di spedizione, se presente e non vuoto, altrimenti lascio quello dell'anagrafica cliente
    contatto_note = fattura.get("note", {}).get("contatto_telefonico")
    contatto_cliente = fattura.get("cliente", {}).get("telefono")
    fattura["cliente"]["telefono"] = contatto_note[:25] if contatto_note and str(contatto_note).strip() else contatto_cliente

    if str(fattura["id_pagamento"]) in ID_PAGAMENTI_ALLA_CONSEGNA:
        fattura["cod_amount"] = sum(Decimal(str(doc[1])) for doc in fattura["tot_doc_pagare"])
    else:
        fattura["cod_amount"] = None

    indirizzo_spedizione = get_indirizzo_spedizione(mexal, fattura, cliente)
    if not indirizzo_spedizione:
        raise Exception("Errore nel recupero dell'indirizzo di spedizione.")
    fattura["indirizzo_spedizione"] = indirizzo_spedizione

    if not parziale:
        fattura["tipologia_etichetta"] = get_altre_note(mexal, cliente) or ""

    return fattura

def process_fatture_group(mexal, sscc_generator, fatture_info):
    fatture = []
    identificativi = []
    last_id_pagamento = None

    for fid, telefono_override, nr_colli_override, peso_override, cod_amount_override in fatture_info:
        sigla, serie, numero, cod_conto = fid.split("+")
        f = load_fattura_for_send(mexal, sigla, serie, numero, cod_conto)
        
        if last_id_pagamento is not None and str(f["id_pagamento"]) != last_id_pagamento:
            raise ValueError("Non è possibile raggruppare fatture con modalità di pagamento diverse.")
        last_id_pagamento = str(f["id_pagamento"])

        # Override individuali
        if telefono_override is not None: f["cliente"]["telefono"] = telefono_override
        if nr_colli_override is not None: f["nr_colli_sped"][0][1] = nr_colli_override
        if peso_override is not None: f["peso_spedizione"][0][1] = peso_override
        if cod_amount_override is not None and str(f.get("id_pagamento")) in ID_PAGAMENTI_ALLA_CONSEGNA: f["cod_amount"] = cod_amount_override
        
        fatture.append(f)
        identificativi.append((sigla, serie, numero, cod_conto))

    merged = copy.deepcopy(fatture[0])
    
    #Aggiunta della modalità di incasso del contrassegno nelle note, se presente
    if last_id_pagamento in ID_PAGAMENTI_ALLA_CONSEGNA:
        if last_id_pagamento == "202":
            merged["note"]["incasso"] = "C - Contanti"
        else:
            merged["note"]["incasso"] = "R - Titolo come rilasciato"

    for f in fatture[1:]:
        merged["nr_colli_sped"][0][1] += f["nr_colli_sped"][0][1]
        merged["peso_spedizione"][0][1] += f["peso_spedizione"][0][1]
        if f.get("cod_amount") is not None:
            merged["cod_amount"] = (merged.get("cod_amount") or Decimal(0)) + f["cod_amount"]
        merged["riferimento"] += f" \&{f['riferimento']}"

    ssccs = sscc_generator.get_ssccs(merged["nr_colli_sped"][0][1])
    if not ssccs:
        raise RuntimeError("Errore nella generazione degli SSCC.")
    
    doc_id, xml = build_xml(merged, ssccs)
    print_label(ssccs, merged)
    
    return doc_id, merged, xml, identificativi