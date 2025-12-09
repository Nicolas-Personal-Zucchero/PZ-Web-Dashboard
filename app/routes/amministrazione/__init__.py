from flask import Blueprint, render_template
from config.links import register_links
from routes.amministrazione.secrets import secrets_bp

amministrazione_bp = Blueprint("amministrazione", __name__, url_prefix="/amministrazione")

register_links("amministrazione", [
    {
        "title": "Lotti e Impianti",
        "links": [
            {"name": "Gestione Lotti", "url": "/amministrazione/gestione_lotti", "description": "Registra un nuovo lotto o visualizza i lotti presenti nel database.", "icon": "bi bi-box-seam me-2"},
            {"name": "Visualizza Impianti", "url": "/amministrazione/visualizza_impianti", "description": "Visualizza lo stato e lo storico degli impianti.", "icon": "bi bi-clock-history me-2"}
        ]
    },
    {
        "title": "Asset",
        "links": [
            {"name": "Registro Manutenzioni e Pulizie", "url": "/amministrazione/asset", "description": "Visualizza il registro delle manutenzioni e pulizie.", "icon": "bi bi-tools me-2"},
        ]
    },
    {
        "title": "Database",
        "links": [
            {"name": "Scarica Backup", "url": "/amministrazione/backups", "description": "Scarica i backup dei database.", "icon": "bi bi-database-fill-down me-2"},
            {"name": "Gestione Token", "url": "/amministrazione/secrets", "description": "Gestisci i token e le chiavi segrete.", "icon": "bi bi-key-fill me-2"},
            {"name": "Gestione Biglietti Sigep", "url": "/amministrazione/sigep-ticket-management", "description": "Gestisci i biglietti del Sigep caricati sul database.", "icon": "bi bi-ticket-perforated-fill me-2"},
        ]
    }
])

amministrazione_bp.register_blueprint(secrets_bp)

@amministrazione_bp.route("/", methods=["GET"])
def index():
    return render_template("index.html")
