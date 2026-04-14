import os
from flask import Blueprint, render_template, request, redirect, flash, url_for
from utils.label_factory import generate_sugar_label
from config.secrets_manager import secrets_manager
import socket

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
            ["codice", "ragione_sociale", "indirizzo", "cap", "localita", "provincia", "cod_paese", "telefono"]
        )

        if customer:
            flash(f"Cliente trovato: {customer.get('ragione_sociale', 'N/D')}", "success")
        else:
            flash("Nessun cliente trovato con il codice Mexal fornito.", "warning")

    return render_template("etichette_spedizioni.html", customer=customer)

def send_to_zebra(printer_ip, zpl_string, port=9100):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(3.0)
            s.connect((printer_ip, port))
            s.sendall(zpl_string.encode('utf-8'))
    except socket.error as e:
        print(f"Errore connessione: {e}")

@etichette_spedizioni_bp.route("/stampa", methods=["POST"])
def stampa_etichetta():
    numero_etichette = int(request.form.get("numero_etichette", 1))
    dati_etichetta = {
        "ragione_sociale": request.form.get("ragione_sociale"),
        "c_a": request.form.get("c_a") or "",
        "indirizzo": request.form.get("indirizzo"),
        "cap": request.form.get("cap"),
        "localita": request.form.get("localita"),
        "provincia": request.form.get("provincia"),
        "cod_paese": request.form.get("cod_paese"),
        "telefono": request.form.get("telefono") or "",
        "note": request.form.get("note") or ""
    }
    
    for _ in range(numero_etichette):
        send_to_zebra("192.168.1.172", generate_sugar_label(
            ragione_sociale=dati_etichetta["ragione_sociale"],
            via=dati_etichetta["indirizzo"],
            cap_citta_provincia=f"{dati_etichetta['cap']} {dati_etichetta['localita']} {dati_etichetta['provincia']}",
            stato=dati_etichetta["cod_paese"],
            telefono=dati_etichetta["telefono"],
            ca=dati_etichetta["c_a"],
            notes=dati_etichetta["note"]
        ))
    
    flash("Richiesta di stampa inoltrata con successo.", "success")
    return redirect(url_for('etichette_spedizioni.etichette_spedizioni'))