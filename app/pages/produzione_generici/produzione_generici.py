import os
from datetime import datetime
from flask import Blueprint, flash, redirect, render_template, request, url_for
from services.employees import EmployeeService
from services.themes import ThemeService
from services.batches import BatchService
from services.productions import ProductionService

produzione_generici_bp = Blueprint(
    "produzione_generici",
    __name__,
    url_prefix="/produzione_generici",
    template_folder="",
)


def _redirect_to_index(theme_id=None, batch_id=None):
    params = {}
    if theme_id is not None:
        params["theme_id"] = theme_id
    if batch_id is not None:
        params["batch_id"] = batch_id
    return redirect(url_for("produzione_generici.produzione_generici", **params))


@produzione_generici_bp.route("/", methods=["GET"])
def produzione_generici():
    themes = ThemeService.get_all_themes(include_hidden=True)

    selected_theme = None
    batches = []
    selected_batch = None
    productions = []

    theme_id = request.args.get("theme_id", type=int)
    batch_id = request.args.get("batch_id", type=int)

    if theme_id is not None:
        selected_theme = ThemeService.get_theme_by_id(theme_id)
        if selected_theme is not None:
            batches = BatchService.get_batches_by_theme(theme_id)

    if selected_theme is not None and batch_id is not None:
        candidate_batch = BatchService.get_batch_by_id(batch_id)
        if (
            candidate_batch is not None
            and candidate_batch.theme_id == selected_theme.id
        ):
            selected_batch = candidate_batch
            productions = ProductionService.get_productions_by_batch(batch_id)
        else:
            selected_batch = None
            productions = []

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

    theme = ThemeService.create_theme(name)
    if not theme:
        flash(
            "Errore durante la creazione del tema. Verificare che il nome non sia già presente.",
            "error",
        )
        return _redirect_to_index()

    flash("Tema creato con successo.", "success")
    return _redirect_to_index(theme_id=theme.id)


@produzione_generici_bp.route("/modifica_tema/<int:theme_id>", methods=["POST"])
def edit_theme(theme_id):
    name = request.form.get("name", "").strip()
    hidden = request.form.get("hidden") == "on"

    if ThemeService.get_theme_by_id(theme_id) is None:
        flash("Tema non valido.", "error")
        return _redirect_to_index()

    result = ThemeService.update_theme(theme_id, name, hidden)
    if not result:
        flash(
            "Errore durante l'aggiornamento del tema. Verificare che il nome non sia già presente.",
            "error",
        )
        return _redirect_to_index(theme_id=theme_id)

    flash("Tema modificato con successo.", "success")
    return _redirect_to_index(theme_id=theme_id)


@produzione_generici_bp.route("/lotti", methods=["POST"])
def crea_lotto():
    theme_id = request.form.get("theme_id", type=int)
    code = request.form.get("code", "").strip()

    if theme_id is None or ThemeService.get_theme_by_id(theme_id) is None:
        flash("Tema non valido.", "error")
        return _redirect_to_index()

    if not code:
        flash("Il codice del lotto è obbligatorio.", "error")
        return _redirect_to_index(theme_id=theme_id)

    try:
        batch = BatchService.create_batch(theme_id, code)
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

    batch = BatchService.get_batch_by_id(batch_id) if batch_id is not None else None
    if batch is None:
        flash("Lotto non valido.", "error")
        return _redirect_to_index(theme_id=theme_id)

    if not reel_batch or not date_str or operator_id is None:
        flash("Tutti i campi sono obbligatori.", "error")
        return _redirect_to_index(theme_id=theme_id, batch_id=batch_id)

    try:
        date = datetime.strptime(date_str, "%Y-%m-%d")
        quantity = int(quantity_str)
    except ValueError:
        flash("Data o quantità non valide.", "error")
        return _redirect_to_index(theme_id=theme_id, batch_id=batch_id)

    try:
        ProductionService.create_production(
            batch_id, date, reel_batch, quantity, operator_id
        )
    except ValueError as e:
        flash(str(e), "error")
        return _redirect_to_index(theme_id=theme_id, batch_id=batch_id)

    flash("Produzione registrata con successo.", "success")
    return _redirect_to_index(theme_id=theme_id, batch_id=batch_id)


@produzione_generici_bp.route("/elimina_tema/<int:theme_id>", methods=["POST"])
def delete_theme(theme_id):
    if ThemeService.delete_theme(theme_id):
        flash("Tema eliminato con successo.", "success")
    else:
        flash("Errore durante l'eliminazione del tema.", "error")
    return _redirect_to_index()


@produzione_generici_bp.route("/modifica_lotto/<int:batch_id>", methods=["POST"])
def edit_batch(batch_id):
    theme_id = request.form.get("theme_id", type=int)
    code = request.form.get("code", "").strip()

    if BatchService.update_batch(batch_id, code=code):
        flash("Lotto modificato con successo.", "success")
    else:
        flash("Errore durante la modifica del lotto.", "error")
    return _redirect_to_index(theme_id=theme_id, batch_id=batch_id)


@produzione_generici_bp.route("/elimina_lotto/<int:batch_id>", methods=["POST"])
def delete_batch(batch_id):
    theme_id = request.form.get("theme_id", type=int)
    if BatchService.delete_batch(batch_id):
        flash("Lotto eliminato con successo.", "success")
        return _redirect_to_index(theme_id=theme_id)

    flash("Errore durante l'eliminazione del lotto.", "error")
    return _redirect_to_index(theme_id=theme_id, batch_id=batch_id)


@produzione_generici_bp.route(
    "/modifica_produzione/<int:production_id>", methods=["POST"]
)
def edit_production(production_id):
    theme_id = request.form.get("theme_id", type=int)
    batch_id = request.form.get("batch_id", type=int)

    try:
        date = datetime.strptime(request.form.get("date", "").strip(), "%Y-%m-%d")
        quantity = int(request.form.get("quantity", "").strip())
    except ValueError:
        flash("Data o quantità non valide.", "error")
        return _redirect_to_index(theme_id=theme_id, batch_id=batch_id)

    reel_batch = request.form.get("reel_batch", "").strip()
    operator_id = request.form.get("operator_id", type=int)

    if ProductionService.update_production(
        production_id,
        date=date,
        reel_batch=reel_batch,
        quantity=quantity,
        operator_id=operator_id,
    ):
        flash("Produzione modificata con successo.", "success")
    else:
        flash("Errore durante la modifica della produzione.", "error")
    return _redirect_to_index(theme_id=theme_id, batch_id=batch_id)


@produzione_generici_bp.route(
    "/elimina_produzione/<int:production_id>", methods=["POST"]
)
def delete_production(production_id):
    theme_id = request.form.get("theme_id", type=int)
    batch_id = request.form.get("batch_id", type=int)

    if ProductionService.delete_production(production_id):
        flash("Produzione eliminata con successo.", "success")
    else:
        flash("Errore durante l'eliminazione della produzione.", "error")
    return _redirect_to_index(theme_id=theme_id, batch_id=batch_id)
