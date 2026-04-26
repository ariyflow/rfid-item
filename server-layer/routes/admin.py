"""Admin login routes"""

from flask import Blueprint, request, make_response, jsonify, session, redirect, send_from_directory
import hashlib
from model.dbObject import db
import os
from .settings import ROOT_DIR
from utils.config import get_config

config = get_config()
STATIC_DIR = config.get("STATIC_DIR", "static") if config else "static"

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


@admin_bp.route("/")
def admin_handler():
    """Serve the admin login page"""
    return make_response(send_from_directory(os.path.join(ROOT_DIR, STATIC_DIR, "html"), "admin_login.html"), 200)


@admin_bp.route("/login", methods=["POST"])
def admin_login_handler():
    """Handle login - validate credentials, set session, redirect to /dashboard"""
    data = request.get_json() or {}
    username = data.get("username", "").strip()
    password = data.get("password", "")

    if not username or not password:
        return make_response(jsonify({"status": "error", "message": "Missing username or password"}), 400)

    result = db.get_auth_pwd(username)
    if result["status"] != "success":
        return make_response(jsonify({"status": "error", "message": "Invalid credentials"}), 401)

    password_hash = hashlib.sha256(password.encode()).hexdigest()
    if password_hash != result["password_hash"]:
        return make_response(jsonify({"status": "error", "message": "Invalid credentials"}), 401)

    session["username"] = username
    return make_response(jsonify({"status": "success", "message": "Login successful", "redirect": "/dashboard"}), 200)


@admin_bp.route("/logout", methods=["POST"])
def admin_logout_handler():
    """Handle logout - clear session, redirect to /admin"""
    session.pop("username", None)
    return redirect("/admin")
