from PySide6.QtCore import QThread
from threading import Event
from PySide6.QtWidgets import QWidget
import requests
from datetime import datetime
import time

class webModel(QWidget):
    def __init__(self, par):
        super().__init__()
        self.par = par

        self.is_running = Event()
        self.is_running.clear()

    
    def submit_sensor_data(self, device_seq: bytes, temp: float, light: int, hall: int):
        url = "http://127.0.0.1:4343/api/submit-data"

        data = {
            "device_seq": device_seq,
            "temperature": temp,
            "light": light,
            "hall": hall,
            "timestamp": time.time()
        }

        requests.post(url, json = data)



if __name__ == "__main__":
    pass