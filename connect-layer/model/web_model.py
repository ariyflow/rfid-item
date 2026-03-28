from typing import Optional
import time

import requests
from PySide6.QtCore import QObject, QThread, Signal, Slot


class _WebWorker(QObject):
    request_finished = Signal(str)
    request_failed = Signal(str)

    def __init__(self):
        super().__init__()
        self.session: Optional[requests.Session] = None

    @Slot(dict)
    def submit_sensor_data(self, task: dict):
        try:
            if self.session is None:
                self.session = requests.Session()

            url = task.get("url")
            data = task.get("data")
            if not isinstance(url, str) or not isinstance(data, dict):
                self.request_failed.emit("submit_sensor_data task format error")
                return

            resp = self.session.post(url, json=data, timeout=5)
            msg = f"[{resp.status_code}] {resp.text}"
            resp.close()
            self.request_finished.emit(msg)
        except requests.RequestException as e:
            self.request_failed.emit(f"request exception: {e}")
        except Exception as e:
            self.request_failed.emit(f"unexpected exception: {e}")

    @Slot()
    def close_session(self):
        if self.session is not None:
            self.session.close()
            self.session = None


class webModel(QObject):
    submit_sensor_data_signal = Signal(dict)
    close_session_signal = Signal()

    def __init__(self, par):
        super().__init__(par)
        self.par = par

        self.worker_thread = QThread(self)
        self.worker = _WebWorker()
        self.worker.moveToThread(self.worker_thread)

        self.submit_sensor_data_signal.connect(self.worker.submit_sensor_data)
        self.close_session_signal.connect(self.worker.close_session)
        self.worker.request_finished.connect(self._on_submit_success)
        self.worker.request_failed.connect(self._on_submit_failed)
        self.worker_thread.finished.connect(self.worker.deleteLater)

        self.worker_thread.start()

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

        self.submit_sensor_data_signal.emit({"url": url, "data": data})

    @Slot(str)
    def _on_submit_success(self, msg: str):
        self.par.log.info(f"函数[submit_sensor_data]收到应用层响应：{msg}")
        self.par.textUpperLayerLog.appendPlainText(msg + "\n")

    @Slot(str)
    def _on_submit_failed(self, msg: str):
        self.par.log.error(f"函数[submit_sensor_data]请求失败：{msg}")
        self.par.textUpperLayerLog.appendPlainText(f"[ERROR] {msg}\n")

    def quit_web_session(self):
        """关闭 web 会话和工作线程"""
        self.close_session_signal.emit()
        self.worker_thread.quit()
        self.worker_thread.wait(2000)


if __name__ == "__main__":
    pass
