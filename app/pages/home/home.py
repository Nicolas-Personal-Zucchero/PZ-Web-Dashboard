import os
from flask import (
    Blueprint,
    render_template,
)

home_bp = Blueprint("home", __name__, template_folder="")


@home_bp.route("/")
def home():
    return render_template("index.html")
