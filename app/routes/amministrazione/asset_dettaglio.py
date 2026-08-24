import os
from pathlib import Path
from flask import Blueprint, render_template, request, redirect, flash, send_from_directory, abort, make_response
from datetime import datetime
from config.constants import ITALY_TZ
import ulid
import io
from weasyprint import HTML
from services.asset import AssetService

asset_dettaglio_bp = Blueprint("asset_dettaglio", __name__, url_prefix="/asset")

ATTACHMENTS_DIR = os.environ.get("ASSET_ATTACHMENTS_DIR", "/attachments/asset_interventi")

def get_attachments_dir():
    os.makedirs(ATTACHMENTS_DIR, exist_ok=True)
    return ATTACHMENTS_DIR

def calcola_giorni(interventi, intervallo):
    """Calcola i giorni trascorsi e l'eventuale ritardo in base all'intervallo previsto."""
    if not interventi:
        return None, None
    last = interventi[0]["data"]
    oggi = datetime.now(ITALY_TZ)
    giorni = (oggi - last).days
    ritardo = max(0, giorni - intervallo)
    return giorni, ritardo

@asset_dettaglio_bp.route("/<asset_id>")
def asset_detail(asset_id):
    asset = AssetService.get(asset_id)

    if not asset:
        flash("Asset non trovato.", "warning")
        return redirect("/amministrazione/asset")

    interventi = AssetService.get_interventi(asset_id)

    manutenzioni = [i for i in interventi if i.get("tipo") == "manutenzione"]
    pulizie = [i for i in interventi if i.get("tipo") == "pulizia"]

    giorni_dalla_manutenzione, giorni_ritardo_manutenzione = calcola_giorni(manutenzioni, asset["intervallo_manutenzione"])
    giorni_dalla_pulizia, giorni_ritardo_pulizia = calcola_giorni(pulizie, asset["intervallo_pulizia"])

    for i in interventi:
        i["data"] = i["data"].astimezone(ITALY_TZ).strftime("%d/%m/%Y")

    return render_template(
        "/amministrazione/asset_dettaglio.html",
        asset=asset,
        interventi=interventi,
        giorni_dalla_manutenzione=giorni_dalla_manutenzione,
        giorni_dalla_pulizia=giorni_dalla_pulizia,
        giorni_ritardo_manutenzione=giorni_ritardo_manutenzione,
        giorni_ritardo_pulizia=giorni_ritardo_pulizia,
        datetime=datetime
    )

@asset_dettaglio_bp.route("/<asset_id>/add_intervento", methods=["POST"])
def add_intervento(asset_id):
    tipo = request.form.get("tipo")
    operatore = request.form.get("operatore", "").strip()
    note = request.form.get("note", "").strip()
    data_str = request.form.get("data")
    allegato = request.files.get("allegato")

    if data_str:
        uploaded_at = datetime.strptime(data_str, "%Y-%m-%d")
        uploaded_at = ITALY_TZ.localize(uploaded_at)
    else:
        uploaded_at = datetime.now(ITALY_TZ)

    entry = {
        "tipo": tipo,
        "data": uploaded_at,
        "operatore": operatore,
        "note": note
    }

    if allegato and allegato.filename:
        original_filename = os.path.basename(allegato.filename).strip()
        extension = Path(original_filename).suffix.lower()
        storage_name = f"{str(ulid.new()).lower()}{extension}"
        storage_path = os.path.join(get_attachments_dir(), storage_name)

        allegato.save(storage_path)

        entry["allegato_original_filename"] = original_filename
        entry["allegato_path"] = storage_name

    result = AssetService.add_intervento(asset_id, entry)
    if not result:
        flash("Errore durante la registrazione dell'intervento.", "danger")
        return redirect(f"/amministrazione/asset/{asset_id}")
    flash(f"Intervento di tipo {tipo} registrato con successo!", "success")

    return redirect(f"/amministrazione/asset/{asset_id}")

@asset_dettaglio_bp.route("/<asset_id>/intervento/<intervento_id>/allegato")
def download_intervento_allegato(asset_id, intervento_id):
    asset = AssetService.get(asset_id)
    if not asset:
        abort(404)

    intervento = AssetService.get_intervento(asset_id, intervento_id)

    if not intervento:
        abort(404)

    stored_name = intervento.get("allegato_path", "")
    original_name = intervento.get("allegato_original_filename", "")

    if not stored_name:
        abort(404)

    safe_stored_name = os.path.basename(stored_name)
    download_name = original_name or safe_stored_name

    return send_from_directory(
        get_attachments_dir(),
        safe_stored_name,
        as_attachment=True,
        download_name=download_name,
    )

@asset_dettaglio_bp.route("/<asset_id>/pdf")
def genera_pdf_riepilogo(asset_id):
    asset = AssetService.get(asset_id)
    if not asset:
        abort(404, description="Asset non trovato")

    interventi = AssetService.get_interventi(asset_id)

    for i in interventi:
        if hasattr(i["data"], "astimezone"):
            i["data"] = i["data"].astimezone(ITALY_TZ).strftime("%d/%m/%Y")

    data_odierna = datetime.now(ITALY_TZ).strftime("%d/%m/%Y")

    # Render HTML
    rendered_html = render_template(
        "pdf/asset_riepilogo.html",
        asset=asset,
        interventi=interventi,
        data_odierna=data_odierna
    )

    # Generazione PDF in-memory
    pdf_io = io.BytesIO()
    HTML(string=rendered_html).write_pdf(pdf_io)
    pdf_io.seek(0)

    response = make_response(pdf_io.read())
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'inline; filename=riepilogo_asset_{asset_id}.pdf'
    
    return response

@asset_dettaglio_bp.route("/<asset_id>/update", methods=["POST"])
def update_asset(asset_id):
    try:
        payload = {
            "nome": request.form.get("nome", "").strip(),
            "modello": request.form.get("modello", "").strip(),
            "tipologia": request.form.get("tipologia", "").strip(),
            "sede": request.form.get("sede", "").strip(),
            "posizione": request.form.get("posizione", "").strip(),
            "intervallo_manutenzione": int(request.form.get("intervallo_manutenzione", 0)),
            "intervallo_pulizia": int(request.form.get("intervallo_pulizia", 0)),
        }
        result = AssetService.update(asset_id, payload)

        if result:
            flash("Asset aggiornato con successo.", "success")
        else:
            flash("Errore durante l'aggiornamento dell'asset su database.", "danger")
    except ValueError:
        flash("Errore di validazione: intervalli non numerici.", "danger")
        
    return redirect(f"/amministrazione/asset/{asset_id}")

@asset_dettaglio_bp.route("/<asset_id>/intervento/<intervento_id>/update", methods=["POST"])
def update_intervento(asset_id, intervento_id):
    tipo = request.form.get("tipo")
    operatore = request.form.get("operatore", "").strip()
    note = request.form.get("note", "").strip()
    data_str = request.form.get("data")

    update_data = {
        "tipo": tipo,
        "operatore": operatore,
        "note": note
    }

    if data_str:
        try:
            dt = datetime.strptime(data_str, "%Y-%m-%d")
            update_data["data"] = ITALY_TZ.localize(dt)
        except ValueError:
            flash("Formato data non valido.", "danger")
            return redirect(f"/amministrazione/asset/{asset_id}")

    result = AssetService.update_intervento(asset_id, intervento_id, update_data)
    
    if result:
        flash("Intervento aggiornato con successo.", "success")
    else:
        flash("Errore durante l'aggiornamento dell'intervento.", "danger")
        
    return redirect(f"/amministrazione/asset/{asset_id}")

@asset_dettaglio_bp.route("/<asset_id>/intervento/<intervento_id>/delete", methods=["POST"])
def delete_intervento(asset_id, intervento_id):
    result = AssetService.delete_intervento(asset_id, intervento_id)
    if result:
        flash("Intervento eliminato.", "success")
    else:
        flash("Errore durante l'eliminazione dell'intervento.", "danger")
        
    return redirect(f"/amministrazione/asset/{asset_id}")