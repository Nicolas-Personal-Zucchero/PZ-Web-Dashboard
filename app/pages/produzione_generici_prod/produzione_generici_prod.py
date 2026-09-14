import os
from datetime import datetime
from flask import Blueprint, flash, redirect, render_template, request, url_for
from services.employees import EmployeeService
from services.themes import ThemeService
from services.batches import BatchService
from services.productions import ProductionService

template_dir = os.path.abspath(os.path.dirname(__file__))
produzione_generici_prod_bp = Blueprint("produzione_generici_prod", __name__, url_prefix="/produzione_generici_prod", template_folder="")

@produzione_generici_prod_bp.route("/", methods=["GET"])
def team_produzione():
    themes = ThemeService.get_all_themes()
    latest_batches = {}

    for theme in themes:
        batches = BatchService.get_batches_by_theme(theme.id)
        if batches:
            latest_batches[theme.id] = max(
                batches,
                key=lambda b: (b.created_at or datetime.min, b.id),
            )

    selected_theme = None
    selected_batch = None
    productions = []

    theme_id = request.args.get("theme_id", type=int)
    if theme_id is not None:
        selected_theme = ThemeService.get_theme_by_id(theme_id)
        if selected_theme is not None:
            selected_batch = latest_batches.get(selected_theme.id)
            if selected_batch is not None:
                productions = ProductionService.get_productions_by_batch(selected_batch.id)

    return render_template(
        "produzione_generici_prod.html",
        generici=themes,
        selected_theme=selected_theme,
        selected_batch=selected_batch,
        productions=productions,
        latest_batches=latest_batches,
        employees=EmployeeService.get_employees(departments=["Reparto Zucchero"]),
        today=datetime.now().strftime("%Y-%m-%d"),
    )

@produzione_generici_prod_bp.route("/produzioni", methods=["POST"])
def crea_produzione_team():
    theme_id = request.form.get("theme_id", type=int)
    date_str = request.form.get("date", "").strip()
    reel_batch = request.form.get("reel_batch", "").strip()
    quantity_str = request.form.get("quantity", "").strip()
    operator_id = request.form.get("operator_id", type=int)

    theme = ThemeService.get_theme_by_id(theme_id) if theme_id is not None else None
    if theme is None:
        flash("Tema non valido.", "error")
        return redirect(url_for("produzione_generici_prod.team_produzione"))

    batches = BatchService.get_batches_by_theme(theme.id)
    batch = max(
        batches,
        key=lambda b: (b.created_at or datetime.min, b.id),
        default=None,
    )

    if batch is None:
        flash("Il tema selezionato non ha ancora un lotto disponibile.", "error")
        return redirect(url_for("produzione_generici_prod.team_produzione", theme_id=theme.id))

    if not reel_batch or not date_str or operator_id is None:
        flash("Tutti i campi sono obbligatori.", "error")
        return redirect(url_for("produzione_generici_prod.team_produzione", theme_id=theme.id))

    try:
        date = datetime.strptime(date_str, "%Y-%m-%d")
        quantity = int(quantity_str)
    except ValueError:
        flash("Data o quantità non valide.", "error")
        return redirect(url_for("produzione_generici_prod.team_produzione", theme_id=theme.id))

    try:
        ProductionService.create_production(
            batch.id, date, reel_batch, quantity, operator_id
        )
    except ValueError as e:
        flash(str(e), "error")
        return redirect(url_for("produzione_generici_prod.team_produzione", theme_id=theme.id))

    flash(f"Produzione registrata.Procedere con la stampa delle etichette per il lotto {theme.name} {batch.code}", "success")
    return redirect(url_for("produzione_generici_prod.team_produzione", theme_id=theme.id))