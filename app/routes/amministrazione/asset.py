from flask import Blueprint, render_template, request, redirect, flash 
from services.asset import AssetService
from config.constants import SEDI, TIPOLOGIE_ASSET

asset_bp = Blueprint("asset", __name__, url_prefix="/asset")

@asset_bp.route("/", methods=["GET", "POST"])
def asset():
    if request.method == "POST":
        nome = request.form.get("nome", "").strip()
        modello = request.form.get("modello", "").strip()
        tipologia = request.form.get("tipologia", "").strip()
        sede = request.form.get("sede", "").strip()
        posizione = request.form.get("posizione", "").strip()
        intervallo_controllo_periodico = int(request.form.get("intervallo_controllo_periodico", "").strip())
        intervallo_pulizia = request.form.get("intervallo_pulizia").strip()
        if intervallo_pulizia:
            intervallo_pulizia = int(intervallo_pulizia.strip())

        AssetService.create(nome, modello, tipologia, sede, posizione, intervallo_controllo_periodico, intervallo_pulizia)
        flash("Asset registrato con successo!", "success")
        return redirect("/amministrazione/asset")

    return render_template(
        "/amministrazione/asset.html",
        sedi=SEDI,
        tipologie_asset=TIPOLOGIE_ASSET,
        entries=AssetService.get_all()
    )

@asset_bp.route("/elimina", methods=["POST"])
def elimina_asset():
    asset_id = request.form.get("asset_id", "").strip()
    if asset_id:
        AssetService.delete(asset_id)
        flash("Asset eliminato con successo.", "success")
    return redirect("/amministrazione/asset")