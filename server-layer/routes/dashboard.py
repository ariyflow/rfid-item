from flask import Blueprint, make_response, jsonify, send_from_directory

dashboard_routes = Blueprint("dashboard", __name__, url_prefix="/dashboard")


@dashboard_routes.route("/")
def default_handler():
    return make_response("dashboard routes success.")