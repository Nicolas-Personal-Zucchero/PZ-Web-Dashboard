import os
from flask import Blueprint, render_template, request, redirect, flash
from config.secrets_manager import secrets_manager
from config.config import ITALY_TZ
from config.mail_config import EMAIL_TEMPLATES

from utils.firebase_client import db
from firebase_admin import firestore

recensioni_collection = db.collection("recensioni")

recensioni_bp = Blueprint("recensioni", __name__, url_prefix="/recensioni")

@recensioni_bp.route("/", methods=["GET", "POST"])
def recensioni():
    mailer = secrets_manager.get_mailer()
    if request.method == "POST":        
        email = request.form.get("email", "").strip().lower()
        customer = request.form.get("nome_cliente", "").strip()
        sender = request.form.get("nome_mittente", "").strip()
        language = request.form.get("lingua_email", "").strip()

        if email and customer and sender and language:
            existing = list(recensioni_collection
            .where("email", "==", email)
            .where("hidden", "==", False)
            .limit(1)
            .stream())
            if any(existing):
                flash("Hai già inviato una richiesta di recensione a questa email.", "warning")
            else:
                recensioni_collection.add({
                    "email": email,
                    "customer": customer,
                    "sender": sender,
                    "language": language,
                    "hidden": False,
                    "created_at": firestore.SERVER_TIMESTAMP
                })

                if mailer:
                    mailer.invia_email_singola(
                        email,
                        EMAIL_TEMPLATES["review_" + language.lower()]["object"],
                        EMAIL_TEMPLATES["review_" + language.lower()]["body"].format(customer=customer, sender=sender),
                        hubspot_ccn=True
                    )
                else:
                    flash("Errore: Configurazione mailer mancante.", "danger")

                flash("Richiesta di recensione inviata con successo!", "success")

            return redirect("/recensioni")

    # Lettura recensioni da Firestore
    docs = recensioni_collection \
    .where("hidden", "==", False) \
    .order_by("created_at", direction=firestore.Query.DESCENDING) \
    .stream()
    reviews = []
    for doc in docs:
        data = doc.to_dict()
        data["id"] = doc.id
        created_at = data.get("created_at")
        if created_at:
            local_time = created_at.astimezone(ITALY_TZ)
            data["formatted_time"] = local_time.strftime("%d/%m/%Y, %H:%M:%S")
        else:
            data["formatted_time"] = "N/A"
        reviews.append(data)

    return render_template("recensioni.html", reviews=reviews)


@recensioni_bp.route("/elimina", methods=["POST"])
def elimina_recensione():
    doc_id = request.form.get("id", "").strip()
    if doc_id:
        doc_ref = recensioni_collection.document(doc_id)
        if doc_ref.get().exists:
            doc_ref.update({"hidden": True})
            flash("Recensione eliminata con successo.", "success")
        else:
            flash("Recensione non trovata.", "warning")
    return redirect("/recensioni")