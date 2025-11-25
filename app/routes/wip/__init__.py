from flask import Blueprint, render_template
from config.links import register_links

wip_bp = Blueprint("wip", __name__, url_prefix="/wip")

register_links("wip", [{
    "title": "WIP",
    "links": [
        {"name": "Biglietti Sigep", "url": "/wip/sigep-ticket", "description": "Gestione invio biglietti omaggio per il Sigep.", "icon": "bi bi-ticket-perforated-fill me-2"}
    ]
}])

@wip_bp.route("/", methods=["GET"])
def index():
    return render_template("index.html")