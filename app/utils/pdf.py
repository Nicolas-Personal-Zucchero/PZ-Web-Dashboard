from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
import qrcode
from reportlab.lib.utils import ImageReader

def generate_pdf(filename, lotto_personal_zucchero, fornitore, ddt, tipologia_zucchero, data, note, lotti_fornitore):
    """
    Genera un PDF di dimensioni 100x150 mm (verticale) con il contenuto ruotato di 90°:
    - tutti i lotti elencati
    - il lotto_personal_zucchero in evidenza
    - un QR code grande
    Restituisce un oggetto BytesIO contenente il PDF.
    """
    # --- COSTANTI MODIFICABILI ---
    LABEL_WIDTH = 100 * mm
    LABEL_HEIGHT = 150 * mm

    MARGIN_X = 5 * mm
    MARGIN_Y = 5 * mm

    TEXT_OFFSET_X = 5 * mm
    TEXT_OFFSET_Y = 15 * mm

    FONT_LOTTO_PERSONAL_TITOLO = ("Helvetica", 10)
    FONT_LOTTO_PERSONAL = ("Helvetica-Bold", 60)
    FONT_FORNITORE_DDT = ("Helvetica-Bold", 25)
    FONT_ZUCCHERO = ("Helvetica-Bold", 20)
    FONT_DATA = ("Helvetica-Bold", 30)
    FONT_LOTTI_TITLE = ("Helvetica", 17)
    FONT_NOTE = ("Helvetica-Bold", 40)
    FONT_LOTTI_LIST = ("Helvetica-Bold", 13)

    SPACING_FORNITORE_DDT = 25
    SPACING_TIPOLOGIA_ZUCCHERO = 185
    SPACING_DATA = 60
    SPACING_LOTTI_TITLE = 80
    SPACING_LOTTI_LIST = 12
    SPACING_NOTE = 220

    QR_SIZE = 45 * mm
    QR_MARGIN = 5 * mm
    # ------------------------------

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
    text_y = y + usable_height - TEXT_OFFSET_Y + 13 * mm

    c.setFont(*FONT_LOTTO_PERSONAL_TITOLO)
    for char in "LOTTO":
        c.drawString(text_x - 5 * mm, text_y, char)
        text_y -= FONT_LOTTO_PERSONAL_TITOLO[1]

    # Lotto personal zucchero (grande)
    c.setFont(*FONT_LOTTO_PERSONAL)
    lotto_y = y + usable_height - TEXT_OFFSET_Y

    # Calcola la larghezza del testo per il rettangolo
    text_width = c.stringWidth(f"{lotto_personal_zucchero}", *FONT_LOTTO_PERSONAL)
    text_height = FONT_LOTTO_PERSONAL[1]  # altezza font approssimativa

    # Rettangolo nero dietro il testo
    c.setFillColorRGB(0, 0, 0)  # nero
    c.rect(text_x - 0 * mm - 2, lotto_y - 4, text_width + 4, text_height - 10, fill=True, stroke=False)

    # Testo bianco sopra il rettangolo
    c.setFillColorRGB(1, 1, 1)  # bianco
    c.drawString(text_x - 0 * mm, lotto_y, f"{lotto_personal_zucchero}")

    # Ripristina colore nero per gli altri testi
    c.setFillColorRGB(0, 0, 0)

    # Dati fornitore, zucchero, data
    c.setFont(*FONT_FORNITORE_DDT)
    c.drawString(text_x, lotto_y - SPACING_FORNITORE_DDT, f"{fornitore} - DDT {ddt}")

    c.setFont(*FONT_DATA)
    c.drawString(text_x, lotto_y - SPACING_DATA, f"{data}")

    c.setFont(*FONT_ZUCCHERO)
    c.drawString(text_x, lotto_y - SPACING_TIPOLOGIA_ZUCCHERO, f"{tipologia_zucchero.upper()}")

    # Lotti fornitore
    c.setFont(*FONT_LOTTI_TITLE)
    c.drawString(text_x, lotto_y - SPACING_LOTTI_TITLE, "Lotti fornitori:")
    lotto_list_y = lotto_y - SPACING_LOTTI_TITLE - 15
    c.setFont(*FONT_LOTTI_LIST)
    for lotto in lotti_fornitore:
        c.drawString(text_x, lotto_list_y, f"{lotto}")
        lotto_list_y -= SPACING_LOTTI_LIST

    c.setFont(*FONT_NOTE)
    c.drawString(text_x + 20, lotto_y - SPACING_NOTE, f"{note.upper()}")

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
    qr_y = y + QR_MARGIN + 35
    c.drawImage(qr_image, qr_x, qr_y, QR_SIZE, QR_SIZE)

    # Chiudi
    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer