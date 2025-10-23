from flask import Blueprint, render_template

agents_map_bp = Blueprint("agents_map", __name__, url_prefix="/agents_map")

@agents_map_bp.route("/", methods=["GET"])
def agents_map():
    return render_template("agents_map.html")