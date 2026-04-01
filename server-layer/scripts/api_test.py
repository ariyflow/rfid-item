import os
import sys
import requests
import time

"""test连通性测试"""
# resp = requests.post("http://127.0.0.1:5353/api/test")
# print(resp.text)
# resp.close()

"""submit_sensor_data测试"""
# data = {
#     "device_seq":"a5642f3ecdb7",
#     "temperature":25.0,
#     "light":143,
#     "hall":1,
#     "timestamp":str(time.time())
# }
# resp = requests.post("http://127.0.0.1:5353/api/submit_sensor_data", json=data)
# print(resp.text)
# resp.close()

"""fetch_sensor_data测试"""
# data = {
#     "start": 0,
#     "num": 2,
#     "device_seq": "a5642f3ecdb7"
# }
# resp = requests.post("http://127.0.0.1:5353/api/fetch_sensor_data", json=data)
# print(resp.text)
# resp.close()

"""remove_sensor_data测试"""
# data = {
#     "id": 1,
#     "device_seq": "a5642f3ecdb7"
# }
# resp = requests.post("http://127.0.0.1:5353/api/remove_sensor_data", json=data)
# print(resp.text)
# resp.close()

"""get_device_list测试"""
# data = {}
# resp = requests.post("http://127.0.0.1:5353/api/get_device_list", json=data)
# print(resp.text)
# resp.close()

"""/api/distribute_seq测试"""
resp = requests.post("http://127.0.0.1:5353/api/distribute_seq")
print(resp.text)
resp.close()