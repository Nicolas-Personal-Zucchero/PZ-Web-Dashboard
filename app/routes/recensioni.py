import os
from flask import Blueprint, render_template, request, redirect, flash
from mailer_pz import MailerPZ
from config.config import ITALY_TZ
from config.mail_config import EMAIL_TEMPLATES

from utils.firebase_client import db
from firebase_admin import firestore

recensioni_collection = db.collection("recensioni")

recensioni_bp = Blueprint("recensioni", __name__, url_prefix="/recensioni")

INFO_EMAIL_NAME = os.getenv("INFO_EMAIL_NAME", "")
INFO_EMAIL_ADDRESS = os.getenv("INFO_EMAIL_ADDRESS", "")
INFO_EMAIL_PASSWORD = os.getenv("INFO_EMAIL_PASSWORD", "")

if not INFO_EMAIL_NAME:
    print("INFO_EMAIL_NAME is not set.")

if not INFO_EMAIL_ADDRESS:
    print("INFO_EMAIL_ADDRESS is not set.")

if not INFO_EMAIL_PASSWORD:
    print("INFO_EMAIL_PASSWORD is not set.")

mailer = MailerPZ(INFO_EMAIL_NAME,INFO_EMAIL_ADDRESS,INFO_EMAIL_PASSWORD)

@recensioni_bp.route("/", methods=["GET", "POST"])
def recensioni():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        customer = request.form.get("nome_cliente", "").strip()
        sender = request.form.get("nome_mittente", "").strip()
        language = request.form.get("lingua_email", "").strip()

        if email and customer and sender and language:
            doc_ref = recensioni_collection.document(email)
            if doc_ref.get().exists:
                flash("Hai già inviato una richiesta di recensione a questa email.", "warning")
            else:
                # Inserimento in Firestore
                doc_ref.set({
                    "email": email,
                    "customer": customer,
                    "sender": sender,
                    "language": language,
                    "created_at": firestore.SERVER_TIMESTAMP
                })

                mailer.invia_email_singola(
                    email,
                    EMAIL_TEMPLATES["review_" + language.lower()]["object"],
                    EMAIL_TEMPLATES["review_" + language.lower()]["body"].format(customer=customer, sender=sender),
                    hubspot_ccn=True
                )

                flash("Richiesta di recensione inviata con successo!", "success")

            mailer = None
            return redirect("/recensioni")

    # Lettura recensioni da Firestore
    docs = recensioni_collection.order_by("created_at", direction=firestore.Query.DESCENDING).stream()
    entries = []
    for doc in docs:
        data = doc.to_dict()
        created_at = data.get("created_at")
        if created_at:
            local_time = created_at.astimezone(ITALY_TZ)
            formatted_time = local_time.strftime("%Y-%m-%d %H:%M:%S")
        else:
            formatted_time = "N/A"
        entries.append((
            data.get("email"),
            data.get("customer"),
            data.get("sender"),
            data.get("language"),
            formatted_time
        ))

    return render_template("recensioni.html", entries=entries)


@recensioni_bp.route("/elimina", methods=["POST"])
def elimina_recensione():
    email = request.form.get("email", "").strip().lower()
    if email:
        doc_ref = recensioni_collection.document(email)
        if doc_ref.get().exists:
            doc_ref.delete()
            flash("Utente eliminato con successo.", "success")
        else:
            flash("Utente non trovato.", "warning")
    return redirect("/recensioni")