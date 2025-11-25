import csv
import io
from flask import Blueprint, render_template, request, redirect, flash
from firebase_admin import firestore
from utils.firebase_client import db
from config.secrets_manager import secrets_manager
from config.mail_config import EMAIL_TEMPLATES
import random

sigep_ticket_bp = Blueprint("sigep_ticket", __name__, url_prefix="/sigep-ticket")
tickets_collection = db.collection("sigep_tickets")

@sigep_ticket_bp.route("/", methods=["GET"])
def index():
    # Count available tickets
    # Note: For large collections, aggregation queries are better, but for this scale stream/len is okay or count() if available
    # Using count() aggregation if supported by the SDK version, otherwise stream
    
    try:
        aggregate_query = tickets_collection.where("assigned", "==", False).count()
        results = aggregate_query.get()
        available_count = int(results[0][0].value)
    except Exception:
        # Fallback if count() is not available or fails
        docs = tickets_collection.where("assigned", "==", False).stream()
        available_count = len(list(docs))

    return render_template("/wip/sigep_ticket.html", available_count=available_count)

@sigep_ticket_bp.route("/upload", methods=["POST"])
def upload():
    if "file" not in request.files:
        flash("Nessun file caricato", "danger")
        return redirect("/wip/sigep-ticket")
    
    file = request.files["file"]
    column_name = request.form.get("column_name", "").strip()

    if not file or not column_name:
        flash("File o nome colonna mancanti", "danger")
        return redirect("/wip/sigep-ticket")

    try:
        file_content = file.stream.read().decode("UTF8")
        stream = io.StringIO(file_content, newline=None)
        
        try:
            dialect = csv.Sniffer().sniff(file_content[:4096], delimiters=";,")
            stream.seek(0)
            csv_input = csv.DictReader(stream, dialect=dialect)
        except csv.Error:
            stream.seek(0)
            csv_input = csv.DictReader(stream)
        
        if column_name not in csv_input.fieldnames:
            flash(f"Colonna '{column_name}' non trovata nel CSV", "danger")
            return redirect("/wip/sigep-ticket")

        batch = db.batch()
        count = 0
        for row in csv_input:
            code = row[column_name].strip()
            if code:
                doc_ref = tickets_collection.document()
                batch.set(doc_ref, {
                    "code": code,
                    "assigned": False,
                    "created_at": firestore.SERVER_TIMESTAMP
                })
                count += 1
                if count % 400 == 0:
                    batch.commit()
                    batch = db.batch()
        
        if count % 400 != 0:
            batch.commit()

        flash(f"Caricati {count} biglietti con successo", "success")

    except Exception as e:
        flash(f"Errore durante il caricamento: {str(e)}", "danger")

    return redirect("/wip/sigep-ticket")

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
        return redirect("/wip/sigep-ticket")

    # Transaction to get random tickets
    transaction = db.transaction()
    
    try:
        assigned_codes = assign_tickets_transaction(transaction, count, email, name)
        
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

    return redirect("/wip/sigep-ticket")

@firestore.transactional
def assign_tickets_transaction(transaction, count, email, name):
    # Query for unassigned tickets
    # Note: Getting random documents efficiently in Firestore is hard.
    # We will query for 'count' unassigned tickets. Ideally we should randomize, 
    # but for this use case, taking the first 'count' available is acceptable 
    # as they are all identical in value.
    
    query = tickets_collection.where("assigned", "==", False).limit(count)
    stream = query.stream(transaction=transaction)
    docs = list(stream)

    if len(docs) < count:
        raise Exception(f"Non ci sono abbastanza biglietti disponibili. Richiesti: {count}, Disponibili: {len(docs)}")

    codes = []
    for doc in docs:
        transaction.update(doc.reference, {
            "assigned": True,
            "assigned_to_email": email,
            "assigned_to_name": name,
            "assigned_at": firestore.SERVER_TIMESTAMP
        })
        codes.append(doc.get("code"))
    
    return codes

@sigep_ticket_bp.route("/clear", methods=["POST"])
def clear_collection():
    try:
        # Delete all documents in batches
        docs = tickets_collection.limit(100).stream()
        deleted = 0
        for doc in docs:
            doc.reference.delete()
            deleted += 1
        
        # If we deleted 100, there might be more. 
        # For a simple implementation, we can just ask the user to click again or loop here.
        # Let's loop a few times to be safe, but avoid infinite loops.
        while deleted > 0 and deleted % 100 == 0:
             batch_docs = tickets_collection.limit(100).stream()
             batch_deleted = 0
             for doc in batch_docs:
                 doc.reference.delete()
                 batch_deleted += 1
             deleted += batch_deleted
             if batch_deleted == 0:
                 break

        flash("Collezione biglietti svuotata (o parzialmente svuotata)", "success")
    except Exception as e:
        flash(f"Errore durante la cancellazione: {str(e)}", "danger")

    return redirect("/wip/sigep-ticket")
