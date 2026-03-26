import sqlite3 as sl
import os

"""
数据库管理模块
"""

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) # 项目根目录
DATABASE_LOCATION = os.path.join(BASE_DIR, "database") # 数据保存的目录

DATABASE_NAME = "data.db" # 数据保存到目录

class dbObject:
    def __init__(self, logger):

        self.par = logger

        if not os.path.exists(DATABASE_LOCATION):
            os.makedirs(DATABASE_LOCATION)

        self.conn = sl.connect(os.path.join(DATABASE_LOCATION, DATABASE_NAME))
        self.cur = self.conn.cursor()

        self.cur.execute('''
            CREATE TABLE IF NOT EXISTS sensor_data(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                device_seq TEXT,
                temperature FLOAT,
                light INT,
                hall INT,
                timestamp TEXT
            )
        ''')
        self.conn.commit()

    def insert_sensor_data(self, data: dict):
        """插入传感器数据
        Args:
            data: 字典，包含 device_seq, temperature, light, hall, timestamp
        Returns:
            status: 成功返回True,失败返回False
        """
        if not data or not data.get('device_seq'):
            return False
        try:
            self.cur.execute('''
                INSERT INTO sensor_data (device_seq, temperature, light, hall, timestamp)
                VALUES (?, ?, ?, ?, ?)
            ''', (data.get('device_seq'), data.get('temperature'),
                data.get('light'), data.get('hall'), data.get('timestamp')))
            self.conn.commit()
            self.par.info(f"向数据库写入信息成功：{data}")
            return True
        except Exception as e:
            self.par.error(f"运行函数[insert_sensor_data]时发生错误：{e}")
        return False

    def get_sensor_data(self, start: int, num: int):
        """获取传感器数据
        Args:
            start: 起始位置（从 0 开始）
            num: 返回 n 条数据
        Returns:
            list: 传感器数据列表
        """
        try:
            self.cur.execute('''
                SELECT id, device_seq, temperature, light, hall, timestamp
                FROM sensor_data
                ORDER BY id DESC
                LIMIT ? OFFSET ?
            ''', (num, start))
            self.par.info(f"获取数据库信息成功，信息条数：{num}")
            return self.cur.fetchall()
        except Exception as e:
            self.par.error(f"运行函数[get_sensor_data]时发生错误：{e}")

    def quit_handler(self):
        """数据库退出"""
        try:
            if self.conn and self.cur:
                self.cur.close()
                self.conn.close()
        except Exception as e:
            self.par.error(f"run [quit_handler] error: {e}")

if __name__ == "__main__":
    print(os.path.join(DATABASE_LOCATION, DATABASE_NAME))