from flask import Blueprint, request, make_response, jsonify
import time
from model.dbObject import db
from model.logger import log

sensor_route = Blueprint("sensor", __name__, url_prefix="/api")

@sensor_route.route("/submit_sensor_data", methods=["POST"])
def submit_sensor_data_handler():
    data = request.get_json()
    # print(data)

    db.insert_sensor_data(data)

    data["rcv_status"] = "ok"
    data["rcv_time"] = str(time.time())

    return make_response(jsonify(data), 200)


@sensor_route.route("/remove_sensor_data", methods=["POST"])
def remove_sensor_data_handler():
    data = request.get_json()

    status = db.remove_sensor_data(data.get("id"))

    data["rcv_status"] = status.get("status")
    data["rcv_time"] = str(time.time())
    return make_response(jsonify(data), 200 if data["rcv_status"] == "success" else 400)


@sensor_route.route("/fetch_sensor_data", methods=["POST"])
def fetch_sensor_data_handler():
    data = request.get_json()

    device_seq = data.get("device_seq")
    sensor_data_list = db.get_sensor_data(
        data.get("start"), data.get("num"), device_seq
    )
    log.debug(f"main.py 函数[fetch_sensor_data_handler]收到数据：{sensor_data_list}")
    if sensor_data_list:
        return make_response(jsonify(sensor_data_list), 200)
    else:
        return make_response(jsonify({}), 400)