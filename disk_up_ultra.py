from flask import Blueprint

disk_up_ultra_bp = Blueprint("disk_up_ultra", __name__, url_prefix="/disk-up-ultra")

@disk_up_ultra_bp.route("/")
def index():
    return "Disk Up Ultra top page"
