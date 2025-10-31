from flask import Blueprint, render_template, request, redirect, flash, send_file
from utils.firebase_client import db
from firebase_admin import firestore
from datetime import datetime
from config.config import ITALY_TZ
import pytz

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

def genera_pdf(lotto_personal_zucchero, fornitore, ddt, tipologia_zucchero, origine, data, lotti_fornitore):
    """
    Genera un PDF di dimensioni 100x150 mm (verticale) con il contenuto ruotato di 90°:
    - tutti i lotti elencati
    - il lotto_personal_zucchero in evidenza
    - un QR code grande
    Restituisce un oggetto BytesIO contenente il PDF.
    """
    from io import BytesIO
    from reportlab.pdfgen import canvas
    from reportlab.lib.units import mm
    import qrcode
    from reportlab.lib.utils import ImageReader

    # --- COSTANTI MODIFICABILI ---
    LABEL_WIDTH = 100 * mm
    LABEL_HEIGHT = 150 * mm

    MARGIN_X = 5 * mm
    MARGIN_Y = 5 * mm

    TEXT_OFFSET_X = 5 * mm
    TEXT_OFFSET_Y = 15 * mm

    FONT_LOTTO_PERSONAL = ("Helvetica-Bold", 60)
    FONT_FORNITORE_DDT = ("Helvetica-Bold", 25)
    FONT_ZUCCHERO = ("Helvetica-Bold", 20)
    FONT_DATA = ("Helvetica-Bold", 30)
    FONT_ORIGINE = ("Helvetica-Bold", 20)
    FONT_LOTTI_TITLE = ("Helvetica-Bold", 17)
    FONT_LOTTI_LIST = ("Helvetica-Bold", 13)

    SPACING_FORNITORE_DDT = 25
    SPACING_TIPOLOGIA_ZUCCHERO = 220
    SPACING_DATA = 60
    SPACING_ORIGINE = 80
    SPACING_LOTTI_TITLE = 100
    SPACING_LOTTI_LIST = 12

    QR_SIZE = 55 * mm
    QR_MARGIN = 5 * mm
    # ------------------------------

    filename = f"etichetta_{lotto_personal_zucchero}.pdf"
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=(LABEL_WIDTH, LABEL_HEIGHT))
    c.setTitle(filename)

    # Ruota tutto di 90° in senso orario, traslando il punto d'origine
    c.translate(LABEL_WIDTH, 0)
    c.rotate(90)

    x = MARGIN_X
    y = MARGIN_Y

    usable_width = LABEL_HEIGHT - 2 * MARGIN_X
    usable_height = LABEL_WIDTH - 2 * MARGIN_Y

    text_x = x + TEXT_OFFSET_X
    text_y = y + usable_height - TEXT_OFFSET_Y

    # Lotto personal zucchero (grande)
    c.setFont(*FONT_LOTTO_PERSONAL)
    lotto_y = text_y
    c.drawString(text_x + 35 * mm, lotto_y, f"{lotto_personal_zucchero}")

    # Dati fornitore, zucchero, data
    c.setFont(*FONT_FORNITORE_DDT)
    c.drawString(text_x, lotto_y - SPACING_FORNITORE_DDT, f"{fornitore} - DDT {ddt}")

    c.setFont(*FONT_DATA)
    c.drawString(text_x, lotto_y - SPACING_DATA, f"{data}")

    c.setFont(*FONT_ORIGINE)
    c.drawString(text_x, lotto_y - SPACING_ORIGINE, f"Origine: {origine}")

    c.setFont(*FONT_ZUCCHERO)
    c.drawString(text_x, lotto_y - SPACING_TIPOLOGIA_ZUCCHERO, f"{tipologia_zucchero.upper()}")

    # Lotti fornitore
    c.setFont(*FONT_LOTTI_TITLE)
    c.drawString(text_x, lotto_y - SPACING_LOTTI_TITLE, "Lotti fornitori:")
    lotto_list_y = lotto_y - SPACING_LOTTI_TITLE - 20
    c.setFont(*FONT_LOTTI_LIST)
    for lotto in lotti_fornitore:
        c.drawString(text_x, lotto_list_y, f"{lotto}")
        lotto_list_y -= SPACING_LOTTI_LIST

    # QR Code
    qr_data = f"https://nicolas-personal-zucchero.github.io/scan?lottoId={lotto_personal_zucchero}"
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=0
    )
    qr.add_data(qr_data)
    qr.make(fit=True)

    qr_img = qr.make_image(fill_color="black", back_color="white")
    qr_buffer = BytesIO()
    qr_img.save(qr_buffer, format="PNG")
    qr_buffer.seek(0)
    qr_image = ImageReader(qr_buffer)

    qr_x = x + usable_width - QR_SIZE - QR_MARGIN
    qr_y = y + QR_MARGIN + 10
    c.drawImage(qr_image, qr_x, qr_y, QR_SIZE, QR_SIZE)

    # Chiudi
    c.showPage()
    c.save()
    buffer.seek(0)
    
    return send_file(buffer, as_attachment=False, download_name=filename, mimetype="application/pdf")

@registrazione_lotti_bp.route("/etichetta", methods=["POST"])
def etichetta():
    id_lotto = request.form.get("id_lotto")
    if not id_lotto:
        return redirect("/registrazione_lotti")

    doc = lotti_zucchero_collection.document(id_lotto).get()
    if not doc.exists:
        flash("Lotto non trovato.", "error")
        return redirect("/registrazione_lotti")
    
    data = doc.to_dict()

    uploaded_at = data.get("uploaded_at")
    if uploaded_at:
        # Convertiamo il timestamp Firestore in ora italiana
        uploaded_at_local = uploaded_at.replace(tzinfo=pytz.UTC).astimezone(ITALY_TZ)
        uploaded_at_str = uploaded_at_local.strftime("%Y-%m-%d")
    else:
        uploaded_at_str = ""
    return genera_pdf(data.get("lotto", ""), data.get("fornitore", ""), data.get("ddt", ""), data.get("tipologia_zucchero", ""), data.get("origine", ""), uploaded_at_str, data.get("lotti_fornitore", ""))
        

@registrazione_lotti_bp.route("/", methods=["GET", "POST"])
def registrazione_lotti():
    if request.method == "GET":
        docs = lotti_zucchero_collection.order_by(
            "uploaded_at", direction=firestore.Query.DESCENDING
        ).stream()

        lotti = []
        for doc in docs:
            data = doc.to_dict()
            if not data.get("loaded_at"):
                data["id"] = doc.id
                # Formatta la data in ora locale italiana
                uploaded_at = data.get("uploaded_at")
                if uploaded_at:
                    data["formatted_time"] = uploaded_at.astimezone(ITALY_TZ).strftime("%Y-%m-%d")
                else:
                    data["formatted_time"] = "N/A"
                etichette_scansionate = len(data.get("scansioni_etichette", []))
                totale_etichette = data.get("numero_etichette", 0)
                data["etichette"] = '{}/{}'.format(etichette_scansionate, totale_etichette)
                if etichette_scansionate < totale_etichette:
                    lotti.append(data)
        return render_template("registrazione-lotti.html", lotti=lotti)

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
        "uploaded_at": uploaded_at
    })

    flash("Lotto caricato con successo!", "success")

    return redirect("/registrazione_lotti")

    