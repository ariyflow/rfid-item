import os
import sys
import requests
import time

"""submit_sensor_data测试"""
# data = {
#     "device_seq":"a5642f3ecdb7",
#     "temperature":25.0,
#     "light":144,
#     "hall":1,
#     "timestamp":str(time.time())
# }

# # print(data)

# resp = requests.post("http://127.0.0.1:5353/api/submit_sensor_data", json=data)

# print(resp.text)

# resp.close()

"""fetch_sensor_data测试"""
# 不带 device_seq（原有功能）
# data = {
#     "start": 0,
#     "num": 2
# }
# resp = requests.post("http://127.0.0.1:5353/api/fetch_sensor_data", json=data)
# print(resp.text)
# resp.close()

# 带 device_seq（新功能）
# data = {
#     "start": 0,
#     "num": 2,
#     "device_seq": "a5642f3ecdb7"
# }
# resp = requests.post("http://127.0.0.1:5353/api/fetch_sensor_data", json=data)
# print(resp.text)
# resp.close()

"""remove_sensor_data测试"""

# data = {"id": 1}
# resp = requests.post("http://127.0.0.1:5353/api/remove_sensor_data", json=data)
# print(resp.text)
# resp.close()
