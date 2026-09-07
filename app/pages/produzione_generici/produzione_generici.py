import os
from datetime import datetime
from decimal import Decimal, InvalidOperation
from flask import Blueprint, redirect, render_template, flash, request, url_for, current_app
from services.themes import ThemeProductionService
from services.employees import EmployeeService

template_dir = os.path.abspath(os.path.dirname(__file__))
produzione_generici_bp = Blueprint("produzione_generici", __name__, url_prefix="/produzione_generici", template_folder="")

def _redirect_to_index(theme_id=None, batch_id=None):
    params = {}
    if theme_id is not None:
        params["theme_id"] = theme_id
    if batch_id is not None:
        params["batch_id"] = batch_id
    return redirect(url_for("produzione_generici.produzione_generici", **params))

@produzione_generici_bp.route("/", methods=["GET"])
def produzione_generici():
    themes = ThemeProductionService.get_all_themes()

    selected_theme = None
    batches = []
    selected_batch = None
    productions = []

    theme_id = request.args.get("theme_id", type=int)
    batch_id = request.args.get("batch_id", type=int)

    if theme_id is not None:
        selected_theme = ThemeProductionService.get_theme_by_id(theme_id)
        if selected_theme is not None:
            batches = ThemeProductionService.get_batches_by_theme(theme_id)

    if selected_theme is not None and batch_id is not None:
        candidate_batch = ThemeProductionService.get_batch_by_id(batch_id)
        if candidate_batch is not None and candidate_batch.theme_id == selected_theme.id:
            selected_batch = candidate_batch
            productions = ThemeProductionService.get_productions_by_batch(batch_id)

    return render_template(
        "themes.html",
        generici=themes,
        selected_theme=selected_theme,
        batches=batches,
        selected_batch=selected_batch,
        productions=productions,
        employees=EmployeeService.get_employees(departments=["Reparto Zucchero"]),
        today=datetime.now().strftime("%Y-%m-%d"),
    )

@produzione_generici_bp.route("/temi", methods=["POST"])
def create_theme():
    name = request.form.get("name", "").strip()
    if not name:
        flash("Il nome del tema è obbligatorio.", "error")
        return _redirect_to_index()

    try:
        theme = ThemeProductionService.create_theme(name)
    except ValueError as e:
        flash(str(e), "error")
        return _redirect_to_index()

    flash("Tema creato con successo.", "success")
    return _redirect_to_index(theme_id=theme.id)

@produzione_generici_bp.route("/lotti", methods=["POST"])
def crea_lotto():
    theme_id = request.form.get("theme_id", type=int)
    code = request.form.get("code", "").strip()

    if theme_id is None or ThemeProductionService.get_theme_by_id(theme_id) is None:
        flash("Tema non valido.", "error")
        return _redirect_to_index()

    if not code:
        flash("Il codice del lotto è obbligatorio.", "error")
        return _redirect_to_index(theme_id=theme_id)

    try:
        batch = ThemeProductionService.create_batch(theme_id, code)
    except ValueError as e:
        flash(str(e), "error")
        return _redirect_to_index(theme_id=theme_id)

    flash("Lotto creato con successo.", "success")
    return _redirect_to_index(theme_id=theme_id, batch_id=batch.id)

@produzione_generici_bp.route("/produzioni", methods=["POST"])
def crea_produzione():
    theme_id = request.form.get("theme_id", type=int)
    batch_id = request.form.get("batch_id", type=int)
    date_str = request.form.get("date", "").strip()
    reel_batch = request.form.get("reel_batch", "").strip()
    quantity_str = request.form.get("quantity", "").strip()
    operator_id = request.form.get("operator_id", type=int)

    batch = ThemeProductionService.get_batch_by_id(batch_id) if batch_id is not None else None
    if batch is None:
        flash("Lotto non valido.", "error")
        return _redirect_to_index(theme_id=theme_id)

    if not reel_batch or not date_str or operator_id is None:
        flash("Tutti i campi sono obbligatori.", "error")
        return _redirect_to_index(theme_id=theme_id, batch_id=batch_id)

    try:
        date = datetime.strptime(date_str, "%Y-%m-%d")
        quantity = Decimal(quantity_str)
    except (ValueError, InvalidOperation):
        flash("Data o quantità non valide.", "error")
        return _redirect_to_index(theme_id=theme_id, batch_id=batch_id)

    try:
        ThemeProductionService.create_production(batch_id, date, reel_batch, quantity, operator_id)
    except ValueError as e:
        flash(str(e), "error")
        return _redirect_to_index(theme_id=theme_id, batch_id=batch_id)

    flash("Produzione registrata con successo.", "success")
    return _redirect_to_index(theme_id=theme_id, batch_id=batch_id)
