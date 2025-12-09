import csv
import io
from flask import Blueprint, render_template, request, redirect, flash
from firebase_admin import firestore
from utils.firebase_client import db
from config.secrets_manager import secrets_manager
from config.mail_config import EMAIL_TEMPLATES


sigep_ticket_bp = Blueprint("sigep_ticket", __name__, url_prefix="/sigep-ticket")
tickets_collection = db.collection("sigep_tickets")

@sigep_ticket_bp.route("/", methods=["GET"])
def index():
    # --- OTTIMIZZAZIONE 1: Count ---
    # Usiamo direttamente count(). Se fallisce, è meglio ricevere un errore 
    # piuttosto che mandare in crash la RAM caricando migliaia di documenti in una lista.
    available_query = tickets_collection.where("assigned", "==", False).count()
    available_results = available_query.get()
    available_count = int(available_results[0][0].value)

    # --- OTTIMIZZAZIONE 2: Projection ---
    # Scarichiamo SOLO i campi che ci servono.
    assigned_docs = tickets_collection.where("assigned", "==", True)\
                                      .select(["assigned_to", "code"])\
                                      .stream()
    
    assigned_map = {}

    for doc in assigned_docs:
        data = doc.to_dict()
        email = data.get("assigned_to")
        
        # Saltiamo record senza email
        if not email:
            continue

        # Logica semplificata
        if email not in assigned_map:
            assigned_map[email] = {
                "email": email,
                "count": 0,
                "codes": []
            }
        
        assigned_map[email]["count"] += 1
        if data.get("code"):
            assigned_map[email]["codes"].append(data.get("code"))

    # Ordinamento
    assigned_list = sorted(assigned_map.values(), key=lambda x: x["count"], reverse=True)

    return render_template("/sigep_ticket.html", available_count=available_count, assigned_list=assigned_list)

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

    # Transaction to get tickets
    transaction = db.transaction()
    
    try:
        assigned_codes = assign_tickets_transaction(transaction, count, email)
        
        # Send email
        mailer = secrets_manager.get_mailer()
        if mailer and assigned_codes:
            codes_str = "<br>".join([f"<b>{code}</b>" for code in assigned_codes])
            template_key = f"sigep_{language}"
            if template_key not in EMAIL_TEMPLATES:
                template_key = "sigep_ita" # Fallback
            
            subject = EMAIL_TEMPLATES[template_key]["object"]
            body = EMAIL_TEMPLATES[template_key]["body"].format(
                nome_cliente=name,
                codici_biglietti=codes_str
            )
            
            mailer.invia_email_singola(email, subject, body, hubspot_ccn=True)
            flash(f"Inviati {len(assigned_codes)} biglietti a {email}", "success")
        else:
            flash("Errore: Mailer non configurato o nessun biglietto assegnato", "danger")

    except Exception as e:
        flash(f"Errore durante l'invio: {str(e)}", "danger")

    return redirect("/sigep-ticket")

@firestore.transactional
def assign_tickets_transaction(transaction, count, email):
    # Query for unassigned tickets
    # Query for 'count' unassigned tickets.
    # We take the first 'count' available tickets.
    
    query = tickets_collection.where("assigned", "==", False).limit(count)
    stream = query.stream(transaction=transaction)
    docs = list(stream)

    if len(docs) < count:
        raise Exception(f"Non ci sono abbastanza biglietti disponibili. Richiesti: {count}, Disponibili: {len(docs)}")

    codes = []
    for doc in docs:
        transaction.update(doc.reference, {
            "assigned": True,
            "assigned_to": email,
            "assigned_at": firestore.SERVER_TIMESTAMP
        })
        codes.append(doc.get("code"))
    
    return codes