from flask import Blueprint, render_template
from config.links import register_links

wip_bp = Blueprint("wip", __name__, url_prefix="/wip")

register_links("wip", [{
    "title": "WIP",
    "links": [
        {"name": "Interventi", "url": "/wip/interventi", "description": "Gestisci gli interventi programmati o richiesti dai clienti.", "icon": "bi bi-tools me-2"}
    ]
}])

@wip_bp.route("/", methods=["GET"])
def index():
    return render_template("index.html")