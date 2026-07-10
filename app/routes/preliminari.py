import json
from io import BytesIO
from flask import Blueprint, redirect, render_template, flash, request, url_for, current_app, send_file

from datetime import datetime
from config.secrets_manager import secrets_manager
from utils.database import db, SpedizionePreliminare, SpedizioneIdentificativo
from config.constants import ITALY_TZ
from utils.utils import convert_datetime_to_italy_tz
from sqlalchemy import or_
from sqlalchemy.orm import joinedload

preliminari_bp = Blueprint("preliminari", __name__, url_prefix="/preliminari")

@preliminari_bp.route("/", methods=["GET"])
def preliminari():
    search_identificativo = request.args.get("sent_search_identificativo", "").strip()
    search_ragione_sociale = request.args.get("sent_search_ragione_sociale", "").strip()

    preliminari_stmt = db.select(SpedizionePreliminare)\
        .where(SpedizionePreliminare.sent.is_(False))\
        .options(joinedload(SpedizionePreliminare.identificativi_rel))

    preliminari = db.session.execute(preliminari_stmt).scalars().unique().all()
    inviate = []

    if search_identificativo or search_ragione_sociale:
        identificativo_expr = (
            SpedizioneIdentificativo.sigla + " " +
            SpedizioneIdentificativo.serie + "/" +
            SpedizioneIdentificativo.numero
        )

        inviate_stmt = db.select(SpedizionePreliminare)\
            .where(SpedizionePreliminare.sent.is_(True))\
            .options(joinedload(SpedizionePreliminare.identificativi_rel))

        if search_ragione_sociale:
            ragione_sociale_pattern = f"%{search_ragione_sociale}%"
            inviate_stmt = inviate_stmt.where(
                SpedizionePreliminare.ragione_sociale_cliente.ilike(ragione_sociale_pattern)
            )

        if search_identificativo:
            identificativo_pattern = f"%{search_identificativo}%"
            inviate_stmt = inviate_stmt.where(
                SpedizionePreliminare.identificativi_rel.any(
                    or_(
                        SpedizioneIdentificativo.sigla.ilike(identificativo_pattern),
                        SpedizioneIdentificativo.serie.ilike(identificativo_pattern),
                        SpedizioneIdentificativo.numero.ilike(identificativo_pattern),
                        identificativo_expr.ilike(identificativo_pattern),
                    )
                )
            )

        inviate = db.session.execute(inviate_stmt).scalars().unique().all()
        for spedizione in inviate:
            spedizione.sent_at = convert_datetime_to_italy_tz(spedizione.sent_at)

    return render_template(
        "preliminari.html", 
        spedizioni_preliminari=preliminari, 
        spedizioni_inviate=inviate,
        sent_search_identificativo=search_identificativo,
        sent_search_ragione_sociale=search_ragione_sociale,
        has_sent_search=bool(search_identificativo or search_ragione_sociale)
    )

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

@preliminari_bp.route("/download-xml/<string:id>", methods=["GET"])
def download_xml(id):
    spedizione = db.session.get(SpedizionePreliminare, id)

    if not spedizione:
        flash("Spedizione preliminare non trovata.", "warning")
        return redirect(url_for("preliminari.preliminari"))

    if not spedizione.xml:
        flash("XML non disponibile per questa spedizione.", "warning")
        return redirect(url_for("preliminari.preliminari"))

    xml_bytes = BytesIO(spedizione.xml.encode("utf-8"))
    filename = f"{spedizione.id}.xml"
    return send_file(
        xml_bytes,
        as_attachment=True,
        download_name=filename,
        mimetype="application/xml"
    )


@preliminari_bp.route("/invio-numero-bancali", methods=["POST"])
def invio_numero_bancali():
    numero_bancali_raw = (request.form.get("numero_bancali") or "").strip()

    if not numero_bancali_raw:
        flash("Inserisci il numero di bancali da inviare.", "warning")
        return redirect(url_for("preliminari.preliminari"))

    try:
        numero_bancali = int(numero_bancali_raw)
        if numero_bancali <= 0:
            raise ValueError
    except ValueError:
        flash("Il numero di bancali deve essere un intero maggiore di zero.", "warning")
        return redirect(url_for("preliminari.preliminari"))

    mailer = secrets_manager.get_mailer()
    if not mailer:
        flash("Errore nella configurazione del mailer.", "danger")
        return redirect(url_for("preliminari.preliminari"))

    data_odierna = datetime.now(ITALY_TZ).strftime("%d/%m/%Y")

    try:
        mailer.invia_email_singola(
            destinatari="cesena.ritiri-nv@dachser.fercam.it;erika@personalzucchero.com;marilena@personalzucchero.com",
            oggetto=f"PERSONAL ZUCCHERO: RITIRO PER DATA {data_odierna}",
            corpo=f"Salve,<br>Per il ritiro di oggi {data_odierna} sono previsti <b>{numero_bancali}</b> bancali."
        )
        flash("Email inviata correttamente a Cesena.", "success")
    except Exception as e:
        current_app.logger.error(f"Errore invio numero bancali a Cesena: {e}")
        flash("Errore durante l'invio dell'email a Cesena.", "danger")

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
        with secrets_manager.get_fercam_sftp() as sftp:
            for spedizione in spedizioni:
                if not spedizione.xml:
                    error_msg = f"Campo XML mancante."
                    current_app.logger.warning(f"Spedizione {spedizione.id}: {error_msg}")
                    errori.append((spedizione.id, error_msg))
                    continue

                filename = f"{spedizione.id}.xml"
                
                try:
                    sftp.send_content(spedizione.xml, filename)
                    inviati += 1
                    current_app.logger.info(f"Inviato {filename} a Fercam.")
                    spedizione.sent = True
                    spedizione.sent_at = datetime.now(ITALY_TZ)
                    db.session.commit()
                    current_app.logger.info(f"Spedizione {spedizione.id} marcata come inviata sul database.")
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