import logging
import os

"""
日志管理模块
"""

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) # 项目根目录
SAVE_LOG_PATH = os.path.join(BASE_DIR, "log") # 日志保存的路径

LOG_FILE_NAME = "server.log" # 日志的文件名

class myLogger(logging.Logger):
    def __init__(self):
        super().__init__(__name__)

        # 确保日志目录存在
        if not os.path.exists(SAVE_LOG_PATH):
            os.makedirs(SAVE_LOG_PATH)

        # 创建文件 handler（只输出到文件，不影响控制台）
        handler = logging.FileHandler(
            os.path.join(SAVE_LOG_PATH, LOG_FILE_NAME),
            encoding="utf-8"
        )
        handler.setLevel(logging.DEBUG)
        handler.setFormatter(logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        ))

        # 添加 handler 到当前 logger
        self.addHandler(handler)


log = myLogger() # 操作日志的log