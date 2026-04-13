from flask import Flask, make_response, request, jsonify, send_from_directory
import time
import json
from model import db, log
from routes import sensor_route, database_bp, functional_routes, public_routes, dashboard_routes
import sys


app = Flask(__name__)

app.register_blueprint(sensor_route)
app.register_blueprint(database_bp)
app.register_blueprint(functional_routes)
app.register_blueprint(public_routes)
app.register_blueprint(dashboard_routes)

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
    app.run("127.0.0.1", port=5353, debug=True)
    db.quit_handler()
    log.info("程序运行结束")
