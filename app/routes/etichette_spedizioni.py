import os
import io
from flask import Blueprint, render_template, request, redirect, flash, url_for, make_response
from utils.label_factory import generate_sugar_label
from config.secrets_manager import secrets_manager
import socket
from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML
from datetime import datetime
import base64
from flask import current_app

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

def genera_pdf_ritiro(data_destinatario, data_spedizione):
    env = Environment(loader=FileSystemLoader('.'))
    template = env.get_template('bartolini-template.html')
    
    # Rendering dell'HTML con i dati
    html_content = template.render(
        destinatario=data_destinatario,
        spedizione={
            **data_spedizione,
            "data": datetime.now().strftime("%d/%m/%Y")
        }
    )

    HTML(string=html_content).write_pdf("ritiro_brt.pdf")
    print("PDF generato con successo.")

@etichette_spedizioni_bp.route("/stampa", methods=["POST"])
def stampa_etichetta():
    numero_etichette = int(request.form.get("numero_etichette", 1))

    spedizione = {
        "data": datetime.now().strftime("%d/%m/%Y"),
        "colli": request.form.get("colli", "N/D"),
        "peso": request.form.get("peso", "N/D"),
        "natura_merce": request.form.get("natura_merce", "N/D")
    }
    dati_etichetta = {
        "ragione_sociale": request.form.get("ragione_sociale"),
        "cortese_attenzione": request.form.get("cortese_attenzione").upper() or "",
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
            ca=dati_etichetta["cortese_attenzione"],
            notes=dati_etichetta["note"]
        ))

    logo_path = os.path.join(current_app.root_path, 'static', 'img', 'brt_logo.png')
    try:
        with open(logo_path, "rb") as f:
            image_data = base64.b64encode(f.read()).decode('utf-8')
            brt_logo_base_64 = f"data:image/png;base64,{image_data}"
    except FileNotFoundError:
        brt_logo_base_64 = ""

    # 3. Generazione PDF in memoria (senza scrivere su disco)
    rendered_html = render_template('bartolini-template.html', 
                                    destinatario=dati_etichetta, 
                                    spedizione=spedizione,
                                    brt_logo=brt_logo_base_64)

    # Creazione del PDF
    pdf_io = io.BytesIO()
    HTML(string=rendered_html).write_pdf(pdf_io)
    pdf_io.seek(0)

    response = make_response(pdf_io.read())
    response.headers['Content-Type'] = 'application/pdf'
    # 'inline' lo apre nel browser, 'attachment' lo scaricherebbe
    response.headers['Content-Disposition'] = 'inline; filename=ritiro_brt.pdf'

    return response
    
    # flash("Richiesta di stampa inoltrata con successo.", "success")
    # return redirect(url_for('etichette_spedizioni.etichette_spedizioni'))