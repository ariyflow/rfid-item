"""Dashboard 用户管理相关"""

from flask import Blueprint, make_response, jsonify, request, session
from model.dbObject import db
from utils.config import get_config

user_management_bp = Blueprint("user_management", __name__)

ROOT_USERNAME = get_config().get("ROOT_USERNAME", "root") if get_config() else "root"

@user_management_bp.before_request
def require_root():
    """所有请求前检查是否为 root 用户"""
    if request.endpoint == "user_management.check_root_handler":
        return None

    username = session.get("username")
    if username != ROOT_USERNAME:
        return make_response(jsonify({"status": "error", "message": "权限不足，仅 root 用户可执行此操作"}), 403)


@user_management_bp.route("/check_root", methods=["GET"])
def check_root_handler():
    """检查当前用户是否为 root"""
    username = session.get("username")
    is_root = username == ROOT_USERNAME
    return make_response(jsonify({"status": "success", "is_root": is_root, "username": username}), 200)


@user_management_bp.route("/get_all_users", methods=["GET"])
def get_all_users_handler():
    """获取所有用户列表"""
    result = db.get_all_auth()
    if result["status"] != "success":
        return make_response(jsonify({"status": "error", "message": result.get("message", "获取用户列表失败")}), 500)

    users = result.get("users", [])
    safe_users = [{"id": u["id"], "username": u["username"], "timestamp": u["timestamp"]} for u in users]

    return make_response(jsonify({"status": "success", "users": safe_users}), 200)


@user_management_bp.route("/add_user", methods=["POST"])
def add_user_handler():
    """添加新用户"""
    data = request.get_json() or {}
    username = data.get("username", "").strip()
    password = data.get("password", "")

    if not username:
        return make_response(jsonify({"status": "error", "message": "用户名不能为空"}), 400)

    if not password:
        return make_response(jsonify({"status": "error", "message": "密码不能为空"}), 400)

    if username == ROOT_USERNAME:
        return make_response(jsonify({"status": "error", "message": "不能创建 root 用户"}), 400)

    result = db.add_auth(username, password)
    if result["status"] != "success":
        return make_response(jsonify({"status": "error", "message": result.get("message", "添加用户失败")}), 400)

    return make_response(jsonify({"status": "success", "message": "用户添加成功"}), 200)


@user_management_bp.route("/update_user", methods=["POST"])
def update_user_handler():
    """更新用户密码"""
    data = request.get_json() or {}
    username = data.get("username", "").strip()
    new_password = data.get("new_password", "")

    if not username:
        return make_response(jsonify({"status": "error", "message": "用户名不能为空"}), 400)

    if not new_password:
        return make_response(jsonify({"status": "error", "message": "新密码不能为空"}), 400)

    if username == ROOT_USERNAME:
        return make_response(jsonify({"status": "error", "message": "不能修改 root 用户密码"}), 400)

    result = db.update_auth(username, new_password)
    if result["status"] != "success":
        return make_response(jsonify({"status": "error", "message": result.get("message", "更新用户失败")}), 400)

    return make_response(jsonify({"status": "success", "message": "用户密码更新成功"}), 200)


@user_management_bp.route("/delete_user", methods=["POST"])
def delete_user_handler():
    """删除用户"""
    data = request.get_json() or {}
    username = data.get("username", "").strip()

    if not username:
        return make_response(jsonify({"status": "error", "message": "用户名不能为空"}), 400)

    if username == ROOT_USERNAME:
        return make_response(jsonify({"status": "error", "message": "不能删除 root 用户"}), 400)

    current_user = session.get("username")
    if username == current_user:
        return make_response(jsonify({"status": "error", "message": "不能删除当前登录用户"}), 400)

    result = db.remove_auth(username)
    if result["status"] != "success":
        return make_response(jsonify({"status": "error", "message": result.get("message", "删除用户失败")}), 400)

    return make_response(jsonify({"status": "success", "message": "用户删除成功"}), 200)
