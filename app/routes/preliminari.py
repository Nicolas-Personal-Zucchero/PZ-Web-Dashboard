import json
from decimal import Decimal
from flask import Blueprint, redirect, render_template, flash, request, url_for, current_app, jsonify
from config.constants import ZEBRA_IP
from utils.utils import send_to_zebra
from config.secrets_manager import secrets_manager
from datetime import datetime, timedelta
from utils.label_factory import generate_dachser_label
from dachser_edi import CountryCode, Product, MeasurementName, UnitCode, MeasurementType
from utils.xml_builder import create_xml, generate_doc_id
from utils.RedisMexalCache import RedisMexalCache
from config.constants import PACKING_TYPE_MAP, PACKING_TYPE_ICONS, LABEL_TYPE_MAP, ID_PAGAMENTI_ALLA_CONSEGNA

from utils.database import db, SpedizionePreliminare

preliminari_bp = Blueprint("preliminari", __name__, url_prefix="/preliminari")

@preliminari_bp.route("/", methods=["GET"])
def preliminari():
    #add a randoma spedizione
    db.session.add(SpedizionePreliminare(
        id=generate_doc_id(1234, "FT", 2027),
        ragione_sociale_cliente="Cliente di Test",
        cash_on_delivery=Decimal("123.45"),
        data_ritiro=datetime.now().date(),
        xml="<xml>Test</xml>"
    ))
    db.session.commit()

    spedizioni = SpedizionePreliminare.query.all()
    current_app.logger.info(f"Recuperate {len(spedizioni)} spedizioni preliminari dal database.")
    return render_template("preliminari.html", fatture=spedizioni)

@preliminari_bp.route("/invia", methods=["POST"])
def invia():
    # singolo_id = request.form.get("fattura_id_singola")
    # fatture_ids = [singolo_id] if singolo_id else request.form.getlist("fatture_selezionate")
    # cod_amount_overrides_raw = request.form.get("cod_amount_overrides", "{}")

    # try:
    #     cod_amount_overrides = json.loads(cod_amount_overrides_raw) if cod_amount_overrides_raw else {}
    # except Exception:
    #     cod_amount_overrides = {}

    # if not fatture_ids:
    #     flash("Nessun documento selezionato per l'invio.", "danger")
    #     return redirect(url_for("preliminari.preliminari"))

    # try:
    #     mexal = secrets_manager.get_mexal()
    #     if not mexal:
    #         raise ValueError("Errore nelle credenziali Mexal.")

    #     sscc_generator = secrets_manager.get_sscc_generator()
    #     if not sscc_generator:
    #         raise ValueError("Errore nelle credenziali per la generazione degli SSCC.")

    #     ssccs = sscc_generator.get_ssccs(len(fatture_ids))
    #     if not ssccs:
    #         raise RuntimeError("Errore nella generazione degli SSCC.")

    #     errori = []
    #     xmls = []
    #     for i, fattura_id in enumerate(fatture_ids):
    #         sigla, serie, numero, cod_conto = fattura_id.split("+")
    #         try:
    #             override_raw = cod_amount_overrides.get(fattura_id)
    #             override = parse_cod_amount(override_raw)
    #             id, xml = process_and_send(mexal, ssccs[i], sigla, serie, numero, cod_conto, cod_amount_override=override)
    #             if xml:
    #                 xmls.append((id,xml))
    #         except Exception as e:
    #             current_app.logger.error(f"Errore fattura {fattura_id}: {e}")
    #             errori.append((f"{sigla} {serie}/{numero}", str(e)))

    #     # if xmls:
    #     #     with secrets_manager.get_fercam_sftp(test_server=True) as sftp:
    #     #         for id, xml in xmls:
    #     #             filename = f"{id}.xml"
    #     #             try:
    #     # #                 current_app.logger.info(f"Invio {filename} a Fercam...")
    #     #                 sftp.send_content(xml, filename)
    #     #             except Exception as e:
    #     #                 current_app.logger.error(f"Errore nell'invio del file {filename} a Fercam: {e}")
    #     #                 errori.append((filename, f"Errore nell'invio a Fercam: {str(e)}"))

    #     for fattura_id, error_msg in errori:
    #         flash(f"Errore fattura {fattura_id}: {error_msg}", "danger")
        
    #     if not errori and xmls:
    #         flash(f"Documenti elaborati e inviati con successo. Etichette stampate", "success")

    # except Exception as e:
    #     flash(f"Errore critico durante l'integrazione con Fercam: {e}", "danger")

    return redirect(url_for("preliminari.preliminari"))