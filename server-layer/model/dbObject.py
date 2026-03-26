import sqlite3 as sl
import os

DATABASE_NAME = "data.db"
DATABASE_LOCATION = os.path.dirname(os.path.abspath(__file__))

class dbObject:
    def __init__(self, par):

        self.par = par

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
        """
        self.cur.execute('''
            INSERT INTO sensor_data (device_seq, temperature, light, hall, timestamp)
            VALUES (?, ?, ?, ?, ?)
        ''', (data.get('device_seq'), data.get('temperature'),
              data.get('light'), data.get('hall'), data.get('timestamp')))
        self.conn.commit()

    def get_sensor_data(self, num: int):
        self.cur.execute('''
            
        ''')

    def quit_handler(self):
        """数据库退出"""
        try:
            if self.conn and self.cur:
                self.cur.close()
                self.conn.close()
        except Exception as e:
            self.par.log.error(f"run [quit_handler] error: {e}")

if __name__ == "__main__":
    print(os.path.join(DATABASE_LOCATION, DATABASE_NAME))