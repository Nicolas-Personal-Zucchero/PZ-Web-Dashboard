from flask import Blueprint, render_template, request, redirect, flash 
from utils.firebase_client import db
from firebase_admin import firestore
import re

asset_bp = Blueprint("asset", __name__, url_prefix="/asset")

# Collezione Firestore
asset_collection = db.collection("asset")

def natural_key(s):
    """Crea una chiave per l'ordinamento naturale: divide numeri e lettere"""
    return [int(text) if text.isdigit() else text.lower() for text in re.split(r'(\d+)', s)]

@asset_bp.route("/", methods=["GET", "POST"])
def asset():
    if request.method == "POST":
        nome = request.form.get("nome", "").strip()
        modello = request.form.get("modello", "").strip()
        tipologia = request.form.get("tipologia", "").strip()
        sede = request.form.get("sede", "").strip()
        posizione = request.form.get("posizione", "").strip()
        intervallo_manutenzione = request.form.get("intervallo_manutenzione", "").strip()
        intervallo_pulizia = request.form.get("intervallo_pulizia", "").strip()

        asset_collection.add({
                    "nome": nome,
                    "modello": modello,
                    "tipologia": tipologia,
                    "sede": sede,
                    "posizione": posizione,
                    "intervallo_manutenzione": int(intervallo_manutenzione),
                    "intervallo_pulizia": int(intervallo_pulizia),
                    "interventi": [],
                    "created_at": firestore.SERVER_TIMESTAMP
                })
        flash("Asset registrato con successo!", "success")
        return redirect("/amministrazione/asset")

    # Lettura asset da Firestore ordinati per creazione decrescente
    docs = asset_collection.stream()
    entries = []
    for doc in docs:
        data = doc.to_dict()
        data["id"] = doc.id
        entries.append(data)

    entries.sort(key=lambda x: natural_key(x["nome"]))

    return render_template("/amministrazione/asset.html", entries=entries)

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
    return redirect("/amministrazione/asset")