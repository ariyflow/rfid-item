from flask import Flask, make_response, request, jsonify, send_from_directory
import os
import time
import json
import secrets
from model import db, log
from routes import sensor_route, database_bp, functional_routes, public_routes, dashboard_routes
from routes.admin import admin_bp
import sys

ROOT_USERNAME = "root"

def ensure_root_user():
    """确保 root 用户存在，每次启动时更新其密码为新随机密码"""
    password = secrets.token_hex(16) # 16字节
    result = db.get_auth_pwd(ROOT_USERNAME)
    if result["status"] == "not_found":
        db.add_auth(ROOT_USERNAME, password)
        log.info(f"Root 用户已创建，用户名: {ROOT_USERNAME}, 密码: {password}")
        print(f"\n{'='*60}")
        print(f"Root 用户已创建！")
        print(f"用户名: {ROOT_USERNAME}")
        print(f"密码: {password}")
        print(f"{'='*60}\n")
    else:
        db.update_auth(ROOT_USERNAME, password)
        log.info(f"Root 密码已更新，用户名: {ROOT_USERNAME}, 密码: {password}")
        print(f"\n{'='*60}")
        print(f"Root 密码已更新！")
        print(f"用户名: {ROOT_USERNAME}")
        print(f"密码: {password}")
        print(f"{'='*60}\n")


app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY") or os.urandom(24)

app.register_blueprint(sensor_route) # 传感器数据处理相关
app.register_blueprint(database_bp) # 设备管理相关
app.register_blueprint(functional_routes) # 分配序列号
app.register_blueprint(public_routes) # public界面的相关路由
app.register_blueprint(dashboard_routes) # dashboard界面的相关路由
app.register_blueprint(admin_bp) # admin登录相关

@app.route("/")
def default_handler():
    return make_response(send_from_directory("./static/html", "index.html"), 200)

@app.route("/dashboard.html")
def dashboard_handler():
    return make_response(send_from_directory("./static/html", "dashboard.html"), 200)

@app.route("/api/test", methods=["GET", "POST"])
def test_connect_handler():
    return make_response("ok", 200)

if __name__ == "__main__":
    log.info("程序开始运行")
    ensure_root_user()
    app.run("127.0.0.1", port=5353, debug=True)
    db.quit_handler()
    log.info("程序运行结束")
