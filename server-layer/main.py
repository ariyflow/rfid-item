from flask import Flask, make_response, request, jsonify
import time
import json
from model.dbObject import dbObject
from model.logger import myLogger
import sys

app = Flask(__name__)

log = myLogger()
db = dbObject(log)

@app.route("/")
def default_handler():
    return make_response("ok", 200) 

@app.route("/api/test", methods = ["GET", "POST"])
def test_connect_handler():
    return make_response("ok", 200)

@app.route("/api/submit_sensor_data", methods = ["POST"])
def submit_sensor_data_handler():
    data = request.get_json()
    # print(data)

    db.insert_sensor_data(data)

    data["rcv_status"] = "ok"
    data["rcv_time"] = str(time.time())

    return make_response(jsonify(data), 200)

@app.route("/api/remove_sensor_data", methods = ["POST"])
def remove_sensor_data_handler():
    data = request.get_json()

    status = db.remove_sensor_data(data.get("id"))

    data["rcv_status"] = status.get("status")
    data["rcv_time"] = str(time.time())
    return make_response(jsonify(data), 200 if data["rcv_status"] == "success" else 400)

@app.route("/api/fetch_sensor_data", methods = ["POST"])
def fetch_sensor_data_handler():
    data = request.get_json()

    sensor_data_list = db.get_sensor_data(data.get("start"), data.get("num"))
    log.debug(f"main.py 函数[fetch_sensor_data_handler]收到数据：{sensor_data_list}")
    if sensor_data_list:
        return make_response(jsonify(sensor_data_list), 200)
    else:
        return make_response(jsonify({}), 400)

if __name__ == "__main__":
    log.info("程序开始运行")
    app.run("127.0.0.1", port=5353, debug=True)
    db.quit_handler()
    log.info("程序运行结束")
