import json
from flask import Blueprint, redirect, render_template, flash, request, url_for, current_app

from utils.database import db, SpedizionePreliminare

preliminari_bp = Blueprint("preliminari", __name__, url_prefix="/preliminari")

@preliminari_bp.route("/", methods=["GET"])
def preliminari():
    spedizioni = SpedizionePreliminare.query.all()
    all_identificativi = set()
    for s in spedizioni:
        s.duplicato = False
        splitted = s.identificativo.split(",") if s.identificativo else []
        for identificativo in splitted:
            identificativo = identificativo.strip()
            if identificativo in all_identificativi:
                current_app.logger.error(f"Identificativo duplicato trovato: {identificativo}")
                flash(f"Fattura duplicata trovata: {identificativo}", "danger")
                s.duplicato = True
        all_identificativi.update(s.strip() for s in splitted)
    return render_template("preliminari.html", spedizioni=spedizioni)

@preliminari_bp.route("/elimina/<string:id>", methods=["POST"])
def elimina(id):
    try:
        spedizione = db.session.get(SpedizionePreliminare, id)
        
        if not spedizione:
            flash("Spedizione preliminare non trovata.", "warning")
            return redirect(url_for("preliminari.preliminari"))

        db.session.delete(spedizione)
        db.session.commit()
        
        current_app.logger.info(f"Spedizione preliminare {id} eliminata con successo.")
        flash("Spedizione preliminare eliminata correttamente.", "success")
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Errore durante l'eliminazione della spedizione {id}: {e}")
        flash("Errore a database durante l'eliminazione della spedizione preliminare.", "danger")

    return redirect(url_for("preliminari.preliminari"))

@preliminari_bp.route("/invia", methods=["POST"])
def invia():
    fatture_ids = request.form.getlist("fatture_selezionate")

    if not fatture_ids:
        flash("Nessuna spedizione preliminare selezionata.", "warning")
        return redirect(url_for("preliminari.preliminari"))

    current_app.logger.info(f"Ricevute {len(fatture_ids)} spedizioni preliminari selezionate.")
    flash(f"Selezionate {len(fatture_ids)} spedizioni preliminari.", "success")
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