import sys
import os
import serial
import serial.tools.list_ports
import html
import re
from datetime import datetime
from enum import Enum
from typing import Optional
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QMessageBox, QFileDialog,
    QLabel, QPushButton, QComboBox, QDoubleSpinBox,
    QPlainTextEdit, QLineEdit, QCheckBox, QFrame,
    QTabWidget
)
from PySide6.QtCore import QThread, Signal, QObject, Qt, QFile
from PySide6.QtGui import QFont
from PySide6 import QtUiTools
import logging as lg
from model.serialThread import serialThread
from model.web_model import webModel
import os
import random
import time
import json
import math

# 常量定义

BASE_URL = "http://127.0.0.1:5353" # 服务器的url
TOKEN = "" # 向服务器发送数据所需的token

# 安全常量
MAX_LOG_HISTORY = 10000  # 最大日志历史条数
MAX_DISPLAY_BYTES = 1048576  # 单次最大显示字节数 (1MB)
MAX_SEND_BYTES = 65536  # 单次最大发送字节数 (64KB)
ALLOWED_LOG_EXTENSIONS = {'.txt', '.log', '.md'}  # 允许的日志导出扩展名

# 主窗口
class SerialToolWindow(QMainWindow):
    """主窗口类"""
    
    def __init__(self, par: QApplication):
        super().__init__()

        self.bytes_sent = 0
        self.bytes_received = 0
        self._is_connected = False

        # 检查日志文件夹是否存在
        self.check_dir_exists()

        today = datetime.now().strftime("%Y_%m_%d")
        lg.basicConfig(
            format="%(asctime)s - %(levelname)s - %(message)s",
            filename=f"./log/{today}.log",
            filemode="a",
            encoding="utf-8"
        )
        
        self.log = lg.getLogger(__name__)
        self.log.setLevel(lg.DEBUG)
        
        self.log.debug("程序开始运行")

        # 加载 UI 文件
        self._load_ui()
        
        # 初始化
        self._init_ui_values()
        self._connect_signals()

        self.par = par
        self.par.aboutToQuit.connect(self.quit_handler)

        # 全局变量声明
        self.device_seq = b"" # 连接串口后，获取的设备序列号
        self.token = TOKEN
        self.base_url = BASE_URL
        # self._is_need_update_device_seq = False # 标志是否需要进行从机序列号的更新
        
        # 模块声明
        self.serialt = serialThread(self)
        self.serialt.data_received.connect(self._on_data_received)
        self.serialt.start()

        self.web = webModel(self)
        self.web.resp_submit.connect(self._web_resp_parse)
    
    def quit_handler(self):
        if hasattr(self, "web"):
            self.web.quit_web_session()

        if self.serialt.is_running:
            if self.serialt.serial and self.serialt.serial.is_open:
                self.serialt.close_serial()
                
            self.serialt.is_running.clear()
            self.serialt.quit()
            self.serialt.wait()
    
    def check_dir_exists(self):
        """检查必须的文件目录是否存在

        """
        if not os.path.exists("./log"):
            os.mkdir("./log")
            # self.log.warning("检测到目录\"./log\"不存在，已创建目录")

        if not os.path.exists("./log/app.log"):
            open("./log/app.log", "w").close()

    def _load_ui(self):
        """从 UI 文件加载界面"""
        # 获取 UI 文件路径（相对于脚本位置）
        script_dir = os.path.dirname(os.path.abspath(__file__))
        ui_path = os.path.join(script_dir, "test.ui")
        
        # 安全验证：检查 UI 文件是否存在且路径合法
        if not os.path.exists(ui_path):
            QMessageBox.critical(self, "错误", f"UI 文件不存在：{ui_path}")
            sys.exit(1)
        
        # 安全验证：检查路径是否在预期目录内（防止路径遍历）
        real_path = os.path.realpath(ui_path)
        if not real_path.startswith(script_dir):
            QMessageBox.critical(self, "错误", "UI 文件路径不安全")
            sys.exit(1)
        
        # 加载 UI
        loader = QtUiTools.QUiLoader()
        # loader.setWorkingDirectory(script_dir)
        ui_window = loader.load(QFile(ui_path))
        
        if not ui_window:
            QMessageBox.critical(self, "错误", "无法加载 UI 文件")
            sys.exit(1)
        
        # 将 UI 控件绑定到当前窗口
        self.setCentralWidget(ui_window)
        self.setWindowTitle("test app")
        self.setGeometry(200, 100, 960, 720)
        
        # 绑定所有 UI 控件引用
        self.comboPort: QComboBox = ui_window.findChild(QComboBox, "comboPort") # type: ignore
        self.btnRefresh: QPushButton = ui_window.findChild(QPushButton, "btnRefresh") # type: ignore
        self.comboBaudrate: QComboBox = ui_window.findChild(QComboBox, "comboBaudrate") # type: ignore
        self.spinTimeout: QDoubleSpinBox = ui_window.findChild(QDoubleSpinBox, "spinTimeout") # type: ignore
        self.btnConnect: QPushButton = ui_window.findChild(QPushButton, "btnConnect") # type: ignore
        self.labelConnectionStatus: QLabel = ui_window.findChild(QLabel, "labelConnectionStatus") # type: ignore
        
        self.tabData: QTabWidget = ui_window.findChild(QTabWidget, "tabData") # type: ignore
        self.checkHexReceive: QCheckBox = ui_window.findChild(QCheckBox, "checkHexReceive") # type: ignore
        self.btnClearRx: QPushButton = ui_window.findChild(QPushButton, "btnClearRx") # type: ignore
        self.textReceive: QPlainTextEdit = ui_window.findChild(QPlainTextEdit, "textReceive") # type: ignore
        
        self.checkHexSend: QCheckBox = ui_window.findChild(QCheckBox, "checkHexSend") # type: ignore
        self.btnClearTx: QPushButton = ui_window.findChild(QPushButton, "btnClearTx") # type: ignore
        self.textSend: QPlainTextEdit = ui_window.findChild(QPlainTextEdit, "textSend") # type: ignore
        self.lineEditSend: QLineEdit = ui_window.findChild(QLineEdit, "lineEditSend") # type: ignore
        self.btnSend: QPushButton = ui_window.findChild(QPushButton, "btnSend") # type: ignore
        
        self.comboLogLevel: QComboBox = ui_window.findChild(QComboBox, "comboLogLevel") # type: ignore
        self.btnClearLog: QPushButton = ui_window.findChild(QPushButton, "btnClearLog") # type: ignore
        self.btnExportLog: QPushButton = ui_window.findChild(QPushButton, "btnExportLog") # type: ignore
        self.textLog: QPlainTextEdit = ui_window.findChild(QPlainTextEdit, "textLog") # type: ignore
        
        # self.labelStats: QLabel = ui_window.findChild(QLabel, "labelStats") # type: ignore
        # self.frameStatus: QFrame = ui_window.findChild(QFrame, "frameStatus") # type: ignore

        """感知层通信组件"""
        # RFID操作
        self.get_uid_btn: QPushButton = ui_window.findChild(QPushButton, "get_uid_btn") # type: ignore
        self.read_data_btn: QPushButton = ui_window.findChild(QPushButton, "read_data_btn") # type: ignore
        self.write_data_btn: QPushButton = ui_window.findChild(QPushButton, "write_data_btn") # type: ignore
        self.fetch_sensor_btn: QPushButton = ui_window.findChild(QPushButton, "fetch_sensor_btn") # type: ignore

        # self.input_data_text: QPlainTextEdit = ui_window.findChild(QPlainTextEdit, "input_data_text") # type: ignore
        self.address_intput_edit: QLineEdit = ui_window.findChild(QLineEdit, "address_intput_edit") # type: ignore
        self.data_input_edit: QLineEdit = ui_window.findChild(QLineEdit, "data_input_edit") # type: ignore
        
        # 从机操作
        self.stcope_input_edit: QLineEdit = ui_window.findChild(QLineEdit, "stcope_input_edit") # type:ignore
        self.stcope_setseq_btn: QPushButton = ui_window.findChild(QPushButton, "stcope_setseq_btn") # type: ignore
        self.stcope_getseq_btn: QPushButton = ui_window.findChild(QPushButton, "stcope_getseq_btn") # type: ignore
        self.get_device_list_btn: QPushButton = ui_window.findChild(QPushButton, "get_device_list_btn") # type: ignore | 获取设备列表
        
        # 输出区
        self.output_data_text: QPlainTextEdit = ui_window.findChild(QPlainTextEdit, "output_data_text") # type: ignore

        
        """上层通信"""
        self.lineEditServerUrl: QLineEdit = ui_window.findChild(QLineEdit, "lineEditServerUrl") # type: ignore | 服务器地址
        self.lineEditApiToken: QLineEdit = ui_window.findChild(QLineEdit, "lineEditApiToken") # type: ignore | api token
        self.textUpperLayerLog: QPlainTextEdit = ui_window.findChild(QPlainTextEdit, "textUpperLayerLog") # type: ignore | 上层日志

        # print(
        #     self.stcope_setseq_btn,
        #     self.stcope_input_edit,
        # sep = "\n")

    def _init_ui_values(self):
        """初始化 UI 值"""
        # 波特率选项
        baudrates = [300, 1200, 2400, 4800, 9600, 14400, 19200, 
                     38400, 57600, 115200, 230400, 460800, 921600]
        self.comboBaudrate.addItems([str(b) for b in baudrates])
        self.comboBaudrate.setCurrentText("9600")

        
        # 刷新串口列表
        self._refresh_ports()

        self.lineEditServerUrl.setText(BASE_URL)
        self.lineEditApiToken.setText(TOKEN)
        


    def _connect_signals(self):
        """连接所有信号"""
        
        # 按钮信号
        self.btnRefresh.clicked.connect(self._refresh_ports)
        self.btnConnect.clicked.connect(self._toggle_connection)
        self.btnSend.clicked.connect(self._send_data)
        
        # Enter 键发送
        self.lineEditSend.returnPressed.connect(self._send_data)

        """感知层通信按键"""
        # RFID
        self.get_uid_btn.clicked.connect(self._get_uid_handler)
        self.read_data_btn.clicked.connect(self._read_data_handler)
        self.write_data_btn.clicked.connect(self._write_data_handler)
        self.fetch_sensor_btn.clicked.connect(self._fetch_sensor_handler)
        
        # 从机
        self.stcope_setseq_btn.clicked.connect(self._setseq_handler)
        self.stcope_getseq_btn.clicked.connect(self._send_fetch_device_seq_handler)
        self.get_device_list_btn.clicked.connect(self._get_device_list_handler)

    def _get_uid_handler(self):
        """获取RFID的uid"""
        tmp = b"\xaa\x55\x00"+b"\x00"*20
        con = 0
        for b in tmp:
            con ^= b
        tmp+=con.to_bytes(1, "big")

        self.serialt.send_data(tmp)

    def _read_data_handler(self):
        """读取RFID的某个地址的数据"""
        addr = bytes.fromhex(self.address_intput_edit.text().strip())
        if len(addr) != 1:
            self.log.error(f"地址长度错误：{addr.hex() if addr else None}")
            QMessageBox.warning(None, "提示", f"输入地址要求1个字节，当前有{len(addr)}个。")
            return
        tmp = b"\xaa\x55\x01"+addr+b"\x00"*19
        con = 0
        for b in tmp:
            con ^= b
        tmp+=con.to_bytes(1, "big")

        self.serialt.send_data(tmp)

    def _write_data_handler(self):
        """向RFID某个地址写入数据"""
        content = bytes.fromhex(self.address_intput_edit.text().strip())+bytes.fromhex(self.data_input_edit.text().replace(" ", "").replace(",", "").strip())
        if len(content) != 17:
            self.log.error(f"地址+数据长度错误：{content.hex()}")
            QMessageBox.warning(None, "提示", f"输入地址要求17个字节，当前有{len(content)}个。")
            return
            
        tmp = b"\xaa\x55\x02"+content+b"\x00"*3
        con = 0
        for b in tmp:
            con ^= b

        tmp+=con.to_bytes(1, "big")
        self.serialt.send_data(tmp)

    def _fetch_sensor_handler(self):
        """获取传感器的数据"""
        tmp = b"\xaa\x55\x03"+b"\x00"*20
        con = 0
        for b in tmp:
            con ^= b
        tmp += con.to_bytes(1, "big")
        self.serialt.send_data(tmp)

    def adcToTem(self, tem: int):
        """温度模数转换"""
        try:
            vccx = tem/1000
            lnx = math.log(vccx/(1-vccx))
            t = 1/((lnx/3950)+(1/298.15)) - 273.15
            return round(t, 1)
        except:
            return 25.0
        
    def _get_check_sum(self, data: bytes) -> bytes:
        """
        功能函数，获取一个字符串的偶校验码（8bit）
        Args:
            data: 要生成偶校验码的字符串
        Returns:
            rst: bytes类型，偶校验值
        Example:
            >>> self._get_check_sum(b"ABC")
            
        """
        try:
            rst = 0
            for b in data:
                rst ^= b
        except Exception as e:
            self.log.error(f"运行函数[_get_check_sum]出错：{e}")
            return b""
            
        return int.to_bytes(rst, 1, "big")

    def _show_btyes_with_space(self, data: bytes) -> str:
        """获取一个btyes的字符串，以空格分开每个字符

        Args:
            data (bytes): 原始字符串

        Returns:
            str: 返回的格式字符串
            
        Example:
            >>> rst = self._show_btyes_with_space(b"ADC")
        """
        return " ".join(f"{b:02X}" for b in data)
        
    def _setseq_handler(self):
        """设置从机的序列号"""
        try:
            msg = self.stcope_input_edit.text().replace(" ", "").replace(",", "").replace("，", "").strip()
            msg = bytes.fromhex(msg)
            msg = b"\xaa\x55\x04"+msg+b"\x00"*14
            
            msg = msg+self._get_check_sum(msg)
            self.log.debug(f"发送设置从机序列号的数据帧：{self._show_btyes_with_space(msg)}")
            
            self.serialt.send_data(msg)
        except Exception as e:
            self.log.error(f"执行 _setseq_handler 发生错误：{e}")

    def _send_fetch_device_seq_handler(self):
        """
        发送获取设备序列号的数据帧
        该函数要求在串口打开后调用

        """
        tmp = b"\xaa\x55\x05"+b"\x00"*20
        tmp = tmp+self._get_check_sum(tmp)
        self.serialt.send_data(tmp)
        self.log.debug(f"运行函数：[_send_fetch_device_seq_handler]尝试获取从机序列号")

    def submit_sensor_data_handler(self, data: dict):
        """
        向应用层发送传感器数据，包含设备序列号和时间戳
        Args:
            data: 传入的传感器数据，需要包含temperature, light, hall
        """
        
        if any(data.get(k) is None for k in ("temperature", "light", "hall")):
            self.log.error(f"函数[submit_sensor_data_handler]运行错误：参数不全。传入参数：{data}")
            return

        self.web.submit_sensor_data(self.device_seq, data.get("temperature"), data.get("light"), data.get("hall")) # type: ignore
    
    def _get_device_list_handler(self):
        """获取设备列表"""
        self.web.get_device_list()

    # 日志输出方法
    def _append_log(self, timestamp: str, level: str, message: str):
        """追加日志到显示区"""
        # 安全：对消息进行 HTML 转义，防止注入
        safe_message = html.escape(message)
        log_text = f"[{timestamp}] [{level}] {safe_message}\n"
        
        colors = {
            "DEBUG": "#6a9955",
            "INFO": "#569cd6",
            "WARNING": "#dcdcaa",
            "ERROR": "#f48771",
            "CRITICAL": "#c586c0"
        }
        color = colors.get(level, "#c9d1d9")
        
        self.textLog.appendHtml(f'<span style="color: {color}">{log_text}</span>')
        scrollbar = self.textLog.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
        # print("add log success.")
    
    def _clear_log(self):
        """清空日志 功能弃用"""
        pass
    
    def _export_log(self):
        """导出日志到文件 功能弃用"""
        return
        file_path, _ = QFileDialog.getSaveFileName(
            self, "导出日志", "", "Text Files (*.txt);;Log Files (*.log);;All Files (*)"
        )
        if file_path:
            # 安全验证：检查文件扩展名
            _, ext = os.path.splitext(file_path)
            if ext.lower() not in ALLOWED_LOG_EXTENSIONS and ext.lower() != '':
                # 允许无扩展名，但不允许危险扩展名
                dangerous_exts = {'.exe', '.bat', '.cmd', '.sh', '.py', '.js', '.vbs'}
                if ext.lower() in dangerous_exts:
                    self.logger.error(f"不允许的文件扩展名：{ext}")
                    QMessageBox.warning(self, "警告", f"不允许导出为该文件类型：{ext}")
                    return
            
            # 安全验证：检查路径是否在安全目录内
            try:
                real_path = os.path.realpath(file_path)
                home_dir = os.path.expanduser("~")
                # 允许写入用户目录
                if not real_path.startswith(home_dir):
                    self.logger.warning(f"尝试写入非用户目录：{real_path}")
                    reply = QMessageBox.question(
                        self, "警告",
                        f"文件将保存到系统目录:\n{real_path}\n\n是否继续？",
                        QMessageBox.Yes | QMessageBox.No
                    )
                    if reply != QMessageBox.Yes:
                        return
            except Exception as e:
                self.logger.error(f"路径验证失败：{str(e)}")
                QMessageBox.critical(self, "错误", "文件路径验证失败")
                return
            
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write('\n'.join(self.logger.get_history()))
                self.logger.info(f"日志已导出到：{os.path.basename(file_path)}")
                QMessageBox.information(self, "成功", f"日志已导出到:\n{file_path}")
            except PermissionError:
                self.logger.error(f"导出日志失败：权限不足")
                QMessageBox.critical(self, "错误", "保存失败：权限不足")
            except Exception as e:
                self.logger.error(f"导出日志失败：{str(e)}")
                QMessageBox.critical(self, "错误", f"导出失败:\n{str(e)}")
    
    def _on_log_level_changed(self, level: str):
        """日志级别改变 功能弃用"""
        return
        log_level = LogLevel(level)
        self.logger.set_level(log_level)
        self.logger.info(f"日志级别已设置为：{level}")
    
    # 串口控制方法
    def _refresh_ports(self):
        """刷新串口列表"""
        current = self.comboPort.currentData()
        self.comboPort.clear()
        
        ports = serial.tools.list_ports.comports()
        ports = [p for p in ports if "USB" in p.hwid]
        for port in sorted(ports, key=lambda p: p.device):
            # 安全：清理端口描述中的特殊字符
            safe_desc = html.escape(str(port.description))
            display = f"{port.device} - {safe_desc}"
            self.comboPort.addItem(display, port.device)
        
        if self.comboPort.count() == 0:
            self.comboPort.addItem("未找到串口", "")
            self.log.warning("未找到可用串口")
        else:
            index = self.comboPort.findData(current)
            if index >= 0:
                self.comboPort.setCurrentIndex(index)
            self.log.info(f"找到 {self.comboPort.count()} 个串口")
    
    def _toggle_connection(self):
        """切换串口连接状态"""
        if self._is_connected:
            self._disconnect()
        else:
            self._connect()
    
    def _connect(self):
        """连接串口"""
        port = self.comboPort.currentData()
        if not port:
            QMessageBox.warning(self, "警告", "请选择有效的串口端口")
            return
        
        # 检查是否选择了有效端口
        if self.comboPort.currentText() == "未找到串口":
            QMessageBox.warning(self, "警告", "未找到可用串口，请检查设备连接")
            return
        
        baudrate = int(self.comboBaudrate.currentText())
        timeout = self.spinTimeout.value()
        
        self.log.info(f"正在连接串口：{port} @ {baudrate}")
        self.serialt.open_serial(port, baudrate, timeout)
        if self.serialt.serial.is_open:
            self._on_connection_changed(True)
            self._send_fetch_device_seq_handler()
            
    
    def _disconnect(self):
        """断开串口连接"""
        self.log.info("正在断开串口连接")
        self.serialt.close_serial()
        if not self.serialt.serial.is_open:
            self._on_connection_changed(False)
    
    def _on_connection_changed(self, connected: bool):
        """连接状态改变"""
        self._is_connected = connected
        
        if connected:
            self.btnConnect.setText("关闭串口")
            self.btnConnect.setStyleSheet(
                "QPushButton { background-color: #e74c3c; color: white; "
                "font-weight: bold; padding: 8px; }"
            )
            self.labelConnectionStatus.setText("已连接")
            self.labelConnectionStatus.setStyleSheet("color: green; font-weight: bold;")
            self._enable_controls(True)
            port = self.comboPort.currentText()
            self.log.info(f"串口已连接：{port}")
        else:
            self.btnConnect.setText("打开串口")
            self.btnConnect.setStyleSheet(
                "QPushButton { font-weight: bold; padding: 8px; }"
            )
            self.labelConnectionStatus.setText("未连接")
            self.labelConnectionStatus.setStyleSheet("color: red; font-weight: bold;")
            self._enable_controls(False)
            self.log.info("串口已断开")
    
    def _enable_controls(self, enabled: bool):
        """启用/禁用控件"""
        self.comboPort.setEnabled(not enabled)
        self.comboBaudrate.setEnabled(not enabled)
        self.spinTimeout.setEnabled(not enabled)
        self.btnRefresh.setEnabled(not enabled)
        self.btnSend.setEnabled(enabled)
        self.lineEditSend.setEnabled(enabled)
    
    def _on_error(self, error: str):
        """错误处理"""
        self.log.error(error)
        QMessageBox.critical(self, "错误", error)
        # 发生错误时重置连接状态
        self._is_connected = False
        self.btnConnect.setText("打开串口")
        self.btnConnect.setStyleSheet("QPushButton { font-weight: bold; padding: 8px; }")
        self.labelConnectionStatus.setText("未连接")
        self.labelConnectionStatus.setStyleSheet("color: red; font-weight: bold;")
        self._enable_controls(False)
    
    # 数据收发方法
    def _send_data(self):
        """发送数据"""
        data_text = self.lineEditSend.text()
        if not data_text:
            self.log.warning("发送数据为空")
            return
        
        if not self._is_connected:
            self.log.error("串口未连接，无法发送数据")
            QMessageBox.warning(self, "警告", "请先打开串口")
            return
        
        hex_mode = self.checkHexSend.isChecked()
        
        try:
            if hex_mode:
                # HEX 模式发送 - 清理空格和逗号
                clean_hex = data_text.replace(' ', '').replace(',', '').upper()
                # 验证 HEX 格式
                if len(clean_hex) % 2 != 0:
                    self.log.error(f"HEX 格式错误：长度为奇数")
                    QMessageBox.warning(self, "警告", "HEX 数据长度必须为偶数")
                    return
                if not all(c in '0123456789ABCDEF' for c in clean_hex):
                    self.log.error(f"HEX 格式错误：包含非法字符")
                    QMessageBox.warning(self, "警告", "HEX 数据只能包含 0-9, A-F")
                    return
                data = bytes.fromhex(clean_hex)
            else:
                data = data_text.encode('utf-8')
            
            # 安全限制：检查数据大小
            if len(data) > MAX_SEND_BYTES:
                self.log.error(f"发送数据过大：{len(data)} 字节 (最大 {MAX_SEND_BYTES})")
                QMessageBox.warning(
                    self, "警告",
                    f"发送数据过大:\n{len(data)} 字节\n最大允许：{MAX_SEND_BYTES} 字节"
                )
                return
            
            if self.serialt.send_data(data):
                self.bytes_sent += len(data)
                # self._update_stats()
                
                # 显示到发送历史
                if hex_mode:
                    hex_str = ' '.join(f'{b:02X}' for b in data)
                    self.textSend.appendPlainText(f">>> {hex_str}")
                else:
                    self.textSend.appendPlainText(f">>> {data_text}")
                
                self.lineEditSend.clear()
            else:
                self.log.error("发送失败：串口未连接")
        except ValueError as e:
            self.log.error(f"HEX 转换错误：{str(e)}")
            QMessageBox.warning(self, "警告", f"HEX 格式错误:\n{str(e)}")
        except Exception as e:
            self.log.error(f"发送数据错误：{str(e)}")
            QMessageBox.critical(self, "错误", f"发送失败:\n{str(e)}")
    
    def _on_data_received(self, data: bytes):
        """接收数据回调"""
        if data:
            self.bytes_received += len(data)
            # self._update_stats()
            
            hex_mode = self.checkHexReceive.isChecked() # type: ignore
            
            # 显示到接收区
            if hex_mode:
                hex_str = ' '.join(f'{b:02X}' for b in data)
                self.textReceive.appendPlainText(f"<<< {hex_str}") # type: ignore
            else:
                try:
                    text = data.decode('utf-8', errors='replace')
                    self.textReceive.appendPlainText(f"<<< {text}") # type: ignore
                except:
                    self.textReceive.appendPlainText(f"<<< {data}") # type: ignore
            
            command = data[3]
            if command == 0x00: # 单片机返回RFID的uid
                # aa 55 06 00 d1 d2 d3 d4 xx
                uid = data[4:8]
                uid = " ".join(f"{b:02X}" for b in uid)
                self.output_data_text.appendPlainText(f"return uid: {uid}") # type: ignore
                
            elif command == 0x01: # 返回读取到的数据
                # aa 55 13 01 addr d1-d16 xx
                addr = data[4]
                cont = data[5:-1]
                cont = " ".join(f"{b:02X}" for b in cont)
                self.output_data_text.appendPlainText(f"read address: {addr:02X}; return data: {cont}") # type: ignore
            elif command == 0x02: # 返回写入的状态
                # 成功：aa 55 19 02 01 d1-d16 xx
                # 失败：aa 55 03 02 00 xx
                sig = data[4]
                if sig == 0:
                    self.output_data_text.appendPlainText(f"write data failed!") # type: ignore
                else:
                    self.output_data_text.appendPlainText(f"write data success!") # type: ignore
            elif command == 0x03: # 返回传感器数据
                # aa 55 08 03 t1 t0 i1 i0 hall shake xx
                temperture = int.from_bytes(data[4:6], byteorder="big")
                temperture = self.adcToTem(temperture)
                light = int.from_bytes(data[6:8], byteorder="big")
                hall = data[8]
                shake = data[9]
                
                if self.device_seq == b"\x00"*6: # 如果当前没有序列号，本次数据丢弃，先要求感知层提供序列号
                    self._send_fetch_device_seq_handler() # 调用获取设备序列号的函数
                else:

                    # self.check_device_seq(self.device_seq) # 获取到传感器数据，准备上报时，检查设备序列号
                    
                    self.submit_sensor_data_handler({
                        "temperature": temperture,
                        "light": light,
                        "hall": hall
                    })
                    self.output_data_text.appendPlainText(f"fetch sensor data(temperatute, light, hall, shake):[{temperture}, {light}, {hall}, {shake}]") # type: ignore
            elif command == 0x04: # 返回写入序列号的结果
                self.log.info(f"收到写入序列号后返回的数据帧：{self._show_btyes_with_space(data)}")
                self.output_data_text.appendPlainText(f"set seq success: {self._show_btyes_with_space(data[4:10])}")
            elif command == 0x05: # 获取从机序列号
                self.device_seq = data[4:-1]
                self.output_data_text.appendPlainText(f"update device sequence: {self._show_btyes_with_space(self.device_seq)}")
                self.log.info(f"获取到连接从机的序列号：{self.device_seq.hex()}")

                self.check_device_seq(self.device_seq) # 每次获取完从机序列号后，检查从机序列号是否正确
            elif command == 0x06: # 提交刷卡信息
                rfid_seq = data[4:-1]
                self.web.submit_card_swipe(self.device_seq.hex(), rfid_seq.hex())
                self.log.info(f"获取到刷卡信息：{self._show_btyes_with_space(rfid_seq)}")
            elif command == 0xFF: # DEBUG模式，不做处理，log中会输出信息
                msg = ' '.join(f'{b:02X}' for b in data)
                self.log.debug(f"收到感知层传来的DEBUG信息：{msg}")
            else:
                self.log.warning(f"接收到未编码的指令：{command}")
    
    def check_device_seq(self, seq: bytes):
        """检查从机序列号，如果不正确则进行序列号分配
        这个函数是分配序列号的！不要拿来检查序列号
        """
        if seq == b"\x00"*6: # 设备无序列号，进行
            self._fetch_device_sequence() # 发送分配序列号的请求
            # self._get_device_list_handler() # 更新设备列表
            # self._is_need_update_device_seq = True # 回调中使用，需要进行设备序列号更新
    def _fetch_device_sequence(self):
        self.web.fetch_device_sequence()

    def _clear_receive(self):
        """清空接收区"""
        self.textReceive.clear()
        self.log.info("接收区已清空")
    
    def _clear_send(self):
        """清空发送区"""
        self.textSend.clear()
        self.log.info("发送区已清空")

    def _web_resp_parse(self, data: dict):
        """
        网络请求响应的处理
        Args:
            data:
                - status: 返回状态码
                - url: 请求的url
                - resp: 返回响应体
        """

        if data.get("url").endswith("get_device_list") and data.get("status") == 200: # type: ignore # 获取到设备序列号列表，输出
            self.output_data_text.appendPlainText(data.get("resp")) # type: ignore

            """4.1 实现逻辑更新，现在获取设备列表后不需要更新序列号"""
            # 如果需要更新从机设备的序列号，进入下面的逻辑
            # if self._is_need_update_device_seq:
            #     try:
            #         device_list = list(data.get("resp")) # type: ignore
            #         tmp_seq = self.create_device_seq(device_list)

            #         data = b"\xaa\x55\x04"+tmp_seq+b"\x00"*14 # type: ignore
            #         data = data+self._get_check_sum(data) # type: ignore
            #         self.serialt.send_data(data) # type: ignore

            #         self._is_need_update_device_seq = False # 恢复原来的状态
            #         self.device_seq = tmp_seq # 更新设备序列号为新的序列号
            #     except Exception as e:
            #         self.log.error(f"运行函数[_web_resp_parse]发生错误：{e}")
        elif data.get("url").endswith("distribute_seq") and data.get("status") == 200:
            try:
                msg = json.loads(data.get("resp")).get("device_seq")
                self.log.info(f"收到应用层分配的序列号：{msg}")

                msg = b"\xaa\x55\x04"+bytes.fromhex(msg)+b"\x00"*14
                
                msg = msg+self._get_check_sum(msg)
                self.log.debug(f"发送设置从机序列号的数据帧：{self._show_btyes_with_space(msg)}")
                
                self.serialt.send_data(msg)
            except Exception as e:
                self.log.error(f"执行 _setseq_handler 发生错误：{e}")

    def create_device_seq(self, device_list: list):
        """
        返回一个尽可能与device_list不冲突的序列号 函数已弃用
        补充：这是最开始的逻辑，现在将这一过程放在应用层
        """
        existing_seqs = set()
        for seq_hex in device_list:
            try:
                existing_seqs.add(int(seq_hex, 16))
            except ValueError:
                continue
        
        # 生成随机序列号，最多尝试100次
        for _ in range(100):
            new_seq = random.randint(0, 0xFFFFFFFFFFFF) # 6字节最大值
            if new_seq not in existing_seqs:
                self.log.info(f"自动分配序列号：{new_seq:02X}")
                return new_seq.to_bytes(6, "big")
        
        # 100次都冲突的话，返回一个随机值（极不可能发生）
        return random.randint(1, 0xFFFFFFFFFFFF).to_bytes(6, "big")

    def _update_stats(self):
        """更新统计信息 弃用"""
        pass
        # self.labelStats.setText(
        #     f"统计：发送 {self.bytes_sent} 字节 | 接收 {self.bytes_received} 字节"
        # )
    
    # 窗口事件
    def closeEvent(self, event):
        """窗口关闭事件 弃用"""
        if self._is_connected:
            self.log.info("正在关闭应用程序...")
            self._disconnect()
        self.log.info("应用程序已关闭")
        event.accept()


# 主程序入口
def main():

    """主函数"""
    app = QApplication(sys.argv)
    # app.setStyle("Fusion")
    
    window = SerialToolWindow(app)
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
