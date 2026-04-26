"""刷卡记录 API"""

from flask import Blueprint, make_response, jsonify, request
from model.dbObject import db
import time

card_swipe_bp = Blueprint("card_swipe", __name__, url_prefix="/card_swipe")


@card_swipe_bp.route("/submit_card_swipe", methods=["POST"])
def submit_card_swipe_handler():
    """提交刷卡记录"""
    data = request.get_json() or {}
    device_seq = data.get("device_seq", "").strip()
    rfid_serial = data.get("rfid_serial", "").strip()
    timestamp = str(time.time())

    if not device_seq:
        return make_response(jsonify({"status": "error", "message": "设备序列号不能为空"}), 400)

    if not rfid_serial:
        return make_response(jsonify({"status": "error", "message": "RFID序列号不能为空"}), 400)

    result = db.insert_card_swipe(device_seq, rfid_serial, timestamp)
    if result["status"] != "success":
        return make_response(jsonify({"status": "error", "message": result.get("message", "提交失败")}), 500)

    return make_response(jsonify({"status": "success", "message": "刷卡记录保存成功"}), 200)


@card_swipe_bp.route("/fetch_card_swipe", methods=["POST"])
def fetch_card_swipe_handler():
    """查询刷卡记录"""
    data = request.get_json() or {}
    device_seq = data.get("device_seq", "").strip() or None
    start = data.get("start", 0)
    num = data.get("num", 20)

    if not isinstance(start, int) or start < 0:
        start = 0
    if not isinstance(num, int) or num <= 0:
        num = 20

    result = db.get_card_swipes(start, num, device_seq)
    if result["status"] != "success":
        return make_response(jsonify({"status": "error", "message": result.get("message", "查询失败")}), 500)

    return make_response(jsonify({"status": "success", "swipes": result.get("swipes", [])}), 200)
