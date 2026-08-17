import os
from flask import Blueprint, current_app, render_template, request, redirect, flash
from config.secrets_manager import secrets_manager
from config.constants import ITALY_TZ
from config.mail_config import EMAIL_TEMPLATES
from services.recensioni import ReviewService

recensioni_bp = Blueprint("recensioni", __name__, url_prefix="/recensioni")

@recensioni_bp.route("/", methods=["GET", "POST"])
def recensioni():
    mailer = secrets_manager.get_mailer()
    if request.method == "POST":        
        email = request.form.get("email", "").strip().lower()
        customer = request.form.get("nome_cliente", "").strip()
        sender = request.form.get("sender", "").strip()
        language = request.form.get("lingua_email", "").strip()

        if not email or not customer or not sender or not language:
            flash("Tutti i campi sono obbligatori.", "danger")
            return redirect("/recensioni")

        if ReviewService.does_review_exist(email):
            flash("Hai già inviato una richiesta di recensione a questa email.", "warning")
        else:
            ReviewService.create(customer_name=customer, customer_email=email, language=language, sender_id=1)
            if mailer:
                mailer.invia_email_singola(
                    recipients=[email],
                    subject=EMAIL_TEMPLATES["review_" + language.lower()]["object"],
                    body=EMAIL_TEMPLATES["review_" + language.lower()]["body"].format(customer=customer, sender=sender),
                    hubspot_ccn=True
                )
                flash("Richiesta di recensione inviata con successo!", "success")
            else:
                flash("Errore: Configurazione mailer mancante.", "danger")

        return redirect("/recensioni")

    return render_template(
        "recensioni.html",
        employees=ReviewService.get_all_employees(),
        reviews=ReviewService.get_reviews(hidden=False)
    )


@recensioni_bp.route("/elimina", methods=["POST"])
def elimina_recensione():
    doc_id = int(request.form.get("id", "").strip())
    if doc_id:
        success = ReviewService.hide(doc_id)
        if success:
            flash("Recensione eliminata con successo.", "success")
        else:
            flash("Recensione non trovata.", "warning")
        
    return redirect("/recensioni")