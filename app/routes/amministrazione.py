from flask import Blueprint, render_template

amministrazione_bp = Blueprint("amministrazione", __name__, url_prefix="/amministrazione")

@amministrazione_bp.route("/", methods=["GET"])
def index():
    return render_template("amministrazione.html")