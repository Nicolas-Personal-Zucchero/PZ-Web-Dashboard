from flask import Blueprint, render_template, request, send_file, flash, redirect
from utils.firebase_client import db
from firebase_admin import firestore
from config.config import ITALY_TZ
import pytz
from utils.pdf import generate_pdf
from firebase_admin import firestore

visualizza_lotti_bp = Blueprint("visualizza_lotti", __name__, url_prefix="/visualizza_lotti")

lotti_zucchero_collection = db.collection("lotti_zucchero")

@visualizza_lotti_bp.route("/", methods=["GET"])
def index():
    if request.method == "GET":
        docs = lotti_zucchero_collection.order_by(
            "uploaded_at", direction=firestore.Query.DESCENDING
        ).stream()

        lotti = []
        for doc in docs:
            data = doc.to_dict()

            data["id"] = doc.id

            etichette_scansionate = len(data.get("scansioni_etichette", []))
            totale_etichette = data.get("numero_etichette", 0)
            data["etichette"] = '{}/{}'.format(etichette_scansionate, totale_etichette)
            
            # Formatta la data in ora locale italiana
            uploaded_at = data.get("uploaded_at")
            if uploaded_at:
                data["formatted_time"] = uploaded_at.astimezone(ITALY_TZ).strftime("%d/%m/%Y")
            else:
                data["formatted_time"] = "N/A"

            lotti.append(data)
        return render_template("amministrazione/visualizza-lotti.html", lotti=lotti)
    
@visualizza_lotti_bp.route("/etichetta", methods=["GET", "POST"])
def etichetta():
    if request.method == "POST":
        id_lotto = request.form.get("id_lotto")
    else:  # GET
        id_lotto = request.args.get("id_lotto")

    if not id_lotto:
        flash("ID lotto non fornito.", "error")
        return redirect("/visualizza_lotti")

    doc = lotti_zucchero_collection.document(id_lotto).get()
    if not doc.exists:
        flash("Lotto non trovato.", "error")
        return redirect("/visualizza_lotti")
    
    data = doc.to_dict()

    uploaded_at = data.get("uploaded_at")
    if uploaded_at:
        # Convertiamo il timestamp Firestore in ora italiana
        uploaded_at_local = uploaded_at.replace(tzinfo=pytz.UTC).astimezone(ITALY_TZ)
        uploaded_at_str = uploaded_at_local.strftime("%Y-%m-%d")
    else:
        uploaded_at_str = ""
    filename = f"etichetta_{data.get('lotto', '')}.pdf"
    pdf = generate_pdf(filename, data.get("lotto", ""), data.get("fornitore", ""), data.get("ddt", ""), data.get("tipologia_zucchero", ""), uploaded_at_str, data.get("note", ""), data.get("lotti_fornitore", ""))
    return send_file(pdf, as_attachment=False, download_name=filename, mimetype="application/pdf")
      