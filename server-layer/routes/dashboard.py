"""dashboard 相关"""

from flask import Blueprint, make_response, jsonify, send_from_directory, session, redirect, request
from functools import wraps
from .settings import *
from .dashboard_routes.analysis import analysis_bp
from .dashboard_routes.user_management import user_management_bp, ROOT_USERNAME
from .dashboard_routes.card_swipe import card_swipe_bp
from .dashboard_routes.rfid_card import rfid_card_bp
import os
from utils.config import get_config

config = get_config()
STATIC_DIR = config.get("STATIC_DIR", "static") if config else "static"

dashboard_routes = Blueprint("dashboard", __name__, url_prefix="/dashboard")
dashboard_routes.register_blueprint(analysis_bp)
dashboard_routes.register_blueprint(user_management_bp)
dashboard_routes.register_blueprint(card_swipe_bp)
dashboard_routes.register_blueprint(rfid_card_bp)


@dashboard_routes.before_request
def require_auth():
    """Protect all /dashboard routes - redirect to /admin if not authenticated."""
    if request.endpoint in ("dashboard.check_session_handler", "user_management.check_root_handler"):
        return

    if "username" not in session:
        return redirect("/admin")


@dashboard_routes.route("/")
def default_handler():
    return make_response(send_from_directory(os.path.join(ROOT_DIR, STATIC_DIR, "html"), "dashboard.html"), 200)


@dashboard_routes.route("/check", methods=["GET"])
def check_session_handler():
    """Frontend checks auth status here."""
    username = session.get("username")
    if username:
        is_root = username == ROOT_USERNAME
        return make_response(jsonify({"status": "authenticated", "username": username, "is_root": is_root}), 200)
    return make_response(jsonify({"status": "unauthenticated"}), 401)
