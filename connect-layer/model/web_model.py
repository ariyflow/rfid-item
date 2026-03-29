from typing import Optional
import time
from queue import Queue
import requests
from PySide6.QtCore import QObject, QThread, Signal, Slot
from threading import Event

QUEUE_MAXSIZE = 50 # 请求队列的最大长度
REQUESTS_TIMEOUT = 5 # 请求等待的最长时间
QUEUE_TIMEOUT = 1.0 # 请求队列每次轮询等待的时间

class webThread(QThread):
    resp_signal = Signal(dict) # 收到某个请求响应的信号，返回给webModel
    def __init__(self, par):
        super().__init__()

        self.par = par # par为webModel

        self._is_running = Event()
        self._is_running.set()

        self.session = requests.Session()
        self.requests_queue: Queue = Queue(maxsize=QUEUE_MAXSIZE)
    
    def run(self):
        while self._is_running.is_set():
            try:
                url, method, data = self.requests_queue.get(timeout=QUEUE_TIMEOUT)
                self._do_requests(url, method, data)
            except:
                continue

    def _do_requests(self, url: str, method: str, data: dict | None):
        """执行请求的函数"""
        method = method.upper()
        try:
            if method == "GET":
                resp = self.session.get(url, timeout=REQUESTS_TIMEOUT)
                data = {
                    "status": resp.status_code,
                    "url": resp.url,
                    "resp": resp.text
                }
                self.resp_signal.emit(data)
                
            elif method == "POST":
                resp = self.session.post(url, json=data, timeout=REQUESTS_TIMEOUT)
                data = {
                    "status": resp.status_code,
                    "url": resp.url,
                    "resp": resp.text
                }
                self.resp_signal.emit(data)

        except Exception as e:
            self.par.par.log.error(f"运行函数[_do_requests]错误：{e}")

    def add_request(self, url: str, method: str, data: dict = None):
        if not self.requests_queue.full():
            self.requests_queue.put((url, method, data))
        else:
            self.par.par.log.warning(f"运行函数[add_request]错误：请求队列已满，新增请求失败：{(url, method, data)}")
    
    def quit_handler(self):
        if self.session is not None:
            self.session.close()
            self.session = None

        if self._is_running.is_set():
            self._is_running.clear()
            self.quit()
            self.wait()


class webModel(QObject):
    resp_submit = Signal(dict) # 向SerialToolWindow返回响应的信号
    def __init__(self, par):
        super().__init__()
        self.par = par # par需要为SerialToolWindow

        self.webt = webThread(self)
        self.webt.start()

        self.webt.resp_signal.connect(self.resp_parse)
    
    def submit_sensor_data(self, device_seq: bytes, temp: float, light: int, hall: int):
        """提交传感器数据"""
        url = f"{self.par.base_url}/api/submit_sensor_data"

        data = {
            "device_seq": device_seq.hex(),
            "temperature": temp,
            "light": light,
            "hall": hall,
            "timestamp": str(time.time()),
        }

        self.webt.add_request(url, "POST", data)

    def get_device_list(self):
        """获取设备列表"""
        url = f"{self.par.base_url}/api/get_device_list"
        self.webt.add_request(url, "GET")

    def resp_parse(self, data: dict):
        """发送的请求得到响应后做处理"""
        self.par.log.debug(f"获取到应用层响应：{data.get('status')}")

        if data.get("url").endswith("get_device_list"):
            # self.par.log.debug(f"获取到设备列表：{data.get('resp')}")
            self.resp_submit.emit(data)

    def quit_web_session(self):
        self.webt.quit_handler()