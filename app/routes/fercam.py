import xml

from flask import Blueprint, redirect, render_template, flash, request, url_for, current_app
from config.config import ZEBRA_IP
from utils.utils import send_to_zebra
from config.secrets_manager import secrets_manager
from datetime import datetime, timedelta
from utils.label_factory import generate_dachser_label
from dachser_edi import CountryCode, Product, PackingType, MeasurementName, UnitCode, MeasurementType
from utils.xml_builder import create_xml, generate_doc_id

fercam_bp = Blueprint("fercam", __name__, url_prefix="/fercam")

@fercam_bp.route("/invia", methods=["POST"])
def invia():
    singolo_id = request.form.get("fattura_id_singola")
    fatture_ids = [singolo_id] if singolo_id else request.form.getlist("fatture_selezionate")

    if not fatture_ids:
        flash("Nessun documento selezionato per l'invio.", "error")
        return redirect(url_for("fercam.fercam"))

    try:
        mexal = secrets_manager.get_mexal()
        if not mexal:
            flash("Errore nelle credenziali Mexal.", "error")
            return redirect(url_for("fercam.fercam"))

        successi = 0
        errori = 0

        sscc_generator = secrets_manager.get_sscc_generator()
        ssccs = sscc_generator.get_ssccs(len(fatture_ids))
        xmls = []
        for i, fattura_id in enumerate(fatture_ids):
            try:
                sigla, serie, numero, cod_conto = fattura_id.split("+")
                aspetti_esteriori_beni = mexal.get_all_aspetti_esteriori_beni()
                id, xml = send(mexal, aspetti_esteriori_beni, ssccs[i], sigla, serie, numero, cod_conto)
                if xml:
                    xmls.append((id,xml))
                successi += 1
            except Exception as e:
                # In produzione è consigliato un logger (es. logging.error) per tracciare il fallimento specifico
                errori += 1

        with secrets_manager.get_fercam_sftp() as sftp:
            for id, xml in xmls:
                filename = f"{id}.xml"
                # sftp.send_content(xml, filename)

        if successi > 0:
            flash(f"{successi} documenti elaborati con successo.", "success")
        if errori > 0:
            flash(f"Errore durante l'elaborazione di {errori} documenti. Verificare i log.", "error")

    except Exception as e:
        flash("Errore critico durante l'integrazione con Fercam.", "error")

    return redirect(url_for("fercam.fercam"))

@fercam_bp.route("/", methods=["GET"])
def fercam():
    mexal = secrets_manager.get_mexal()
    if not mexal:
        flash("Errore nelle credenziali Mexal.", "error")
        return render_template("fercam.html", fatture = [])

    yesterday = datetime.now() - timedelta(days=5)
    yesterday_str = yesterday.strftime('%Y%m%d')
    filters = [
       ("data_documento", ">=", yesterday_str),
       ("nr_tracking", "<>", "SPEDITO"),
       ("cod_vettore", "contiene", ["606.00002", "606.00501"]),
       ("sigla_doc_orig", "contiene", ["FT", "BS", "BC"]),
       ("id_causale", "<>", 11)
    ]

    properties = [
        "sigla", "serie", "numero", "cod_conto",
        "data_documento", "sigla_doc_orig", "numero_doc_orig", "nr_colli_sped", "peso_spedizione", "asp_est_beni", "cod_anag_sped"
    ]
    
    #Ottengo i movimenti filtrati
    fatture = mexal.find_warehouse_movements(str(datetime.now().year), properties=properties, filters=filters)

    #Ottengo le ragioni sociali dei clienti delle fatture ottenute
    clienti = mexal.find_customers(
        properties= ["codice", "ragione_sociale"],
        filters=[("codice", "=", [f["cod_conto"] for f in fatture])]
    )
    ragioni_sociali = {c["codice"]: c["ragione_sociale"] for c in clienti}
    
    aspetti_esteriori_beni = mexal.get_all_aspetti_esteriori_beni() #Ottengo gli aspetti disponibili nel gestionale
    for f in fatture:
        f["id"] = f"{f['sigla']}+{f['serie']}+{f['numero']}+{f['cod_conto']}"
        f["data_documento"] = datetime.strptime(f["data_documento"], "%Y%m%d").strftime("%d/%m/%Y")
        f["aspetto"] = aspetti_esteriori_beni.get(f["asp_est_beni"], "???")
        f["completo"] = f["aspetto"] != "???"

        cliente = ragioni_sociali.get(f["cod_conto"])
        f["ragione_sociale_cliente"] = cliente if cliente else "Cliente non trovato"

    return render_template("fercam.html", fatture = fatture)

def print_label(sscc, fattura):
    label_total = int(fattura["nr_colli_sped"][0][1]) if fattura.get("nr_colli_sped") else 1
    date = datetime.now().strftime("%d/%m/%y")
    ragione_sociale = fattura["cliente"]["ragione_sociale"]
    via = fattura["indirizzo_spedizione"]["indirizzo"]
    cap_citta_provincia = f'{fattura["indirizzo_spedizione"]["cap"]} {fattura["indirizzo_spedizione"]["localita"]} {fattura["indirizzo_spedizione"]["provincia"]}'
    stato = fattura["indirizzo_spedizione"]["cod_paese"]
    show_personal_zucchero = True
    for counter in range(1, label_total + 1):
        label = generate_dachser_label(sscc, date, counter, label_total, ragione_sociale, via, cap_citta_provincia, stato, show_personal_zucchero)
        # current_app.logger.debug(f"Generated label for SSCC {sscc}:\n{label}")
        send_to_zebra(ZEBRA_IP, label)

def get_indirizzo_spedizione(mexal, fattura, cliente):
    '''
    Se è presente un indirizzo di spedizione nell'anagrafica specifica, uso quello, altrimenti uso le informazioni dell'anagrafica cliente.
    I campi indirizzo, cap, localita, provincia e cod_paese sono presenti in entrambi i casi.
    '''
    indirizzo_spedizione = None
    if fattura["cod_anag_sped"]:
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
    return indirizzo_spedizione

def get_note(mexal, fattura):
    note = None
    if fattura["cod_anag_sped"]:
        note_spedizione = mexal.get_note_indirizzi_spedizione_by_address_id(fattura["cod_anag_sped"][0][1])
        if note_spedizione:
            note = {
                "giorno_di_chiusura": note_spedizione.get("7") or "",
                "orario_di_consegna": note_spedizione.get("2") or "",
                "orario_vietato": note_spedizione.get("3") or "",
                "avviso_da_corriere": note_spedizione.get("8") or "",
                "contatto_telefonico": note_spedizione.get("9") or "",
                "referente_scarico": note_spedizione.get("10") or "",
                "dislocazione_consegna": note_spedizione.get("4") or "",
                "aggiuntiva_1": note_spedizione.get("5") or "",
                "aggiuntiva_2": note_spedizione.get("6") or "",
            }
    else:
        note_consegna = mexal.get_note_consegna_by_customer_id(fattura["cod_conto"])
        if note_consegna:
            note = {
                "giorno_di_chiusura": note_consegna.get("2") or "",
                "orario_di_consegna": note_consegna.get("3") or "",
                "orario_vietato": note_consegna.get("4") or "",
                "avviso_da_corriere": note_consegna.get("5") or "",
                "contatto_telefonico": note_consegna.get("6") or "",
                "referente_scarico": note_consegna.get("7") or "",
                "dislocazione_consegna": note_consegna.get("8") or "",
                "aggiuntiva_1": note_consegna.get("9") or "",
                "aggiuntiva_2": note_consegna.get("10") or "",
            }
    return note

def build_xml(fattura, sscc):
    packing_type_dict = {
        1: PackingType.CARTON,
        2: PackingType.LOSS_PALLET,
        3: PackingType.EURO_PALLET,
        4: PackingType.LOSS_PALLET,
        5: PackingType.LOSS_PALLET,
        6: PackingType.SACK,
        7: None, #Non presente su mexal al 18-05-26
        8: PackingType.BARREL,
        9: None, #Non presente su mexal al 18-05-26
        10: PackingType.BIG_BAG,
        11: None, #Non presente su mexal al 18-05-26
        12: PackingType.LOSS_PALLET,
        13: PackingType.CARTON,
        14: PackingType.CARTON,
        15: PackingType.CARTON,
        16: PackingType.CARTON,
        17: PackingType.CARTON,
        18: PackingType.LOSS_PALLET,
        19: PackingType.LOSS_PALLET,
    }
    doc_id = generate_doc_id(fattura["numero"], fattura["sigla"], int(fattura["data_documento"][:4]))

    spedizione = {
            "doc_id": doc_id,
            "reference": f"{fattura['sigla']}{fattura['serie']}/{fattura['numero']}",
            "consignee": {
                "name": fattura["cliente"]["ragione_sociale"][:30],
                "street": fattura["indirizzo_spedizione"]["indirizzo"],
                "city": fattura["indirizzo_spedizione"]["localita"],
                "postal_code": fattura["indirizzo_spedizione"]["cap"],
                "country_code": CountryCode(fattura["indirizzo_spedizione"]["cod_paese"]),
                "contact": {"email": fattura["cliente"].get("email"), "phone": fattura["cliente"].get("telefono")} #1: note, 2: anagrafica spedizione o cliente
            },
            "forwarder": {
                "id": "72859708"
            },
            "product": Product.TARGOFLEX, # O targospeed in alcuni rari casi, da verificare sul codice vettore
            "items": [
                {
                    "quantity": fattura["nr_colli_sped"][0][1], #numeri di cartoni, pallet a perdere o pallet a scambio, a seconda del packing type
                    "type": packing_type_dict.get(fattura["asp_est_beni"][0][1]), #variabile, info presente in fattura
                    "description": "Prodotti monodose personalizzati.",
                    "measurements": [
                        { "name": MeasurementName.WEIGHT, "value": fattura["peso_spedizione"][0][1], "unit": UnitCode.KILOGRAM, "code": MeasurementType.GROSS_WEIGHT }, #presente in fattura
                    ]
                },
            ],
            "notes": "; ".join([f"{k}: {v}" for k, v in fattura.get("note", {}).items() if v]),
            "tail_lift_required": False,
            "sscc": sscc,
        }
    #SPONDA, facchinaggio, ZTL, consegna al piano, preavviso
    xml = create_xml(spedizione)
    return doc_id, xml

def update_nr_tracking(mexal, sigla, serie, numero, cod_conto):
    payload = {
        "nr_tracking": [
            [1, "SPEDITO"]
        ]
    }
    mexal.update_warehouse_movement(str(datetime.now().year), sigla, serie, numero, cod_conto, payload)

def send(mexal, aspetti_esteriori_beni, sscc, sigla, serie, numero, cod_conto):
    try:
        fattura = mexal.get_single_warehouse_movement(str(datetime.now().year), sigla, serie, numero, cod_conto)
        if not fattura:
            raise Exception("Errore nel recupero dei dati della fattura.")

        note = get_note(mexal, fattura)
        if not note:
            raise Exception("Errore nel recupero delle note di consegna/spedizione.")

        cliente = mexal.get_customer_by_mexal_code(fattura["cod_conto"])
        if not cliente:
            raise Exception("Errore nel recupero dei dati cliente.")
        
        indirizzo_spedizione = get_indirizzo_spedizione(mexal, fattura, cliente)
        if not indirizzo_spedizione:
            raise Exception("Errore nel recupero dell'indirizzo di spedizione.")
        
        fattura["aspetto"] = aspetti_esteriori_beni.get(fattura["asp_est_beni"][0][1], "???")
        fattura["note"] = note
        fattura["cliente"] = cliente
        fattura["indirizzo_spedizione"] = indirizzo_spedizione

        doc_id, xml = build_xml(fattura, sscc)
        
        print_label(sscc, fattura)
        # update_nr_tracking(mexal, sigla, serie, numero, cod_conto)
        return doc_id, xml
    except Exception as e:
        current_app.logger.error(f"Error occurred while sending Fercam data: {e}")
        return None