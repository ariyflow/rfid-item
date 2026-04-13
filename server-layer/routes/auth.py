"""Authentication routes: login and logout"""

from flask import Blueprint, request, make_response, jsonify, session
import hashlib
from model.dbObject import db

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


@auth_bp.route("/login", methods=["POST"])
def login_handler():
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
    return make_response(jsonify({"status": "success", "message": "Login successful"}), 200)


@auth_bp.route("/logout", methods=["POST"])
def logout_handler():
    session.pop("username", None)
    return make_response(jsonify({"status": "success", "message": "Logged out"}), 200)


@auth_bp.route("/check", methods=["GET"])
def check_auth_handler():
    """Check if the current session is authenticated."""
    username = session.get("username")
    if username:
        return make_response(jsonify({"status": "authenticated", "username": username}), 200)
    return make_response(jsonify({"status": "unauthenticated"}), 401)
