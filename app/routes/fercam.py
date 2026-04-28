from flask import Blueprint, render_template, flash
from config.secrets_manager import secrets_manager
from datetime import datetime

fercam_bp = Blueprint("fercam", __name__, url_prefix="/fercam")

@fercam_bp.route("/", methods=["GET"])
def fercam():

    mexal = secrets_manager.get_mexal()
    if not mexal:
        flash("Errore nelle credenziali Mexal.", "error")
        return render_template("fercam.html", fatture = [])

    properties = ["data_creazione", "sigla_doc_orig", "sigla", "numero_ordine", "data_doc_orig", "data_ordine", "cod_vettore", "nr_tracking", "data_documento"]

    #data documento
    #sigla doc orig
    #numero_doc_orig
    #ragione sociale cliente
    #colli e peso
    #asp_est_beni
    current_year = datetime.now().year
    fatture = mexal.get_warehouse_movements(str(current_year), properties)
    return render_template("fercam.html", fatture = fatture[:100])