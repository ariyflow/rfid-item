"""RFID卡管理 API"""

import re
from flask import Blueprint, make_response, jsonify, request
from model.dbObject import db
from model.logger import log

rfid_card_bp = Blueprint("rfid_card", __name__, url_prefix="/rfid_card")

# 4字节16进制正则以小写无空格形式存储
_UID_PATTERN = re.compile(r"^[0-9a-f]{8}$")

def _normalize_uid(raw: str) -> str | None:
    """清理并验证RFID卡UID。合法的UID是4字节（8字符）十六进制字符串。
    返回规范化后的小写hex，非法时返回None。
    """
    s = raw.strip().replace(" ", "").replace("0x", "").replace("0X", "")
    s = s.lower()
    if _UID_PATTERN.match(s):
        return s
    return None


@rfid_card_bp.route("/get_rfid_cards", methods=["POST"])
def get_rfid_cards_handler():
    """获取所有RFID卡列表"""
    data = request.get_json() or {}
    start = data.get("start", 0)
    num = data.get("num", 100)

    if not isinstance(start, int) or start < 0:
        start = 0
    if not isinstance(num, int) or num <= 0:
        num = 100

    result = db.get_rfid_cards(start, num)
    if result["status"] != "success":
        return make_response(jsonify({"status": "error", "message": result.get("message", "获取RFID卡列表失败")}), 500)

    return make_response(jsonify({"status": "success", "cards": result.get("cards", [])}), 200)


@rfid_card_bp.route("/get_rfid_card", methods=["POST"])
def get_rfid_card_handler():
    """获取单个RFID卡信息"""
    data = request.get_json() or {}
    uid = _normalize_uid(data.get("uid", ""))

    if uid is None:
        return make_response(jsonify({"status": "error", "message": "UID格式错误，需要4字节十六进制（8字符）"}), 400)

    result = db.get_rfid_card(uid)
    if result["status"] == "not_found":
        return make_response(jsonify({"status": "not_found", "message": f"RFID卡 {uid} 不存在"}), 404)
    if result["status"] != "success":
        return make_response(jsonify({"status": "error", "message": result.get("message", "查询失败")}), 500)

    return make_response(jsonify({"status": "success", "card": result.get("card", {})}), 200)


@rfid_card_bp.route("/add_rfid_card", methods=["POST"])
def add_rfid_card_handler():
    """添加RFID卡"""
    data = request.get_json() or {}
    uid = _normalize_uid(data.get("uid", ""))
    balance = float(data.get("balance", 0))

    if uid is None:
        return make_response(jsonify({"status": "error", "message": "UID格式错误，需要4字节十六进制（8字符）"}), 400)

    if balance < 0:
        return make_response(jsonify({"status": "error", "message": "初始余额不能为负数"}), 400)

    result = db.add_rfid_card(uid, balance)
    if result["status"] == "error":
        return make_response(jsonify({"status": "error", "message": result.get("message", "添加失败")}), 400)

    return make_response(jsonify({"status": "success", "message": "RFID卡添加成功"}), 200)


@rfid_card_bp.route("/modify_balance", methods=["POST"])
def modify_balance_handler():
    """修改RFID卡余额
    Body:
        uid: str - RFID卡的UID
        amount: float - 金额
        mode: str - "add"（增减，卡不存在时amount>0则自动创建）或 "set"（直接设置）
    """
    data = request.get_json() or {}
    uid = _normalize_uid(data.get("uid", ""))
    amount = float(data.get("amount", 0))
    mode = data.get("mode", "add")

    if uid is None:
        return make_response(jsonify({"status": "error", "message": "UID格式错误，需要4字节十六进制（8字符）"}), 400)

    if mode not in ("add", "set"):
        return make_response(jsonify({"status": "error", "message": "无效的操作模式"}), 400)

    if mode == "set" and amount < 0:
        return make_response(jsonify({"status": "error", "message": "设置模式余额不能为负数"}), 400)

    log.debug(f"更新RFID信息:{uid, amount, mode}")
    result = db.update_rfid_card_balance(uid, amount, mode)
    if result["status"] == "not_found":
        return make_response(jsonify({"status": "not_found", "message": result.get("message", f"RFID卡 {uid} 不存在")}), 404)
    if result["status"] != "success":
        return make_response(jsonify({"status": "error", "message": result.get("message", "操作失败")}), 500)

    return make_response(jsonify({
        "status": "success",
        "message": result.get("message", "余额更新成功"),
        "balance": result.get("balance")
    }), 200)


@rfid_card_bp.route("/delete_rfid_card", methods=["POST"])
def delete_rfid_card_handler():
    """删除RFID卡"""
    data = request.get_json() or {}
    uid = _normalize_uid(data.get("uid", ""))

    if uid is None:
        return make_response(jsonify({"status": "error", "message": "UID格式错误，需要4字节十六进制（8字符）"}), 400)

    result = db.delete_rfid_card(uid)
    if result["status"] == "not_found":
        return make_response(jsonify({"status": "not_found", "message": f"RFID卡 {uid} 不存在"}), 404)
    if result["status"] != "success":
        return make_response(jsonify({"status": "error", "message": result.get("message", "删除失败")}), 500)

    return make_response(jsonify({"status": "success", "message": "RFID卡删除成功"}), 200)
