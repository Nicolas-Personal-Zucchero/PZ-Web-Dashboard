import os
from flask import Blueprint, flash, redirect, render_template, request

from config.mail_config import EMAIL_TEMPLATES
from mailer_pz import MailerPZ
from services.sigep_tickets import SigepTicketService

sigep_ticket_bp = Blueprint(
    "sigep_ticket", __name__, url_prefix="/sigep-ticket", template_folder=""
)


@sigep_ticket_bp.route("/", methods=["GET"])
def index():
    available_count = SigepTicketService.get_available_count()
    assigned_list = SigepTicketService.get_assigned_summary()

    return render_template(
        "/sigep_ticket.html",
        available_count=available_count,
        assigned_list=assigned_list,
    )


@sigep_ticket_bp.route("/send", methods=["POST"])
def send_tickets():
    email = request.form.get("email", "").strip().lower()
    name = request.form.get("name", "").strip()
    try:
        count = int(request.form.get("count", 0))
    except ValueError:
        count = 0
    language = request.form.get("language", "ita").lower()

    if not email or not name or count <= 0:
        flash("Dati mancanti o non validi", "danger")
        return redirect("/sigep-ticket")

    try:
        assigned_codes = SigepTicketService.assign_tickets(
            count=count,
            email=email,
            assigned_with="personalzucchero.local",
        )

        mailer = MailerPZ(
            os.getenv("INFO_EMAIL_NAME"),
            os.getenv("INFO_EMAIL_ADDRESS"),
            os.getenv("INFO_EMAIL_PASSWORD"),
        )
        if mailer and assigned_codes:
            codes_str = "<br>".join([f"<b>{code}</b>" for code in assigned_codes])
            template_key = f"sigep_{language}"
            if template_key not in EMAIL_TEMPLATES:
                template_key = "sigep_ita"  # Fallback

            mailer.invia_email_singola(
                recipients=[email],
                subject=EMAIL_TEMPLATES[template_key]["object"],
                body=EMAIL_TEMPLATES[template_key]["body"].format(
                    nome_cliente=name, codici_biglietti=codes_str
                ),
                hubspot_ccn=True,
            )
            flash(f"Inviati {len(assigned_codes)} biglietti a {email}", "success")
        else:
            flash(
                "Errore: Mailer non configurato o nessun biglietto assegnato",
                "danger",
            )

    except Exception as e:
        flash(f"Errore durante l'invio: {str(e)}", "danger")

    return redirect("/sigep-ticket")
