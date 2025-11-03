from flask import Blueprint, render_template, request, send_file, flash, redirect
from utils.firebase_client import db
from firebase_admin import firestore
from config.config import ITALY_TZ
import pytz
from utils.pdf import generate_pdf
from firebase_admin import firestore
from collections import defaultdict
from datetime import datetime

visualizza_impianti_bp = Blueprint("visualizza_impianti", __name__, url_prefix="/visualizza_impianti")

lotti_zucchero_collection = db.collection("lotti_zucchero")

@visualizza_impianti_bp.route("/", methods=["GET"])
def index():
    if request.method == "GET":
        # Recupera tutti i documenti dalla collezione "documenti"
        docs = lotti_zucchero_collection.stream()

        impianti = defaultdict(list)

        for doc in docs:
            data = doc.to_dict()
            lotto = data.get('lotto')
            scansioni = data.get('scansioni_etichette', [])

            for scan in scansioni:
                impianto = scan['impianto']
                dt = scan['date'].astimezone(ITALY_TZ)
                impianti[impianto].append({
                    'date': dt,
                    'lotto': lotto,
                    'operatore': scan['operatore']
                })

        # Ordinamento semplice
        for impianto, scansioni in impianti.items():
            scansioni.sort(key=lambda x: x['date'], reverse=True)
            for scan in scansioni:
                scan['date'] = scan['date'].strftime("%d/%m/%Y, %H:%M:%S")
        return render_template('visualizza-impianti.html', impianti=impianti)