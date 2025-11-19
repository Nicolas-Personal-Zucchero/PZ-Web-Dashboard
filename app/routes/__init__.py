from flask import Blueprint, render_template
from config.links import register_links

home_bp = Blueprint("home", __name__)

register_links("home", [{
    "title": "Clienti e Agenti",
    "links": [
        {"name": "Richiesta Recensione", "url": "/recensioni", "description": "Invia una mail di richiesta recensione ai clienti in modo rapido.", "icon": "bi bi-envelope-fill me-2"},
        {"name": "Assegna agente", "url": "/assegna-agente", "description": "Assegna un agente ad un contatto specifico con pochi click.", "icon": "bi bi-person-badge-fill me-2"},
        {"name": "Mappa agenti", "url": "/agents_map", "description": "Visualizza la mappa degli agenti divisi per provincia.", "icon": "bi bi-geo-alt-fill me-2"}
    ]
}])

@home_bp.route("/")
def home():
    return render_template("index.html")
