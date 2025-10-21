from flask import Blueprint, render_template, request, redirect, flash
import mysql.connector
from mysql.connector import errorcode
import pytz
from datetime import datetime
from mailer_pz import MailerPZ
import mysql.connector
from mysql.connector import errorcode

from config.config import ITALY_TZ
from config.interventi_db_config import DB_CONFIG

interventi_bp = Blueprint("interventi", __name__, url_prefix="/interventi")

# def init_db_interventi():
#     try:
#         conn = mysql.connector.connect(
#             user=DB_CONFIG['user'],
#             password=DB_CONFIG['password'],
#             host=DB_CONFIG['host'],
#         )
#         cursor = conn.cursor()

#         # Creazione del database se non esiste
#         cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_CONFIG['database']}")
#         conn.database = DB_CONFIG['database']

#         # Creazione tabella assets
#         cursor.execute("""
#             CREATE TABLE IF NOT EXISTS assets (
#                 id INT AUTO_INCREMENT PRIMARY KEY,
#                 nome VARCHAR(255) NOT NULL,
#                 tipologia ENUM('macchina', 'veicolo', 'oggetto') NOT NULL,
#                 posizione VARCHAR(255) NOT NULL,
#                 intervallo_manutenzione INT NOT NULL,
#                 intervallo_pulizia INT NOT NULL,
#                 data_ultima_manutenzione TIMESTAMP,
#                 data_ultima_pulizia TIMESTAMP,
#                 UNIQUE(nome, tipologia)
#             )
#         """)

#         # Creazione tabella interventi
#         cursor.execute("""
#             CREATE TABLE IF NOT EXISTS interventi (
#                 id INT AUTO_INCREMENT PRIMARY KEY,
#                 asset_id INT NOT NULL,
#                 tipologia ENUM('pulizia', 'manutenzione', 'riparazione') NOT NULL,
#                 descrizione TEXT,
#                 data TIMESTAMP NOT NULL,
#                 operatore VARCHAR(255) NOT NULL,
#                 FOREIGN KEY (asset_id) REFERENCES assets(id) ON DELETE CASCADE
#             )
#         """)

#         # Creazione tabella documenti
#         cursor.execute("""
#             CREATE TABLE IF NOT EXISTS documenti (
#                 id INT AUTO_INCREMENT PRIMARY KEY,
#                 intervento_id INT NOT NULL,
#                 data_aggiunta TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
#                 percorso VARCHAR(255) NOT NULL,
#                 FOREIGN KEY (intervento_id) REFERENCES interventi(id) ON DELETE CASCADE
#             )
#         """)

#         conn.commit()
#         print("Database e tabelle creati con successo.")

#     except mysql.connector.Error as err:
#         if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
#             print("Errore di autenticazione al database.")
#         elif err.errno == errorcode.ER_BAD_DB_ERROR:
#             print("Errore nella creazione o accesso al database.")
#         else:
#             print(f"Errore: {err}")
#     finally:
#         cursor.close()
#         conn.close()

@interventi_bp.route("/", methods=["GET", "POST"])
def interventi():
    if request.method == "POST":
        nome = request.form.get("nome", "").strip().lower()
        tipologia = request.form.get("tipologia", "").strip().lower()
        posizione = request.form.get("posizione", "").strip().lower()
        intervallo_manutenzione = int(request.form.get("intervallo_manutenzione", "").strip().lower())
        intervallo_pulizia = int(request.form.get("intervallo_pulizia", "").strip().lower())
        if nome and tipologia and posizione and intervallo_manutenzione and intervallo_pulizia:
            conn = mysql.connector.connect(**DB_CONFIG)
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM assets WHERE nome = %s AND tipologia = %s", (nome, tipologia))
            if cursor.fetchone():
                flash("Nel database è già presente un asset con questo nome e tipologia.", "warning")
            else:
                cursor.execute("INSERT INTO assets (nome, tipologia, posizione, intervallo_manutenzione, intervallo_pulizia) VALUES (%s, %s, %s, %s, %s)",
                               (nome, tipologia, posizione, intervallo_manutenzione, intervallo_pulizia))
                conn.commit()
                flash("Asset registrato con successo!", "success")
            cursor.close()
            conn.close()
            return redirect("/interventi")

    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM assets")
    entries = cursor.fetchall()
    converted_entries = []
    for id, nome, tipologia, posizione, intervallo_manutenzione, intervallo_pulizia, data_ultima_manutenzione, data_ultima_pulizia in entries:

        if data_ultima_manutenzione is not None:
            if data_ultima_manutenzione.tzinfo is None:
                data_ultima_manutenzione = pytz.utc.localize(data_ultima_manutenzione)
            local_data_ultima_manutenzione = data_ultima_manutenzione.astimezone(ITALY_TZ)
        else:
            local_data_ultima_manutenzione = None
    
        if data_ultima_pulizia is not None:
            if data_ultima_pulizia.tzinfo is None:
                data_ultima_pulizia = pytz.utc.localize(data_ultima_pulizia)
            local_data_ultima_pulizia = data_ultima_pulizia.astimezone(ITALY_TZ)
        else:
            local_data_ultima_pulizia = None

        converted_entries.append((
            id,
            nome,
            tipologia,
            posizione,
            intervallo_manutenzione,
            intervallo_pulizia, 
            local_data_ultima_manutenzione.strftime('%Y-%m-%d %H:%M:%S')  if local_data_ultima_manutenzione else 'N/A',
            local_data_ultima_pulizia.strftime('%Y-%m-%d %H:%M:%S')  if local_data_ultima_pulizia else 'N/A'
        ))
    
    cursor.close()
    conn.close()

    return render_template("interventi.html", entries=converted_entries)