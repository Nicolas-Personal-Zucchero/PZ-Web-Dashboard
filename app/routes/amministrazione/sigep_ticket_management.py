import csv
import io
from flask import Blueprint, render_template, request, redirect, flash
from firebase_admin import firestore
from utils.firebase_client import db

sigep_ticket_management_bp = Blueprint("sigep_ticket_management", __name__, url_prefix="/sigep-ticket-management")
tickets_collection = db.collection("sigep_tickets")

@sigep_ticket_management_bp.route("/", methods=["GET"])
def index():
    return render_template("/amministrazione/sigep_ticket_management.html")
                       
@sigep_ticket_management_bp.route("/upload", methods=["POST"])
def upload():
    if "file" not in request.files:
        flash("Nessun file caricato", "danger")
        return redirect("/sigep-ticket")
    
    file = request.files["file"]
    column_name = request.form.get("column_name", "").strip()

    if not file or not column_name:
        flash("File o nome colonna mancanti", "danger")
        return redirect("/sigep-ticket")

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
            return redirect("/sigep-ticket")

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

    return redirect("/sigep-ticket")

@sigep_ticket_management_bp.route("/clear", methods=["POST"])
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

    return redirect("/sigep-ticket")