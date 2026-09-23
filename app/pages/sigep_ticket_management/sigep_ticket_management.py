import csv
import io
from flask import Blueprint, flash, redirect, render_template, request

from services.sigep_tickets import SigepTicketService

sigep_ticket_management_bp = Blueprint(
    "sigep_ticket_management",
    __name__,
    url_prefix="/sigep-ticket-management",
    template_folder="",
)


@sigep_ticket_management_bp.route("/", methods=["GET"])
def index():
    return render_template("sigep_ticket_management.html")


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

        if not csv_input.fieldnames or column_name not in csv_input.fieldnames:
            flash(f"Colonna '{column_name}' non trovata nel CSV", "danger")
            return redirect("/sigep-ticket")

        codes = [
            row[column_name].strip()
            for row in csv_input
            if row.get(column_name) and row[column_name].strip()
        ]

        inserted_count = SigepTicketService.bulk_create_tickets(codes)
        flash(f"Caricati {inserted_count} nuovi biglietti con successo", "success")

    except Exception as e:
        flash(f"Errore durante il caricamento: {str(e)}", "danger")

    return redirect("/sigep-ticket")


@sigep_ticket_management_bp.route("/clear", methods=["POST"])
def clear_collection():
    try:
        deleted_count = SigepTicketService.clear_all_tickets()
        flash(f"Cancellati {deleted_count} biglietti con successo", "success")
    except Exception as e:
        flash(f"Errore durante la cancellazione: {str(e)}", "danger")

    return redirect("/sigep-ticket")
