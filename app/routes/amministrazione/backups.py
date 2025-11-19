from flask import Blueprint, render_template, send_file
import os
import shutil
import tempfile

backups_bp = Blueprint('backup', __name__, url_prefix='/backups')

# Percorso cartella backup dentro al container
BACKUP_FOLDER = "/backups"

@backups_bp.route("/")
def list_backups():
    # Raccoglie tutte le cartelle nella directory dei backup
    folders = [
        f for f in os.listdir(BACKUP_FOLDER)
        if os.path.isdir(os.path.join(BACKUP_FOLDER, f))
    ]
    # Ordina per data (più recente prima)
    folders.sort(key=lambda f: os.path.getmtime(os.path.join(BACKUP_FOLDER, f)), reverse=True)

    return render_template("amministrazione/backups.html", folders=folders)


@backups_bp.route("/download/all")
def download_all_backups():
    # Crea zip temporaneo
    temp_zip = tempfile.NamedTemporaryFile(delete=False, suffix=".zip")
    shutil.make_archive(temp_zip.name[:-4], 'zip', BACKUP_FOLDER)
    return send_file(temp_zip.name, as_attachment=True, download_name="all_backups.zip")


@backups_bp.route("/download/<folder>")
def download_single_backup(folder):
    folder_path = os.path.join(BACKUP_FOLDER, folder)
    if not os.path.isdir(folder_path):
        return "Cartella non trovata.", 404

    temp_zip = tempfile.NamedTemporaryFile(delete=False, suffix=".zip")
    shutil.make_archive(temp_zip.name[:-4], 'zip', folder_path)
    return send_file(temp_zip.name, as_attachment=True, download_name=f"{folder}.zip")