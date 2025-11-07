from flask import Blueprint, render_template, send_from_directory
import os

backups_bp = Blueprint('backup', __name__, url_prefix='/backups')

# Percorso cartella backup dentro al container
BACKUP_FOLDER = "/backups"

@backups_bp.route("/")
def list_backups():
    files = os.listdir(BACKUP_FOLDER)
    files = [f for f in files if os.path.isfile(os.path.join(BACKUP_FOLDER, f))]
    # Ordina per data di modifica (dal più recente)
    files.sort(key=lambda f: os.path.getmtime(os.path.join(BACKUP_FOLDER, f)), reverse=True)
    return render_template("backups.html", files=files)

@backups_bp.route("/download/<filename>")
def download_backup(filename):
    return send_from_directory(BACKUP_FOLDER, filename, as_attachment=True)