from flask import Blueprint, render_template, request, redirect, flash
from utils.firebase_client import db
from datetime import datetime
from config.config import ITALY_TZ

lotti_zucchero_collection = db.collection("lotti_zucchero")

registrazione_lotti_bp = Blueprint("registrazione_lotti", __name__, url_prefix="/registrazione_lotti")

PRODUCER_MAP = {
    "ITALIAZUCCHERI": "IZ",
    "INAGRA": "IN",
    "FASTZUCCHERI": "FZ",
    "GRANDAZUCCHERI": "GZ",
    "PININPERO": "PP"
}

PRODUCT_MAP = {
    "Zucchero Bianco Semolato": "01",
    "Zucchero Bianco Extrafine": "02",
    "Zucchero Canna Grezzo": "06",
    "Zucchero Canna Barbabietola": "07",
    "Zucchero BIO Golden": "08",
    "Zucchero BIO White": "09"
}  

@registrazione_lotti_bp.route("/", methods=["GET", "POST"])
def registrazione_lotti():
    if request.method == "GET":
        return render_template("registrazione-lotti.html")

    data_str = request.form.get("data", "").strip()
    if data_str:
        uploaded_at = datetime.strptime(data_str, "%Y-%m-%d")
        # opzionale: rendi la data timezone-aware
        uploaded_at = ITALY_TZ.localize(uploaded_at)
    else:
        uploaded_at = datetime.now(ITALY_TZ)
    tipologia = request.form.get("tipologia", "").strip()
    fornitore = request.form.get("fornitore", "").strip()
    ddt = request.form.get("ddt", "").strip()
    origine = request.form.get("origine", "").strip()
    n_etichette = int(request.form.get("n_etichette", "").strip())
    lotti = request.form.getlist("lotti[]")
    note = request.form.get("note", "").strip()
    
    prefix = PRODUCT_MAP.get(tipologia) + "-"

    existing = lotti_zucchero_collection \
        .where("lotto", ">=", prefix) \
        .where("lotto", "<", prefix + "\uf8ff") \
        .stream()
    
    count = sum(1 for _ in existing)
    lotto = prefix + f"{count + 1:03d}"

    doc_ref = lotti_zucchero_collection.document(lotto)
    doc_ref.set({
        "lotto" : lotto,
        "fornitore": fornitore,
        "ddt": ddt,
        "tipologia_zucchero": tipologia,
        "lotti_fornitore": lotti,
        "origine": origine,
        "numero_etichette": n_etichette,
        "scansioni_etichette": [],
        "note": note,
        "uploaded_at": uploaded_at
    })

    flash("Lotto caricato con successo!", "success")

    return redirect("/registrazione_lotti")

    