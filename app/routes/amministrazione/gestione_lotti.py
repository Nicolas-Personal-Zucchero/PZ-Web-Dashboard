from flask import Blueprint, render_template, request, send_file, flash, redirect, url_for
from utils.firebase_client import db
from firebase_admin import firestore
from config.config import ITALY_TZ
import pytz
from utils.pdf import generate_pdf
from datetime import datetime

# --- Parte di Visualizzazione (Da visualizza_lotti.py) ---

# Mappa per la generazione del codice lotto (Da registrazione_lotti.py)
PRODUCT_MAP = {
    "Zucchero Bianco Semolato": "01",
    "Zucchero Bianco Extrafine": "02",
    "Zucchero Canna Grezzo": "06",
    "Zucchero Canna Barbabietola": "07",
    "Zucchero BIO Golden": "08",
    "Zucchero BIO White": "09"
}

gestione_lotti_bp = Blueprint("gestione_lotti", __name__, url_prefix="/gestione_lotti")
lotti_zucchero_collection = db.collection("lotti_zucchero")

def get_lotto(tipologia):
    # Generazione del codice lotto
    prefix = PRODUCT_MAP.get(tipologia) + "-"

    existing = lotti_zucchero_collection \
        .where("lotto", ">=", prefix) \
        .where("lotto", "<", prefix + "\uf8ff") \
        .stream()
    
    count = sum(1 for _ in existing)
    lotto = prefix + f"{count + 1:03d}"
    return lotto  

@gestione_lotti_bp.route("/get_lotto", methods=["GET"])
def get_lotto_route():
    tipologia = request.args.get("tipologia", "").strip()
    if not tipologia:
        return {"error": "Tipologia non fornita"}, 400
    
    if tipologia not in PRODUCT_MAP:
        return {"error": f"Tipologia '{tipologia}' non valida"}, 400

    lotto = get_lotto(tipologia)
    return {"lotto": lotto}, 200  

@gestione_lotti_bp.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        # --- Logica di Registrazione (Da registrazione_lotti.py) ---
        
        lotto = request.form.get("lotto", "").strip()
        if not lotto:
            flash("Lotto non valido.", "danger")
            return redirect("/amministrazione/gestione_lotti")

        # Gestione della Data
        data_str = request.form.get("data", "").strip()
        if data_str:
            uploaded_at = datetime.strptime(data_str, "%Y-%m-%d")
            uploaded_at = ITALY_TZ.localize(uploaded_at)
        else:
            uploaded_at = datetime.now(ITALY_TZ)
        
        tipologia = request.form.get("tipologia", "").strip()
        fornitore = request.form.get("fornitore", "").strip()
        ddt = request.form.get("ddt", "").strip()
        origine = request.form.get("origine", "").strip()
        
        try:
            n_etichette = int(request.form.get("n_etichette", "").strip())
        except ValueError:
            flash("Numero etichette non valido.", "danger")
            return redirect("/amministrazione/gestione_lotti")

        lotti = request.form.getlist("lotti[]")
        note = request.form.get("note", "").strip()

        # Salvataggio su Firestore
        doc_ref = lotti_zucchero_collection.document(lotto)
        if doc_ref.get().exists:
            flash(f"Lotto {lotto} già esistente.", "danger")
            return redirect("/amministrazione/gestione_lotti")
        
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
        # Reindirizza con il parametro 'stampare' per aprire il PDF
        return redirect(f"/amministrazione/gestione_lotti?stampare={lotto}")

    # --- Logica di Visualizzazione (Da visualizza_lotti.py) ---
    # GET
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

        for scansione in data.get("scansioni_etichette", []):
            date = scansione.get("date")
            if date:
                scansione["date"] = date.astimezone(ITALY_TZ).strftime("%d/%m/%Y, %H:%M:%S")
            else:
                scansione["date"] = "N/A"

        lotti.append(data)
    
    # Restituisce il nuovo template unificato
    return render_template("/amministrazione/gestione-lotti.html", lotti=lotti)

@gestione_lotti_bp.route("/etichetta", methods=["GET", "POST"])
def etichetta():
    # Funzione per la generazione PDF (rimane invariata, usare il nuovo blueprint)
    if request.method == "POST":
        id_lotto = request.form.get("id_lotto")
    else:  # GET
        id_lotto = request.args.get("id_lotto")

    if not id_lotto:
        flash("ID lotto non fornito.", "danger")
        return redirect(url_for(".index"))

    doc = lotti_zucchero_collection.document(id_lotto).get()
    if not doc.exists:
        flash("Lotto non trovato.", "danger")
        return redirect(url_for(".index"))
    
    data = doc.to_dict()

    uploaded_at = data.get("uploaded_at")
    if uploaded_at:
        uploaded_at_local = uploaded_at.replace(tzinfo=pytz.UTC).astimezone(ITALY_TZ)
        uploaded_at_str = uploaded_at_local.strftime("%Y-%m-%d")
    else:
        uploaded_at_str = ""
    filename = f"etichetta_{data.get('lotto', '')}.pdf"
    pdf = generate_pdf(filename, data.get("lotto", ""), data.get("fornitore", ""), data.get("ddt", ""), data.get("tipologia_zucchero", ""), uploaded_at_str, data.get("note", ""), data.get("lotti_fornitore", ""))
    return send_file(pdf, as_attachment=False, download_name=filename, mimetype="application/pdf")

@gestione_lotti_bp.route("/aggiungi_scansione", methods=["POST"])
def aggiungi_scansione():
    try:
        data = request.get_json()
        lotto_id = data.get("lotto_id")
        impianto = data.get("impianto")
        operatore = data.get("operatore")

        if not lotto_id or not impianto or not operatore:
            return {"success": False, "error": "Dati mancanti"}, 400

        # Verifica dell'esistenza del documento
        doc_ref = lotti_zucchero_collection.document(lotto_id)
        if not doc_ref.get().exists:
            return {"success": False, "error": f"Lotto con ID {lotto_id} non trovato"}, 404
        
        now = datetime.now(ITALY_TZ)
        nuova_scansione = {
            "impianto": impianto,
            "operatore": operatore,
            "date": now
        }

        doc_ref.update({
            "scansioni_etichette": firestore.ArrayUnion([nuova_scansione])
        })

        return {"success": True, "message": "Scansione aggiunta"}, 200

    except Exception as e:
        return {"success": False, "error": str(e)}, 500