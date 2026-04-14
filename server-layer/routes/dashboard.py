"""dashboard 相关"""

from flask import Blueprint, make_response, jsonify, send_from_directory, session, redirect, request
from functools import wraps
from .settings import *
from .dashboard_routes.analysis import analysis_bp
import os

dashboard_routes = Blueprint("dashboard", __name__, url_prefix="/dashboard")
dashboard_routes.register_blueprint(analysis_bp)


@dashboard_routes.before_request
def require_auth():
    """Protect all /dashboard routes - redirect to /admin if not authenticated."""
    if request.endpoint == "dashboard.check_session_handler":
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
        return make_response(jsonify({"status": "authenticated", "username": username}), 200)
    return make_response(jsonify({"status": "unauthenticated"}), 401)
