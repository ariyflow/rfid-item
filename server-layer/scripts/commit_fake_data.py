import secrets
import random
import time
import requests

random.seed(time.time())

data = {
    "device_seq":"a5642f3ecdb7",
    "temperature":random.randrange(200, 300) / 10,
    "light":random.randrange(0, 300),
    "hall":1 if random.random()>0.5 else 0,
    "timestamp":str(time.time())
}

resp = requests.post("http://127.0.0.1:5353/api/submit_sensor_data", json = data)

print(resp.text)

resp.close()