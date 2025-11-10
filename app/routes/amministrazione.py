from flask import Blueprint, render_template
from config.links import register_links

amministrazione_bp = Blueprint("amministrazione", __name__, url_prefix="/amministrazione")

register_links("amministrazione", [
    {
        "title": "Lotti e Impianti",
        "links": [
            {"name": "Registrazione lotti", "url": "/amministrazione/registrazione_lotti", "description": "Registra nuovi lotti di zucchero e stampa la loro etichetta.", "icon": "bi bi-box-seam me-2"},
            {"name": "Visualizza lotti", "url": "/amministrazione/visualizza_lotti", "description": "Visualizza i lotti presenti nel database.", "icon": "bi bi-box-seam me-2"},
            {"name": "Visualizza impianti", "url": "/amministrazione/visualizza_impianti", "description": "Visualizza lo stato e lo storico degli impianti.", "icon": "bi bi-clock-history me-2"}
        ]
    },
    {
        "title": "Amministrazione Database",
        "links": [
            {"name": "Scarica backup", "url": "/amministrazione/backups", "description": "Scarica i backup dei database.", "icon": "bi bi-database-fill-down me-2"},
        ]
    }
])

@amministrazione_bp.route("/", methods=["GET"])
def index():
    return render_template("index.html")