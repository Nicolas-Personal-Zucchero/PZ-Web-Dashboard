from flask import Blueprint, redirect, render_template, flash, request, url_for, current_app
from config.constants import ZEBRA_IP
from utils.utils import send_to_zebra
from config.secrets_manager import secrets_manager
from datetime import datetime, timedelta
from utils.label_factory import generate_dachser_label
from dachser_edi import CountryCode, Product, MeasurementName, UnitCode, MeasurementType
from utils.xml_builder import create_xml, generate_doc_id
from utils.RedisMexalCache import RedisMexalCache
from config.constants import PACKING_TYPE_MAP, PACKING_TYPE_ICONS, LABEL_TYPE_MAP, ID_PAGAMENTI_ALLA_CONSEGNA

mexal_cache = RedisMexalCache()
fercam_bp = Blueprint("fercam", __name__, url_prefix="/fercam")

@fercam_bp.route("/", methods=["GET"])
def fercam():
    mexal = secrets_manager.get_mexal()
    if not mexal:
        flash("Errore nelle credenziali Mexal.", "danger")
        return render_template("fercam.html", fatture=[])

    yesterday_str = (datetime.now() - timedelta(days=1)).strftime('%Y%m%d')
    filters = [
       ("data_documento", ">=", yesterday_str),
       ("nr_tracking", "<>", "SPEDITO"),
       ("cod_vettore", "contiene", ["606.00002", "606.00501"]),
       ("sigla_doc_orig", "contiene", ["FT", "BS", "BC"]),
       ("id_causale", "<>", 11),
       ("utente_ult_mod", "<>", "0") # Filtro per escludere i movimenti duplicati
    ]

    properties = [
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

    for f in fatture:
        f["id"] = f"{f['sigla']}+{f['serie']}+{f['numero']}+{f['cod_conto']}"
        f["data_documento"] = datetime.strptime(f["data_documento"], "%Y%m%d").strftime("%d/%m/%Y")

        f["ragione_sociale_cliente"] = ragioni_sociali.get(f["cod_conto"]) or "Cliente non trovato"

        f["aspetto"] = mexal_cache.get_aspetto_esteriore(mexal, f["asp_est_beni"]) or "???"
        f["aspetto_icon"] = PACKING_TYPE_ICONS.get(PACKING_TYPE_MAP.get(int(f["asp_est_beni"])), "bi bi-question-circle text-muted")

        f["cod"] = f["id_pagamento"] in ID_PAGAMENTI_ALLA_CONSEGNA

        f["completo"] = f["aspetto"] != "???"

    return render_template("fercam.html", fatture=fatture)

@fercam_bp.route("/invia", methods=["POST"])
def invia():
    singolo_id = request.form.get("fattura_id_singola")
    fatture_ids = [singolo_id] if singolo_id else request.form.getlist("fatture_selezionate")

    if not fatture_ids:
        flash("Nessun documento selezionato per l'invio.", "danger")
        return redirect(url_for("fercam.fercam"))

    try:
        mexal = secrets_manager.get_mexal()
        if not mexal:
            raise ValueError("Errore nelle credenziali Mexal.")

        sscc_generator = secrets_manager.get_sscc_generator()
        if not sscc_generator:
            raise ValueError("Errore nelle credenziali per la generazione degli SSCC.")

        ssccs = sscc_generator.get_ssccs(len(fatture_ids))
        if not ssccs:
            raise RuntimeError("Errore nella generazione degli SSCC.")

        errori = []
        xmls = []
        for i, fattura_id in enumerate(fatture_ids):
            sigla, serie, numero, cod_conto = fattura_id.split("+")
            try:
                id, xml = process_and_send(mexal, ssccs[i], sigla, serie, numero, cod_conto)
                if xml:
                    xmls.append((id,xml))
            except Exception as e:
                current_app.logger.error(f"Errore fattura {fattura_id}: {e}")
                errori.append((f"{sigla} {serie}/{numero}", str(e)))

        # if xmls:
        #     with secrets_manager.get_fercam_sftp(test_server=True) as sftp:
        #         for id, xml in xmls:
        #             filename = f"{id}.xml"
        #             try:
        #                 current_app.logger.info(f"Invio {filename} a Fercam...")
        #                 sftp.send_content(xml, filename)
        #             except Exception as e:
        #                 current_app.logger.error(f"Errore nell'invio del file {filename} a Fercam: {e}")
        #                 errori.append((filename, f"Errore nell'invio a Fercam: {str(e)}"))

        for fattura_id, error_msg in errori:
            flash(f"Errore fattura {fattura_id}: {error_msg}", "danger")
        
        if not errori and xmls:
            flash(f"Documenti elaborati e inviati con successo. Etichette stampate", "success")

    except Exception as e:
        flash(f"Errore critico durante l'integrazione con Fercam: {e}", "danger")

    return redirect(url_for("fercam.fercam"))

def print_label(sscc, fattura):
    id = f"{fattura['sigla']} {fattura['serie']}/{fattura['numero']}"

    label_total = int(fattura["nr_colli_sped"][0][1]) if fattura.get("nr_colli_sped") else 1
    date_str = datetime.now().strftime("%d/%m/%y")
    ragione_sociale = fattura["cliente"]["ragione_sociale"]

    via = fattura["indirizzo_spedizione"]["indirizzo"]
    cap_citta_prov = f'{fattura["indirizzo_spedizione"]["cap"]} {fattura["indirizzo_spedizione"]["localita"]} {fattura["indirizzo_spedizione"]["provincia"]}'
    stato = fattura["indirizzo_spedizione"]["cod_paese"]

    show_personal_zucchero = LABEL_TYPE_MAP.get(fattura.get("tipologia_etichetta"))
    for counter in range(label_total, 0, -1):
        label = generate_dachser_label(
            sscc, id, date_str, counter, label_total,
            ragione_sociale, via, cap_citta_prov, stato,
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

    return {
        "giorno_di_chiusura": sorgente.get("7" if is_indirizzo else "2") or "",
        "orario_di_consegna": sorgente.get("2" if is_indirizzo else "3") or "",
        "orario_vietato":     sorgente.get("3" if is_indirizzo else "4") or "",
        "avviso_da_corriere": sorgente.get("8" if is_indirizzo else "5") or "",
        "contatto_telefonico":sorgente.get("9" if is_indirizzo else "6") or "",
        "referente_scarico":  sorgente.get("10" if is_indirizzo else "7") or "",
        "dislocazione_consegna": sorgente.get("4" if is_indirizzo else "8") or "",
        "aggiuntiva_1": sorgente.get("5" if is_indirizzo else "9") or "",
        "aggiuntiva_2": sorgente.get("6" if is_indirizzo else "10") or "",
        "preavviso": sorgente.get("11"),
        "facchinaggio": sorgente.get("12"),
        "sponda": sorgente.get("13"),
        "GDO": sorgente.get("14"),
        "sbancalamento": sorgente.get("15")
    }

def get_altre_note(mexal, cliente: dict) -> str:
    if not cliente:
        return None

    current_app.logger.warning("MX: Recupero altre note cliente.")
    altre_note = mexal.get_altre_note_gestionali_by_customer_id(cliente.get("codice"))
    if not altre_note:
        return None

    return altre_note.get("3") or ""

def build_xml(fattura, sscc):
    doc_id = generate_doc_id(fattura["numero"], fattura["sigla"], int(fattura["data_documento"][:4]))

    notes = [
            f"{k}: {v}" 
            for k, v in fattura.get("note", {}).items() 
            if v and v not in ["S", "N"] # Escludiamo le note boolean che indicherebbero la presenza di un servizio, per evitare confusione con i servizi stessi
        ]

    if fattura.get("facchinaggio") == "S":
        notes.append("Servizio di Facchinaggio richiesto")

    if fattura.get("GDO") == "S":
        notes.append("Consegna GDO richiesta")

    if fattura.get("sbancalamento") == "S":
        notes.append("Servizio di Sbancalamento richiesto")

    spedizione = {
            "doc_id": doc_id,
            "reference": f"{fattura['sigla']} {fattura['serie']}/{fattura['numero']}",
            "consignee": {
                "name": fattura["cliente"]["ragione_sociale"][:90], #90 char is the limitation for PartnerName in Dachser's system, splitted in 3 lines of 30 char each, so we take the first 90 char to avoid errors
                "street": fattura["indirizzo_spedizione"]["indirizzo"],
                "city": fattura["indirizzo_spedizione"]["localita"],
                "postal_code": fattura["indirizzo_spedizione"]["cap"],
                "country_code": CountryCode(fattura["indirizzo_spedizione"]["cod_paese"]),
                "contact": {"email": fattura["cliente"].get("email"), "phone": fattura["cliente"].get("telefono")} #1: note, 2: anagrafica spedizione o cliente
            },
            "forwarder": {
                "id": "956" # Codice fisso fornito da loro
            },
            "product": Product.TARGOFLEX, # O targospeed in alcuni rari casi, da verificare sul codice vettore
            "items": [
                {
                    "quantity": fattura["nr_colli_sped"][0][1], #numeri di cartoni, pallet a perdere o pallet a scambio, a seconda del packing type
                    "type": PACKING_TYPE_MAP.get(fattura["asp_est_beni"][0][1]), #variabile, info presente in fattura
                    "description": "Prodotti monodose personalizzati.",
                    "measurements": [
                        { "name": MeasurementName.WEIGHT, "value": fattura["peso_spedizione"][0][1], "unit": UnitCode.KILOGRAM, "code": MeasurementType.GROSS_WEIGHT }, #presente in fattura
                    ]
                },
            ],
            "notes": notes,
            "tail_lift_required": fattura.get("note", {}).get("sponda") == "S",
            "cod_amount": fattura.get("cod_amount"),
            "sscc": sscc,
        }
    #SPONDA, facchinaggio, ZTL, consegna al piano, preavviso e GDO grande distribuzione
    xml = create_xml(spedizione)
    return doc_id, xml

def update_nr_tracking(mexal, sigla, serie, numero, cod_conto):
    payload = {"nr_tracking": [[1, "SPEDITO"]]}
    current_app.logger.warning("MX: Aggiornamento numero di tracking.")
    mexal.update_warehouse_movement(str(datetime.now().year), sigla, serie, numero, cod_conto, payload)

def process_and_send(mexal, sscc, sigla, serie, numero, cod_conto):
    current_app.logger.warning("MX: Recupero dettaglio singolo movimenti di magazzino.")
    fattura = mexal.get_single_warehouse_movement(str(datetime.now().year), sigla, serie, numero, cod_conto)
    if not fattura:
        raise Exception("Errore nel recupero dei dati della fattura.")

    cliente = mexal_cache.get_customers(mexal, [fattura["cod_conto"]]).get(fattura["cod_conto"])
    if not cliente:
        raise Exception("Errore nel recupero dei dati cliente.")
    
    indirizzo_spedizione = get_indirizzo_spedizione(mexal, fattura, cliente)
    if not indirizzo_spedizione:
        raise Exception("Errore nel recupero dell'indirizzo di spedizione.")
    
    fattura["cliente"] = cliente
    fattura["indirizzo_spedizione"] = indirizzo_spedizione
    fattura["note"] = get_note(mexal, fattura) or {} # Note può essere None se non è mai stato valorizzata nessuna delle tabelle mydb
    fattura["tipologia_etichetta"] = get_altre_note(mexal, cliente) or {}

    if str(fattura["id_pagamento"]) in ID_PAGAMENTI_ALLA_CONSEGNA:
        fattura["cod_amount"] = sum(doc[1] for doc in fattura["tot_doc_pagare"])

    doc_id, xml = build_xml(fattura, sscc)
    current_app.logger.info(f"XML generato per {sigla} {serie}/{numero}. {fattura} \n\n\n{xml}")
    # print_label(sscc, fattura)
    # update_nr_tracking(mexal, sigla, serie, numero, cod_conto)
    return doc_id, xml