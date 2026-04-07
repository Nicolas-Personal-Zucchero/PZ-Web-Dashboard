import os
from flask import Blueprint, render_template, request, redirect, flash
from config.secrets_manager import secrets_manager
from config.config import ITALY_TZ

etichette_spedizioni_bp = Blueprint("etichette_spedizioni", __name__, url_prefix="/etichette_spedizioni")

@etichette_spedizioni_bp.route("/", methods=["GET", "POST"])
def etichette_spedizioni():
    customer = None
    if request.method == "POST":
        mexal_code = request.form.get("mexal_code", "").strip()

        if not mexal_code:
            flash("Codice Mexal mancante.", "warning")
            return render_template("etichette_spedizioni.html", customer=customer)
        
        mexal = secrets_manager.get_mexal()
        if not mexal:
            flash("Errore nelle credenziali Mexal.", "error")
            return render_template("etichette_spedizioni.html", customer=customer)
        
        customer = mexal.get_customer_by_mexal_code(
            mexal_code,
            ["codice", "ragione_sociale", "localita", "provincia", "cod_paese", "telefono"]
        )

        if customer:
            flash(f"Cliente trovato: {customer.get('ragione_sociale', 'N/D')}", "success")
        else:
            flash("Nessun cliente trovato con il codice Mexal fornito.", "warning")

    return render_template("etichette_spedizioni.html", customer=customer)