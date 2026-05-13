from flask import Blueprint, redirect, render_template, flash, request, url_for
from config.secrets_manager import secrets_manager
from datetime import datetime, timedelta
from utils.label_factory import generate_dachser_label
from dachser_edi import CountryCode, Product, PackingType, MeasurementName, UnitCode, MeasurementType
from utils.xml_builder import create_xml

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
        for i, fattura_id in enumerate(fatture_ids):
            try:
                sigla, serie, numero, cod_conto = fattura_id.split("+")
                aspetti_esteriori_beni = mexal.get_all_aspetti_esteriori_beni()
                send(mexal, aspetti_esteriori_beni, ssccs[i], sigla, serie, numero, cod_conto)
                successi += 1
            except Exception as e:
                # In produzione è consigliato un logger (es. logging.error) per tracciare il fallimento specifico
                errori += 1

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

    current_year = datetime.now().year
    yesterday = datetime.now() - timedelta(days=1)
    yesterday_str = yesterday.strftime('%Y%m%d')
    filters = [
       ("data_documento", ">=", yesterday_str),
       ("nr_tracking", "<>", "SPEDITO"),
       ("cod_vettore", "contiene", ["606.00002", "606.00501"]),
       ("sigla_doc_orig", "contiene", ["FT", "BS", "BC"])
    ]

    properties = [
        "sigla", "serie", "numero", "cod_conto",
        "data_documento", "sigla_doc_orig", "numero_doc_orig", "nr_colli_sped", "peso_spedizione", "asp_est_beni", "cod_anag_sped"]
    fatture = mexal.find_warehouse_movements(str(current_year), properties=properties, filters=filters)
    aspetti_esteriori_beni = mexal.get_all_aspetti_esteriori_beni()
    for f in fatture:
        cliente = mexal.get_customer_by_mexal_code(f["cod_conto"])
        f["id"] = f"{f['sigla']}+{f['serie']}+{f['numero']}+{f['cod_conto']}"
        f["ragione_sociale_cliente"] = cliente.get("ragione_sociale", "") if cliente else "Cliente non trovato"
        f["data_documento"] = datetime.strptime(f["data_documento"], "%Y%m%d").strftime("%d/%m/%Y")
        f["asp_est_beni"] = aspetti_esteriori_beni.get(f["asp_est_beni"], "???")

    return render_template("fercam.html", fatture = fatture)

def print_label(sscc, fattura):
    date = datetime.now().strftime("%d/%m/%y")
    label_counter = 0
    label_total = 10
    ragione_sociale = ""
    via = ""
    cap_citta_provincia = ""
    stato = ""
    show_personal_zucchero = True
    generate_dachser_label(sscc, date, label_counter, label_total, ragione_sociale, via, cap_citta_provincia, stato, show_personal_zucchero)

def get_indirizzo_spedizione(mexal, fattura, cliente):
    '''
    Se è presente un indirizzo di spedizione nell'anagrafica specifica, uso quello, altrimenti uso le informazioni dell'anagrafica cliente.
    I campi indirizzo, cap, localita, provincia e cod_paese sono presenti in entrambi i casi.
    '''
    indirizzo_spedizione = None
    if fattura["cod_anag_sped"]:
        indirizzo_spedizione = mexal.get_indirizzo_di_spedizione(fattura["cod_anag_sped"])
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
        note_spedizione = mexal.get_note_indirizzi_spedizione_by_address_id(fattura["cod_anag_sped"])
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
        cliente = mexal.get_customer_by_mexal_code(fattura["cod_conto"])
        indirizzo_spedizione = get_indirizzo_spedizione(mexal, fattura, cliente)
        note = get_note(mexal, fattura)

        fattura["ragione_sociale_cliente"] = cliente.get("ragione_sociale", "") if cliente else "Cliente non trovato"
        fattura["data_documento"] = datetime.strptime(fattura["data_documento"], "%Y%m%d").strftime("%d/%m/%Y")
        fattura["asp_est_beni"] = aspetti_esteriori_beni.get(fattura["asp_est_beni"], "???")
        fattura["indirizzo_spedizione"] = indirizzo_spedizione["descrizione"] if indirizzo_spedizione else "???"
        fattura["note"] = note

        spedizione = {
            "doc_id": "12345", #5 caratteri che decidiamo noi
            "reference": "DDT Ordine o fattura (max 35)",
            "consignee": {
                "name": "Mario Rossi SPA",
                "street": "Via Milano 15",
                "city": "Milano",
                "postal_code": "20100",
                "country_code": CountryCode.IT,
                "contact": {"name": "Mario", "phone": "123456"}
            },
            "forwarder": {
                "id": "9999999" # ci deve dare il valore esatto da mettere
            },
            "product": Product.TARGOFLEX, # O targospeed in alcuni rari casi, da verificare sul codice vettore
            "items": [
                {
                    "quantity": 1, #numeri di cartoni, pallet a perdere o pallet a scambio, a seconda del packing type
                    "type": PackingType.EURO_PALLET, #variabile, info presente in fattura
                    "description": "Descrizione del prodotto.",
                    "measurements": [
                        { "name": MeasurementName.WEIGHT, "value": 20, "unit": UnitCode.KILOGRAM, "code": MeasurementType.GROSS_WEIGHT }, #presente in fattura
                    ]
                },
            ],
            "sscc": sscc,
        }
        xml = create_xml(spedizione)
        print(xml)
        # print_label(sscc)
        # update_nr_tracking(mexal, sigla, serie, numero, cod_conto)
        return True
    except Exception as e:
        return False