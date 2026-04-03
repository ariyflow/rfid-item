from flask import Blueprint, make_response, jsonify
from model import db
import time
import secrets

functional_routes = Blueprint("functional", __name__, url_prefix="/api")

def generate_device_seq(existing_devices: list) -> str:
    """生成不与现有设备冲突的12位十六进制序列号"""
    max_attempts = 100
    for _ in range(max_attempts):
        new_seq = secrets.token_hex(6)  # 生成12位十六进制字符串
        if new_seq not in existing_devices:
            return new_seq
    raise Exception("无法生成唯一的设备序列号，请稍后重试")

@functional_routes.route("/distribute_seq", methods=["POST"])
def distribute_seq_handler():
    device_list = db.get_device_list()
    try:
        new_seq = generate_device_seq(device_list)
        rsp = {
            "device_seq": new_seq,
            "status": "ok",
            "timestamp": str(time.time())
        }
        return make_response(jsonify(rsp), 200)
    except Exception as e:
        rsp = {
            "status": "error",
            "message": str(e),
            "timestamp": str(time.time())
        }
        return make_response(jsonify(rsp), 500)