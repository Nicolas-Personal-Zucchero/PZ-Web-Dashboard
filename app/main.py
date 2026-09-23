import logging
import os
import sys

from flask import Flask, session, request
from extensions import db

from sqlalchemy import event
from sqlalchemy.engine import Engine
from sqlite3 import Connection as SQLite3Connection

# Necessari per la creazione delle tabelle nel database
from models.spedizioni import SpedizionePreliminare, SpedizioneIdentificativo
from models.recensioni import Review
from models.employees import Employee
from models.sigep_tickets import Ticket, TicketAssignment
from models.themes import Theme
from models.batches import Batch
from models.productions import Production

from config.links import get_links

from pages.home import home_bp
from pages.recensioni import recensioni_bp
from routes.assegna_agente import assegna_agente_bp
from routes.agents_map import agents_map_bp
from routes.sigep_ticket import sigep_ticket_bp
from routes.trattative_agenti import trattative_agenti_bp
from pages.etichette_spedizioni import etichette_spedizioni_bp
from pages.fercam import fercam_bp
from pages.preliminari import preliminari_bp
from pages.produzione_generici import produzione_generici_bp
from pages.produzione_generici_prod import (
    produzione_generici_prod_bp,
)

from routes.amministrazione.asset import asset_bp
from routes.amministrazione.asset_dettaglio import asset_dettaglio_bp
from routes.amministrazione.visualizza_impianti import visualizza_impianti_bp
from routes.amministrazione import amministrazione_bp
from routes.amministrazione.backups import backups_bp
from routes.amministrazione.gestione_lotti import gestione_lotti_bp
from routes.amministrazione.sigep_ticket_management import sigep_ticket_management_bp


# Forza l'attivazione del pragma foreign_keys ad ogni nuova connessione al database
@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    if isinstance(dbapi_connection, SQLite3Connection):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


def setup_logging():
    # Rimuove eventuali handler predefiniti per evitare duplicati
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)

    # Configura il formato e il livello (es. INFO o DEBUG da variabili d'ambiente)
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()

    logging.basicConfig(
        level=log_level,
        format="[%(asctime)s] %(levelname)s in %(module)s: %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )


def create_app():
    app = Flask(__name__)
    app.secret_key = os.getenv("SECRET_KEY") or os.urandom(24)

    # Limite massimo per il caricamento dei file (16MB)
    app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024

    # PostgreSQL Database setup
    postgres_user = os.getenv("POSTGRES_USER")
    postgres_password = os.getenv("POSTGRES_PASSWORD")
    postgres_host = os.getenv("POSTGRES_HOST")
    postgres_port = os.getenv("POSTGRES_PORT")
    postgres_db = os.getenv("POSTGRES_DB")
    postgres_uri = f"postgresql://{postgres_user}:{postgres_password}@{postgres_host}:{postgres_port}/{postgres_db}"

    # SQLite Database setup
    db_dir = os.path.join(app.instance_path)
    os.makedirs(db_dir, exist_ok=True)
    sqlite_uri = f"sqlite:///{os.path.join(db_dir, 'database.db')}"

    app.config["SQLALCHEMY_DATABASE_URI"] = postgres_uri
    app.config["SQLALCHEMY_BINDS"] = {"old_sqlite": sqlite_uri}

    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)

    with app.app_context():
        db.create_all()

    # Registrazione dei blueprint
    app.register_blueprint(home_bp)
    app.register_blueprint(recensioni_bp)
    app.register_blueprint(assegna_agente_bp)
    app.register_blueprint(agents_map_bp)
    app.register_blueprint(sigep_ticket_bp)
    app.register_blueprint(trattative_agenti_bp)
    app.register_blueprint(etichette_spedizioni_bp)
    app.register_blueprint(fercam_bp)
    app.register_blueprint(preliminari_bp)
    app.register_blueprint(produzione_generici_bp)
    app.register_blueprint(produzione_generici_prod_bp)

    amministrazione_bp.register_blueprint(gestione_lotti_bp)
    amministrazione_bp.register_blueprint(visualizza_impianti_bp)
    amministrazione_bp.register_blueprint(backups_bp)
    amministrazione_bp.register_blueprint(asset_bp)
    amministrazione_bp.register_blueprint(asset_dettaglio_bp)
    amministrazione_bp.register_blueprint(sigep_ticket_management_bp)
    app.register_blueprint(amministrazione_bp)

    @app.context_processor
    def inject_links():
        path = request.path

        # Mappatura path/section a tuple (args get_links..., home_link)
        sections = {
            "home": (["home"], "/"),
            "admin": (["home", "amministrazione"], "/amministrazione"),
        }

        # Determina la sezione corrente
        if path == "/":
            section = "home"
        elif path.startswith("/amministrazione"):
            section = "admin"
        else:
            section = session.get("section", "home")

        session["section"] = section
        args, home_link = sections.get(section, (["home"], "/"))

        return {"linkGroups": get_links(*args), "home_link": home_link}

    return app


setup_logging()

if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=5000)
