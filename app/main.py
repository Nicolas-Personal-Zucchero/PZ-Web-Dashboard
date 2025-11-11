from flask import Flask, render_template

from config.links import register_links, get_links
from routes.assegna_agente import assegna_agente_bp
from routes.recensioni import recensioni_bp
from routes.asset import asset_bp
from routes.registrazione_lotti import registrazione_lotti_bp
from routes.wip import wip_bp
from routes.agents_map import agents_map_bp
from routes.visualizza_lotti import visualizza_lotti_bp
from routes.visualizza_impianti import visualizza_impianti_bp
from routes.amministrazione import amministrazione_bp
from routes.backups import backups_bp

app = Flask(__name__)
app.secret_key = "supersecretkey"  # Serve per flash()

app.register_blueprint(recensioni_bp)
app.register_blueprint(assegna_agente_bp)
app.register_blueprint(agents_map_bp)

amministrazione_bp.register_blueprint(registrazione_lotti_bp)
amministrazione_bp.register_blueprint(visualizza_lotti_bp)
amministrazione_bp.register_blueprint(visualizza_impianti_bp)
amministrazione_bp.register_blueprint(backups_bp)
app.register_blueprint(amministrazione_bp)

wip_bp.register_blueprint(asset_bp)
app.register_blueprint(wip_bp)

register_links("home", [{
    "title": "Clienti e Agenti",
    "links": [
        {"name": "Richiesta Recensione", "url": "/recensioni", "description": "Invia una mail di richiesta recensione ai clienti in modo rapido.", "icon": "bi bi-envelope-fill me-2"},
        {"name": "Assegna agente", "url": "/assegna-agente", "description": "Assegna un agente ad un contatto specifico con pochi click.", "icon": "bi bi-person-badge-fill me-2"},
        {"name": "Mappa agenti", "url": "/agents_map", "description": "Visualizza la mappa degli agenti divisi per provincia.", "icon": "bi bi-geo-alt-fill me-2"}
    ]
}])

@app.context_processor
def inject_links():
    from flask import session, request
    from config.links import get_links

    path = request.path

    # Mappatura path/section a tuple (args get_links..., home_link)
    sections = {
        'home': (['home'], '/'),
        'admin': (['home', 'amministrazione'], '/amministrazione'),
        'wip': (['wip'], '/wip'),
    }

    # Determina la sezione corrente
    if path == "/":
        section = 'home'
    elif path.startswith("/amministrazione"):
        section = 'admin'
    elif path.startswith("/wip"):
        section = 'wip'
    else:
        section = session.get('section', 'home')

    session['section'] = section
    args, home_link = sections.get(section, (['home'], '/'))

    return {
        'linkGroups': get_links(*args),
        'home_link': home_link
    }

@app.route("/")
def home():
    return render_template("index.html")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)