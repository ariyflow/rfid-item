from PySide6.QtCore import QThread, Signal
import serial
from threading import Event

class serialThread(QThread):
    data_received = Signal(bytes)
    def __init__(self, par):
        super().__init__()
        self.par = par
        self.is_running = Event()
        self.is_running.set()
        
        self.serial = serial.Serial()
    
    def _check_sum(self, data: bytes):
        """检查能否通过偶校验"""
        rst = 0
        for b in data:
            rst ^= b
        return 1 if rst == 0 else 0 # 偶校验通过时，所有字节异或为0
    
    def run(self):
        self.par.log.debug("serialThread开始运行")
        head = [0xaa, 0x55] # 数据包头
        data = b""
        while self.is_running.is_set():
            if self.serial and self.serial.is_open:
                try:
                    data = self.serial.read(2) # 窝要验牌
                    if (not data) or (data[0] != head[0] or data[1] != head[1]): # 牌有问题
                        while True:
                            data = self.serial.read(2) # 换牌
                            if data and data[0] == head[0] and data[1] == head[1]: # 没有问题
                                break
                            
                    if data and data[0] == head[0] and data[1] == head[1]: # 牌没有问题
                        num = self.serial.read(1)
                        if num:
                            num = int.from_bytes(num, "big")
                        else:
                            continue
                            
                        content = self.serial.read(num) # 读取实际的数据和校验位
                                
                        content = data+num.to_bytes(1, "big")+content
                        if(self._check_sum(content)):
                            self.par.log.info(f"收到合法数据包：{content.hex()}")
                            self.data_received.emit(content)
                        else:
                            self.par.log.warning(f"收到数据包，但是未通过偶校验：{content.hex()}, 偶校验结果：{self._check_sum(content)}")
                    else:
                        continue
                except serial.SerialException as e:
                    self.par.log.error(f"发生错误：{e}")
                except Exception as e:
                    self.par.log.error(f"发生错误：{e}")
            else:
                self.msleep(100)
            data = b"" # 处理完一次清空缓冲区
        
    
    def open_serial(self, port: str = "COM5", baudrate: int = 9600, timeout: float = 1.0):
        try:
            self.serial.port = port
            self.serial.baudrate = baudrate
            self.serial.timeout = timeout
            self.serial.open()
            self.par.log.info(f"串口打开成功！(port: {port} baudrate: {baudrate} timeout: {timeout:.1f})")
        except Exception as e:
            self.par.log.error(f"串口打开失败:{e}")
    
    def close_serial(self):
        if self.serial and self.serial.is_open:
            self.serial.close()
            self.par.log.info("串口关闭成功！")
        else:
            self.par.log.warning("串口已关闭！")
    
    def send_data(self, data: bytes):
        if self.serial and self.serial.is_open:
            self.serial.write(data)
            self.par.log.debug(f"数据发送成功：{self._to_hex_stream(data)}")
        else:
            self.par.log.warning(f"串口未打开，数据发送失败：{self._to_hex_stream(data)}")
    
    def _to_hex_stream(self, data: bytes) -> str:
        return " ".join(f"{b:02X}" for b in data)