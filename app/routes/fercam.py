from flask import Blueprint, render_template, flash
from config.secrets_manager import secrets_manager
from datetime import datetime, timedelta

fercam_bp = Blueprint("fercam", __name__, url_prefix="/fercam")

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
       ("nr_tracking", "=", ""),
       ("cod_vettore", "contiene", ["606.00002", "606.00501"]),
       ("sigla_doc_orig", "contiene", ["FT", "BS", "BC"])
    ]

    properties = ["data_documento", "sigla_doc_orig", "numero_doc_orig", "cod_conto", "nr_colli_sped", "peso_spedizione", "asp_est_beni", "cod_anag_sped"]
    fatture = mexal.find_warehouse_movements(str(current_year), properties=properties, filters=filters)
    aspetti_esteriori_beni = mexal.get_all_aspetti_esteriori_beni()
    for f in fatture:
        cliente = mexal.get_customer_by_mexal_code(f["cod_conto"])

        '''
        Se è presente un indirizzo di spedizione nell'anagrafica specifica, uso quello, altrimenti uso le informazioni dell'anagrafica cliente.
        I campi indirizzo, cap, localita, provincia e cod_paese sono presenti in entrambi i casi.
        '''
        note_spedizione = None
        note_consegna = None
        note = {
                "giorno_di_chiusura": "",
                "orario_di_consegna": "",
                "orario_vietato": "",
                "avviso_da_corriere": "",
                "contatto_telefonico": "",
                "referente_scarico": "",
                "dislocazione_consegna": "",
                "aggiuntiva_1": "",
                "aggiuntiva_2": "",
            }
        if f["cod_anag_sped"]:
            indirizzo_spedizione = mexal.get_indirizzo_di_spedizione(f["cod_anag_sped"])
            note_spedizione = mexal.get_note_indirizzi_spedizione_by_address_id(f["cod_anag_sped"])
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
            indirizzo_spedizione = {
                "descrizione": cliente.get("ragione_sociale", "") if cliente else None,
                "indirizzo": cliente.get("indirizzo", "") if cliente else None,
                "cap": cliente.get("cap", "") if cliente else None,
                "localita": cliente.get("localita", "") if cliente else None,
                "provincia": cliente.get("provincia", "") if cliente else None,
                "cod_paese": cliente.get("cod_paese", "") if cliente else None
            }
            note_consegna = mexal.get_note_consegna_by_customer_id(f["cod_conto"])
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

        f["ragione_sociale_cliente"] = cliente.get("ragione_sociale", "") if cliente else "Cliente non trovato"
        f["data_documento"] = datetime.strptime(f["data_documento"], "%Y%m%d").strftime("%d/%m/%Y")
        f["asp_est_beni"] = aspetti_esteriori_beni.get(f["asp_est_beni"], "???")
        f["indirizzo_spedizione"] = indirizzo_spedizione["descrizione"] if indirizzo_spedizione else "???"

    return render_template("fercam.html", fatture = fatture)