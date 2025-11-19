from flask import Blueprint, render_template, request, flash, redirect
from config.secrets_manager import secrets_manager

secrets_bp = Blueprint("secrets", __name__, url_prefix="/secrets")

@secrets_bp.route("/", methods=["GET", "POST"])
def manage_secrets():
    current_secrets = secrets_manager.get_all_secrets()
    
    if request.method == "POST":
        action = request.form.get("action")
        
        if action == "update":
            new_secrets = current_secrets.copy()
            # Update existing keys
            for key in current_secrets:
                new_value = request.form.get(key)
                if new_value is not None:
                    new_secrets[key] = new_value.strip()
            
            secrets_manager.save_secrets(new_secrets)
            flash("Token aggiornati con successo!", "success")
            return redirect("/amministrazione/secrets")

        elif action == "add":
            new_secrets = current_secrets.copy()
            new_key = request.form.get("new_key_name")
            new_val = request.form.get("new_key_value")
            
            if new_key and new_val:
                key_clean = new_key.strip()
                if key_clean in new_secrets:
                    flash(f"Errore: La chiave '{key_clean}' esiste già.", "danger")
                else:
                    new_secrets[key_clean] = new_val.strip()
                    secrets_manager.save_secrets(new_secrets)
                    flash("Nuovo token aggiunto con successo!", "success")
            else:
                flash("Errore: Nome chiave e valore sono obbligatori.", "warning")
            
            return redirect("/amministrazione/secrets")
            
        elif action == "delete":
            key_to_delete = request.form.get("key_to_delete")
            if key_to_delete and key_to_delete in current_secrets:
                new_secrets = current_secrets.copy()
                del new_secrets[key_to_delete]
                secrets_manager.save_secrets(new_secrets)
                flash(f"Chiave '{key_to_delete}' eliminata.", "success")
                return redirect("/amministrazione/secrets")

    return render_template("amministrazione/secrets.html", secrets=current_secrets)
