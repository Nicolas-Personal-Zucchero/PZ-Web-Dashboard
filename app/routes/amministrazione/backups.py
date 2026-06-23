from flask import Blueprint, render_template, send_file, abort
import os
import shutil
import tempfile
from werkzeug.utils import safe_join

backups_bp = Blueprint('backup', __name__, url_prefix='/backups')

BACKUP_FOLDER = "/backups/"

@backups_bp.route("/")
def list_backups():
    backup_tree = {}

    if os.path.exists(BACKUP_FOLDER):
        for main_folder in os.listdir(BACKUP_FOLDER):
            main_path = os.path.join(BACKUP_FOLDER, main_folder)
            if os.path.isdir(main_path):
                subfolders = [
                    f for f in os.listdir(main_path)
                    if os.path.isdir(os.path.join(main_path, f))
                ]
                subfolders.sort()
                backup_tree[main_folder] = subfolders

    return render_template("/amministrazione/backups.html", backup_tree=backup_tree)

@backups_bp.route("/download/all")
def download_all_backups():
    if not os.path.exists(BACKUP_FOLDER):
        abort(404, description="Directory di backup non trovata.")

    temp_zip = tempfile.NamedTemporaryFile(delete=False, suffix=".zip")
    shutil.make_archive(temp_zip.name[:-4], 'zip', BACKUP_FOLDER)
    return send_file(temp_zip.name, as_attachment=True, download_name="all_backups.zip")

@backups_bp.route("/download/<path:folder_path>")
def download_single_backup(folder_path):
    target_dir = safe_join(BACKUP_FOLDER, folder_path)

    if not target_dir or not os.path.isdir(target_dir):
        abort(404, description="Cartella non trovata o accesso negato.")

    temp_zip = tempfile.NamedTemporaryFile(delete=False, suffix=".zip")
    shutil.make_archive(temp_zip.name[:-4], 'zip', target_dir)
    safe_filename = folder_path.replace("/", "_") + ".zip"
    return send_file(temp_zip.name, as_attachment=True, download_name=safe_filename)