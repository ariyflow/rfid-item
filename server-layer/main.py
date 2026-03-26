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

    data["rcv_status"] = "ok"
    data["rcv_time"] = str(time.time())

    return make_response(jsonify(data), 200)

if __name__ == "__main__":
    log.info("程序开始运行")
    app.run("127.0.0.1", port=5353, debug=True)

    log.info("程序运行结束")
