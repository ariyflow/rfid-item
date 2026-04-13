"""dashboard 相关"""

from flask import Blueprint, make_response, jsonify, send_from_directory
from .settings import *
from .dashboard_routes.analysis import analysis_bp
import os

dashboard_routes = Blueprint("dashboard", __name__, url_prefix="/dashboard")
dashboard_routes.register_blueprint(analysis_bp)

@dashboard_routes.route("/")
def default_handler():
    return make_response(send_from_directory(os.path.join(ROOT_DIR, STATIC_DIR, "html"), "dashboard.html"), 200)