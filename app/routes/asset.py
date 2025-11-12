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
        modello = request.form.get("modello", "").strip()
        tipologia = request.form.get("tipologia", "").strip()
        posizione = request.form.get("posizione", "").strip()
        intervallo_manutenzione = request.form.get("intervallo_manutenzione", "").strip()
        intervallo_pulizia = request.form.get("intervallo_pulizia", "").strip()

        asset_collection.add({
                    "nome": nome,
                    "modello": modello,
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

def calcola_giorni(interventi, intervallo):
    if not interventi:
        return None, None
    last = interventi[0]["data"]
    oggi = datetime.now(ITALY_TZ)
    giorni = (oggi - last).days
    ritardo = max(0, giorni - intervallo)
    return giorni, ritardo

@asset_bp.route("/<asset_id>")
def asset_detail(asset_id):
    doc = asset_collection.document(asset_id).get()

    if not doc.exists:
        flash("Asset non trovato.", "warning")
        return redirect("/wip/asset")

    asset = doc.to_dict()
    asset["id"] = doc.id

    manutenzioni = sorted(asset.get("manutenzioni", []), key=lambda x: x.get("data", ""), reverse=True)
    pulizie = sorted(asset.get("pulizie", []), key=lambda x: x.get("data", ""), reverse=True)

    giorni_dalla_manutenzione, giorni_ritardo_manutenzione = calcola_giorni(manutenzioni, asset["intervallo_manutenzione"])
    giorni_dalla_pulizia, giorni_ritardo_pulizia = calcola_giorni(pulizie, asset["intervallo_pulizia"])

    for m in manutenzioni:
        m["data"] = m["data"].astimezone(ITALY_TZ).strftime("%d/%m/%Y")

    for p in pulizie:
        p["data"] = p["data"].astimezone(ITALY_TZ).strftime("%d/%m/%Y")

    return render_template(
        "/wip/asset_dettaglio.html",
        asset=asset,
        manutenzioni=manutenzioni,
        pulizie=pulizie,
        giorni_dalla_manutenzione=giorni_dalla_manutenzione,
        giorni_dalla_pulizia=giorni_dalla_pulizia,
        giorni_ritardo_manutenzione=giorni_ritardo_manutenzione,
        giorni_ritardo_pulizia=giorni_ritardo_pulizia,
        datetime=datetime
    )

@asset_bp.route("/<asset_id>/add_intervento", methods=["POST"])
def add_intervento(asset_id):
    tipo = request.form.get("tipo")  # "manutenzione" o "pulizia"
    operatore = request.form.get("operatore", "").strip()
    note = request.form.get("note", "").strip()
    data_str = request.form.get("data")

    if data_str:
        uploaded_at = datetime.strptime(data_str, "%Y-%m-%d")
        uploaded_at = ITALY_TZ.localize(uploaded_at)
    else:
        uploaded_at = datetime.now(ITALY_TZ)

    doc_ref = asset_collection.document(asset_id)

    entry = {
        "data": uploaded_at,
        "operatore": operatore,
        "note": note
    }

    if tipo == "manutenzione":
        doc_ref.update({"manutenzioni": firestore.ArrayUnion([entry])})
        flash("Manutenzione registrata con successo!", "success")
    elif tipo == "pulizia":
        doc_ref.update({"pulizie": firestore.ArrayUnion([entry])})
        flash("Pulizia registrata con successo!", "success")
    else:
        flash("Tipo intervento non valido.", "danger")

    return redirect(f"/wip/asset/{asset_id}")
