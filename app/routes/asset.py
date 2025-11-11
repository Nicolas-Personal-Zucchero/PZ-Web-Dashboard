import os
from flask import Blueprint, render_template, request, redirect, flash
from datetime import datetime
import pytz
from config.config import ITALY_TZ
from utils.firebase_client import db
from firebase_admin import firestore

asset_bp = Blueprint("asset", __name__, url_prefix="/asset")

# Collezione Firestore
asset_collection = db.collection("asset")

@asset_bp.route("/", methods=["GET", "POST"])
def asset():
    if request.method == "POST":
        nome = request.form.get("nome", "").strip()
        tipologia = request.form.get("tipologia", "").strip()
        posizione = request.form.get("posizione", "").strip()
        intervallo_manutenzione = request.form.get("intervallo_manutenzione", "").strip()
        intervallo_pulizia = request.form.get("intervallo_pulizia", "").strip()

        asset_collection.add({
                    "nome": nome,
                    "tipologia": tipologia,
                    "posizione": posizione,
                    "intervallo_manutenzione": int(intervallo_manutenzione),
                    "intervallo_pulizia": int(intervallo_pulizia),
                    "manutenzioni": [],
                    "pulizie": [],
                    "created_at": firestore.SERVER_TIMESTAMP
                })
        flash("Asset registrato con successo!", "success")
        return redirect("/wip/asset")

    # Lettura asset da Firestore ordinati per creazione decrescente
    docs = asset_collection.order_by("created_at", direction=firestore.Query.DESCENDING).stream()
    entries = []
    for doc in docs:
        data = doc.to_dict()
        data["id"] = doc.id
        entries.append(data)

    return render_template("/wip/asset.html", entries=entries)


@asset_bp.route("/elimina", methods=["POST"])
def elimina_asset():
    asset_id = request.form.get("asset_id", "").strip()
    if asset_id:
        doc_ref = asset_collection.document(asset_id)
        if doc_ref.get().exists:
            doc_ref.delete()
            flash("Asset eliminato con successo.", "success")
        else:
            flash("Asset non trovato.", "warning")
    return redirect("/wip/asset")
