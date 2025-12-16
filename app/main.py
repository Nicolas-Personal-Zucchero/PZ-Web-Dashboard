from flask import Flask, render_template

from config.links import register_links, get_links

from routes.wip import wip_bp

from routes import home_bp
from routes.recensioni import recensioni_bp
from routes.assegna_agente import assegna_agente_bp
from routes.agents_map import agents_map_bp
from routes.sigep_ticket import sigep_ticket_bp
from routes.trattative_agenti import trattative_agenti_bp

from routes.amministrazione.asset import asset_bp
from routes.amministrazione.visualizza_impianti import visualizza_impianti_bp
from routes.amministrazione import amministrazione_bp
from routes.amministrazione.backups import backups_bp
from routes.amministrazione.gestione_lotti import gestione_lotti_bp
from routes.amministrazione.sigep_ticket_management import sigep_ticket_management_bp

app = Flask(__name__)
app.secret_key = "supersecretkey"  # Serve per flash()

app.register_blueprint(wip_bp)

app.register_blueprint(home_bp)
app.register_blueprint(recensioni_bp)
app.register_blueprint(assegna_agente_bp)
app.register_blueprint(agents_map_bp)
app.register_blueprint(sigep_ticket_bp)
app.register_blueprint(trattative_agenti_bp)

amministrazione_bp.register_blueprint(gestione_lotti_bp)
amministrazione_bp.register_blueprint(visualizza_impianti_bp)
amministrazione_bp.register_blueprint(backups_bp)
amministrazione_bp.register_blueprint(asset_bp)
amministrazione_bp.register_blueprint(sigep_ticket_management_bp)
app.register_blueprint(amministrazione_bp)

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

# Ignorato da gunicorn
if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000
    )