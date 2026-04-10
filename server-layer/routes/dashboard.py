"""dashboard 相关"""

from flask import Blueprint, make_response, jsonify, send_from_directory
from .settings import *
import os

dashboard_routes = Blueprint("dashboard", __name__, url_prefix="/dashboard")


@dashboard_routes.route("/")
def default_handler():
    return make_response(send_from_directory(os.path.join(ROOT_DIR, STATIC_DIR, "html"), "dashboard.html"), 200)