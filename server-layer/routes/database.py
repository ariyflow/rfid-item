from flask import Blueprint, make_response, jsonify
from model import db

database_bp = Blueprint("database", __file__, url_prefix="/api")

"""获取设备列表"""
@database_bp.route("/get_device_list", methods=["GET", "POST"])
def get_device_list_handler():
    device_list = db.get_device_list()
    return make_response(jsonify(device_list), 200)