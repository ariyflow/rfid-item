import os
import sys
import requests
import time

data = {
    "device_seq":"a5642f3ecdb7",
    "temperature":25.0,
    "light":142,
    "hall":1,
    "timestamp":str(time.time())
}

# print(data)

resp = requests.post("http://127.0.0.1:5353/api/submit_sensor_data", json=data)

print(resp.text)

resp.close()