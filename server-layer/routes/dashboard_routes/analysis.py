"""API 数据分析相关"""

from flask import Blueprint, make_response, jsonify, request
from model.dbObject import SENSOR_TABLE_PREFIX, DATABASE_LOCATION, DATABASE_NAME
import sqlite3
import time

analysis_bp = Blueprint("analysis", __name__, url_prefix="")


@analysis_bp.route("/fetch_analysis_data", methods=["POST"])
def fetch_analysis_data_handler():
    """
    获取用于分析的传感器数据

    Body (JSON):
        device_seq: str, optional - 设备序列号，省略则返回所有设备
        start_time: float, optional - Unix时间戳，默认 24小时前
        end_time: float, optional - Unix时间戳，默认当前时间
        limit: int, optional - 每设备最大记录数，默认1000
    """
    data = request.get_json() or {}

    device_seq = data.get("device_seq")
    limit = int(data.get("limit", 1000))

    now = time.time()
    default_start = now - 24 * 3600
    start_time = float(data.get("start_time", default_start))
    end_time = float(data.get("end_time", now))

    try:
        if device_seq:
            result = _fetch_single_device_data(device_seq, start_time, end_time, limit)
        else:
            result = _fetch_all_devices_data(start_time, end_time, limit)

        return make_response(jsonify(result), 200)
    except Exception as e:
        return make_response(jsonify({"status": "error", "message": str(e)}), 500)


def _fetch_single_device_data(device_seq: str, start_time: float, end_time: float, limit: int):
    """获取单个设备的数据"""
    table_name = f"{SENSOR_TABLE_PREFIX}{device_seq}"

    conn = sqlite3.connect(f"{DATABASE_LOCATION}/{DATABASE_NAME}")
    cur = conn.cursor()

    try:
        cur.execute(
            f"""
            SELECT id, temperature, light, hall, timestamp
            FROM {table_name}
            WHERE CAST(timestamp AS REAL) BETWEEN ? AND ?
            ORDER BY CAST(timestamp AS REAL) ASC
            LIMIT ?
            """,
            (start_time, end_time, limit),
        )
        rows = cur.fetchall()
        cur.close()
        conn.close()

        return {
            "status": "success",
            "data": [_row_to_dict(row, device_seq) for row in rows],
            "device_count": 1,
            "total_records": len(rows),
        }
    except Exception as e:
        cur.close()
        conn.close()
        raise e


def _fetch_all_devices_data(start_time: float, end_time: float, limit: int):
    """获取所有设备的数据"""
    conn = sqlite3.connect(f"{DATABASE_LOCATION}/{DATABASE_NAME}")
    cur = conn.cursor()

    try:
        cur.execute("SELECT device_seq FROM devices")
        devices = [row[0] for row in cur.fetchall()]
        cur.close()
        conn.close()

        all_data = []
        per_device_limit = max(1, limit // max(len(devices), 1))

        for device_seq in devices:
            table_name = f"{SENSOR_TABLE_PREFIX}{device_seq}"
            conn = sqlite3.connect(f"{DATABASE_LOCATION}/{DATABASE_NAME}")
            cur = conn.cursor()

            try:
                cur.execute(
                    f"""
                    SELECT id, temperature, light, hall, timestamp
                    FROM {table_name}
                    WHERE CAST(timestamp AS REAL) BETWEEN ? AND ?
                    ORDER BY CAST(timestamp AS REAL) ASC
                    LIMIT ?
                    """,
                    (start_time, end_time, per_device_limit),
                )
                rows = cur.fetchall()
                all_data.extend([_row_to_dict(row, device_seq) for row in rows])
            except Exception:
                pass
            finally:
                cur.close()
                conn.close()

        all_data.sort(key=lambda x: float(x["timestamp"]))

        return {
            "status": "success",
            "data": all_data,
            "device_count": len(devices),
            "total_records": len(all_data),
        }
    except Exception as e:
        cur.close()
        conn.close()
        raise e


def _row_to_dict(row, device_seq: str):
    """将数据库行转换为字典"""
    return {
        "id": row[0],
        "device_seq": device_seq,
        "temperature": row[1],
        "light": row[2],
        "hall": row[3],
        "timestamp": row[4],
    }
