"""API 数据库相关"""

from flask import Blueprint, make_response, jsonify, request
from model import db

database_bp = Blueprint("database", __file__, url_prefix="/api")

"""获取设备列表"""
@database_bp.route("/get_device_list", methods=["GET", "POST"])
def get_device_list_handler():
    device_list = db.get_device_list()
    return make_response(jsonify(device_list), 200)

@database_bp.route("/add_device", methods = ["POST"])
def add_device_handler():
    data = request.get_json() or request.form
    seq = data.get("device_seq")
    timestamp = data.get("timestamp")
    
    if not seq:
        return make_response(jsonify({"status": "error", "message": "缺少设备序列号参数"}), 400)
    
    result = db.add_device(seq, timestamp)
    
    if result["status"] == "success":
        return make_response(jsonify(result), 200)
    elif result["status"] == "exist":
        return make_response(jsonify(result), 409)  # Conflict
    else:
        return make_response(jsonify(result), 500)

@database_bp.route("/remove_device", methods = ["POST"])
def remove_device_handler():
    data = request.get_json() or request.form
    seq = data.get("device_seq")
    
    if not seq:
        return make_response(jsonify({"status": "error", "message": "缺少设备序列号参数"}), 400)
    
    result = db.remove_device(seq)
    
    if result["status"] == "success":
        return make_response(jsonify(result), 200)
    elif result["status"] == "not_found":
        return make_response(jsonify(result), 404)
    else:
        return make_response(jsonify(result), 500)