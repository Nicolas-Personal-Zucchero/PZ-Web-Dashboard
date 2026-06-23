import json
from flask import Blueprint, redirect, render_template, flash, request, url_for, current_app

from datetime import datetime
from config.secrets_manager import secrets_manager
from utils.database import db, SpedizionePreliminare
from sqlalchemy.orm import joinedload

preliminari_bp = Blueprint("preliminari", __name__, url_prefix="/preliminari")

@preliminari_bp.route("/", methods=["GET"])
def preliminari():
    spedizioni = SpedizionePreliminare.query.options(
        joinedload(SpedizionePreliminare.identificativi_rel)
    ).all()
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
    spedizioni_ids = request.form.getlist("spedizioni_selezionate")

    if not spedizioni_ids:
        flash("Nessuna spedizione preliminare selezionata.", "warning")
        return redirect(url_for("preliminari.preliminari"))

    mexal = secrets_manager.get_mexal()
    if not mexal:
        flash("Errore nelle credenziali Mexal.", "danger")
        return render_template("fercam.html", fatture=[])
    
    current_app.logger.info(f"Ricevute {len(spedizioni_ids)} spedizioni preliminari selezionate.")

    spedizioni = SpedizionePreliminare.query.filter(
            SpedizionePreliminare.id.in_(spedizioni_ids)
        ).options(
            joinedload(SpedizionePreliminare.identificativi_rel)
        ).all()

    if not spedizioni:
        flash("Spedizioni selezionate non trovate a database.", "danger")
        return redirect(url_for("preliminari.preliminari"))

    errori = []
    inviati = 0

    try:
        with secrets_manager.get_fercam_sftp(test_server=True) as sftp:
            for spedizione in spedizioni:
                if not spedizione.xml:
                    error_msg = f"Campo XML mancante."
                    current_app.logger.warning(f"Spedizione {spedizione.id}: {error_msg}")
                    errori.append((spedizione.id, error_msg))
                    continue

                filename = f"{spedizione.id}.xml"
                
                try:
                    # sftp.send_content(spedizione.xml, filename)
                    inviati += 1
                    current_app.logger.info(f"Inviato {filename} a Fercam.")
                    for identificativo in spedizione.identificativi_rel:
                        current_app.logger.info(f"Aggiornamento numero di tracking per {identificativo.sigla} {identificativo.serie}/{identificativo.numero} ({identificativo.cod_conto}).")
                        # update_nr_tracking(
                        #     mexal,
                        #     identificativo.sigla,
                        #     identificativo.serie,
                        #     identificativo.numero,
                        #     identificativo.cod_conto
                        # )
                    db.session.delete(spedizione)
                    db.session.commit()
                except Exception as e:
                    error_msg = f"Errore nell'invio a Fercam: {e}"
                    current_app.logger.error(f"Errore spedizione {spedizione.id} [{filename}]: {e}")
                    errori.append((spedizione.id, error_msg))

        if inviati > 0:
            flash(f"{inviati} documenti elaborati e inviati con successo.", "success")
            
        for sp_id, error_msg in errori:
            flash(f"Errore spedizione {sp_id}: {error_msg}", "danger")

    except Exception as e:
        current_app.logger.error(f"Errore critico di connessione SFTP Fercam: {e}")
        flash("Errore critico durante l'integrazione con Fercam. Controllare i log di sistema.", "danger")

    return redirect(url_for("preliminari.preliminari"))

def update_nr_tracking(mexal, sigla, serie, numero, cod_conto):
    payload = {"nr_tracking": [[1, "SPEDITO"]]}
    current_app.logger.warning("MX: Aggiornamento numero di tracking.")
    mexal.update_warehouse_movement(str(datetime.now().year), sigla, serie, numero, cod_conto, payload)