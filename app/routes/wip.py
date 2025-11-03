from flask import Blueprint, render_template

wip_bp = Blueprint("wip", __name__, url_prefix="/wip")

@wip_bp.route("/", methods=["GET"])
def index():
    return render_template("wip.html")