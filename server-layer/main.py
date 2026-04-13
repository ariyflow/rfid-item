from flask import Flask, make_response, request, jsonify, send_from_directory
import os
import time
import json
from model import db, log
from routes import sensor_route, database_bp, functional_routes, public_routes, dashboard_routes
from routes.auth import auth_bp
import sys


app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY") or os.urandom(24)

app.register_blueprint(sensor_route) # 传感器数据处理相关
app.register_blueprint(database_bp) # 设备管理相关
app.register_blueprint(functional_routes) # 分配序列号
app.register_blueprint(public_routes) # public界面的相关路由
app.register_blueprint(dashboard_routes) # dashboard界面的相关路由
app.register_blueprint(auth_bp) # 身份认证相关

@app.route("/")
def default_handler():
    return make_response(send_from_directory("./static/html", "index.html"), 200)

@app.route("/dashboard.html")
def dashboard_handler():
    return make_response(send_from_directory("./static/html", "dashboard.html"), 200)

@app.route("/api/test", methods=["GET", "POST"])
def test_connect_handler():
    return make_response("ok", 200)

@app.cli.command("create-admin")
def create_admin():
    """Create an admin user. Usage: flask create-admin <username> <password>"""
    import click
    username = input("Username: ").strip()
    if not username:
        print("Username cannot be empty")
        return
    password = input("Password: ")
    if not password:
        print("Password cannot be empty")
        return

    result = db.add_auth(username, password)
    if result["status"] == "success":
        print(f"Admin user '{username}' created successfully.")
    elif result["status"] == "exist":
        print(f"User '{username}' already exists.")
    else:
        print(f"Failed to create user: {result.get('message')}")

if __name__ == "__main__":
    log.info("程序开始运行")
    app.run("127.0.0.1", port=5353, debug=True)
    db.quit_handler()
    log.info("程序运行结束")
