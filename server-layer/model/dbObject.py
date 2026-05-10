import sqlite3 as sl
import os
import hashlib
from model.logger import log
import time
from utils.config import get_config
"""
数据库管理模块
"""

config: dict = get_config().get("database")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # 项目根目录
DATABASE_LOCATION = os.path.join(BASE_DIR, "database")  # 数据保存的目录

DATABASE_NAME = config.get("DATABASE_NAME")# 数据保存到目录
DEVICE_TABLE_NAME = config.get("DEVICE_TABLE_NAME") # 设备列表的名字
SENSOR_TABLE_PREFIX = config.get("SENSOR_TABLE_PREFIX") # 设备传感器数据表名字的前缀
CARD_SWIPES_TABLE_NAME = config.get("CARD_SWIPES_TABLE_NAME") # 刷卡记录表名
RFID_CARDS_TABLE_NAME = config.get("RFID_CARDS_TABLE_NAME") # RFID卡管理表名


def _get_conn():
    """获取一个新的数据库连接（线程安全）"""
    return sl.connect(os.path.join(DATABASE_LOCATION, DATABASE_NAME), timeout=30)


class dbObject:
    def __init__(self, logger):
        self.par = logger
        if not os.path.exists(DATABASE_LOCATION):
            os.makedirs(DATABASE_LOCATION)

        # 初始化数据库和表结构
        conn = _get_conn()
        cur = conn.cursor()

        cur.execute(f"""
            CREATE TABLE IF NOT EXISTS {DEVICE_TABLE_NAME}(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                device_seq TEXT UNIQUE,
                created_at TEXT
            )
        """)
        conn.commit()

        # 检查所有设备的表是否存在，不存在则创建
        cur.execute("SELECT device_seq FROM devices")
        device_list = cur.fetchall()
        for (device_seq,) in device_list:
            table_name = f"{SENSOR_TABLE_PREFIX}{device_seq}"
            cur.execute(f"""
                CREATE TABLE IF NOT EXISTS {table_name}(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    temperature FLOAT,
                    light INT,
                    hall INT,
                    timestamp TEXT
                )
            """)
        conn.commit()

        # 创建 auth 表
        cur.execute("""
            CREATE TABLE IF NOT EXISTS auth(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                timestamp TEXT NOT NULL
            )
        """)
        conn.commit()

        # 创建 card_swipes 表
        cur.execute(f"""
            CREATE TABLE IF NOT EXISTS {CARD_SWIPES_TABLE_NAME}(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                device_seq TEXT,
                rfid_serial TEXT,
                timestamp TEXT
            )
        """)
        conn.commit()

        # 创建 rfid_cards 表
        cur.execute(f"""
            CREATE TABLE IF NOT EXISTS {RFID_CARDS_TABLE_NAME}(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                uid TEXT UNIQUE NOT NULL,
                balance REAL DEFAULT 0,
                created_at TEXT,
                updated_at TEXT
            )
        """)
        conn.commit()

        cur.close()
        conn.close()

    def insert_sensor_data(self, data: dict):
        """插入传感器数据
        Args:
            data: 字典，包含 device_seq, temperature, light, hall, timestamp
        Returns:
            status: 成功返回True,失败返回False
        """
        if not data or not data.get("device_seq"):
            return False

        device_seq = data.get("device_seq")
        table_name = f"{SENSOR_TABLE_PREFIX}{device_seq}"

        try:
            conn = _get_conn()
            cur = conn.cursor()

            # 检查 devices 表中是否存在该设备
            cur.execute("SELECT device_seq FROM devices WHERE device_seq = ?", (device_seq,))
            if not cur.fetchone():
                # 创建设备专属表
                cur.execute(f"""
                    CREATE TABLE IF NOT EXISTS {table_name}(
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        temperature FLOAT,
                        light INT,
                        hall INT,
                        timestamp TEXT
                    )
                """)
                # 在 devices 表中添加设备记录
                cur.execute(
                    "INSERT INTO devices (device_seq, created_at) VALUES (?, ?)",
                    (device_seq, data.get("timestamp"))
                )
                self.par.info(f"创建新设备表：{table_name}")

            # 插入数据到设备专属表
            cur.execute(
                f"INSERT INTO {table_name} (temperature, light, hall, timestamp) VALUES (?, ?, ?, ?)",
                (
                    data.get("temperature"),
                    data.get("light"),
                    data.get("hall"),
                    data.get("timestamp"),
                ),
            )
            conn.commit()
            self.par.debug(f"向设备表 {table_name} 写入信息成功：{data}")
            cur.close()
            conn.close()
            return True
        except Exception as e:
            self.par.error(f"运行函数[insert_sensor_data]时发生错误：{e}")
        return False

    def get_sensor_data(self, start: int, num: int, device_seq: str = None):
        """获取传感器数据
        Args:
            start: 起始位置（从 0 开始）
            num: 返回 n 条数据
            device_seq: 要获取数据的设备序列号
        Returns:
            list: 传感器数据列表
        """
        if not device_seq:
            self.par.error("get_sensor_data 需要指定 device_seq")
            return []

        table_name = f"sensor_data_{device_seq}"

        try:
            conn = _get_conn()
            cur = conn.cursor()
            cur.execute(
                f"""
                SELECT id, temperature, light, hall, timestamp
                FROM {table_name}
                ORDER BY id DESC
                LIMIT ? OFFSET ?
            """,
                (num, start),
            )
            tmp = cur.fetchall()
            self.par.info(f"从设备表 {table_name} 获取数据成功，条数：{len(tmp)}")

            cur.close()
            conn.close()
            columns = ["id", "temperature", "light", "hall", "timestamp"]
            return [dict(zip(columns, row)) for row in tmp]
        except Exception as e:
            self.par.error(f"运行函数[get_sensor_data]时发生错误：{e}")
            return []

    def remove_sensor_data(self, id: int, device_seq: str = None) -> dict:
        """删除传感器数据
        Args:
            id: 要删除的数据ID
            device_seq: 设备序列号（必填）
        Returns:
            dict: 包含删除状态的字典
        """
        if not device_seq:
            return {"status": "error", "message": "缺少 device_seq 参数"}

        if id is None or not isinstance(id, int) or id <= 0:
            return {"status": "error", "message": "无效的ID"}

        table_name = f"sensor_data_{device_seq}"

        try:
            conn = _get_conn()
            cur = conn.cursor()

            cur.execute(f"SELECT id FROM {table_name} WHERE id = ?", (id,))
            result = cur.fetchone()
            if result is None:
                cur.close()
                conn.close()
                return {"status": "not_found", "message": f"ID为{id}的数据不存在"}

            cur.execute(f"DELETE FROM {table_name} WHERE id = ?", (id,))
            conn.commit()
            self.par.debug(f"从设备表 {table_name} 删除ID为 {id} 的传感器数据成功")
            cur.close()
            conn.close()
            return {"status": "success", "message": "删除成功"}
        except Exception as e:
            self.par.error(f"运行函数[remove_sensor_data]时发生错误：{e}")
            return {"status": "error", "message": str(e)}

    def get_device_list(self):
        """获取所有设备序列号列表
        Returns:
            list: 设备序列号列表
        """
        try:
            conn = _get_conn()
            cur = conn.cursor()

            cur.execute("SELECT device_seq FROM devices ORDER BY id DESC")
            device_list = cur.fetchall()

            cur.close()
            conn.close()

            return [row[0] for row in device_list]
        except Exception as e:
            self.par.error(f"运行函数[get_device_list]时发生错误：{e}")
            return []

    def add_device(self, seq: str, timestamp: str = None) -> dict:
        """添加设备并创建数据表
        Args:
            seq: 设备序列号
            timestamp: 创建时间戳（可选）
        Returns:
            dict: 包含添加状态的字典
        """
        if not seq:
            return {"status": "error", "message": "缺少设备序列号参数"}

        table_name = f"{SENSOR_TABLE_PREFIX}{seq}"

        try:
            conn = _get_conn()
            cur = conn.cursor()

            # 检查设备是否已存在
            cur.execute("SELECT device_seq FROM devices WHERE device_seq = ?", (seq,))
            if cur.fetchone():
                cur.close()
                conn.close()
                return {"status": "exist", "message": f"设备 {seq} 已存在"}

            # 创建设备专属表
            cur.execute(f"""
                CREATE TABLE IF NOT EXISTS {table_name}(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    temperature FLOAT,
                    light INT,
                    hall INT,
                    timestamp TEXT
                )
            """)
            self.par.debug(f"创建设备数据表：{table_name}")

            # 在 devices 表中添加设备记录
            cur.execute(
                "INSERT INTO devices (device_seq, created_at) VALUES (?, ?)",
                (seq, timestamp)
            )
            conn.commit()
            self.par.info(f"添加设备 {seq} 及其数据表成功")

            cur.close()
            conn.close()
            return {"status": "success", "message": "添加成功"}
        except Exception as e:
            self.par.error(f"运行函数 [add_device] 时发生错误：{e}")
            return {"status": "error", "message": str(e)}

    def remove_device(self, seq: str) -> dict:
        """删除设备及其数据表
        Args:
            seq: 设备序列号
        Returns:
            dict: 包含删除状态的字典
        """
        if not seq:
            return {"status": "error", "message": "缺少设备序列号参数"}

        table_name = f"{SENSOR_TABLE_PREFIX}{seq}"

        try:
            conn = _get_conn()
            cur = conn.cursor()

            # 检查设备是否存在
            cur.execute("SELECT device_seq FROM devices WHERE device_seq = ?", (seq,))
            if not cur.fetchone():
                cur.close()
                conn.close()
                return {"status": "not_found", "message": f"设备 {seq} 不存在"}

            # 删除设备数据表
            cur.execute(f"DROP TABLE IF EXISTS {table_name}")
            self.par.debug(f"删除设备数据表：{table_name}")

            # 从设备表中删除设备记录
            cur.execute("DELETE FROM devices WHERE device_seq = ?", (seq,))
            conn.commit()
            self.par.info(f"删除设备 {seq} 及其数据表成功")

            cur.close()
            conn.close()
            return {"status": "success", "message": "delete success"}
        except Exception as e:
            self.par.error(f"运行函数[remove_device]时发生错误：{e}")
            return {"status": "error", "message": str(e)}

    def add_auth(self, username: str, password: str) -> dict:
        """添加用户
        Args:
            username: 用户名
            password: 密码（明文，会自动进行哈希处理）
        Returns:
            dict: 包含添加状态的字典
        """
        if not username:
            return {"status": "error", "message": "缺少用户名参数"}

        if not password:
            return {"status": "error", "message": "缺少密码参数"}

        timestamp = str(time.time())
        try:
            conn = _get_conn()
            cur = conn.cursor()

            # 检查用户是否已存在
            cur.execute("SELECT username FROM auth WHERE username = ?", (username,))
            if cur.fetchone():
                cur.close()
                conn.close()
                return {"status": "exist", "message": f"用户 {username} 已存在"}

            # 对密码进行哈希处理
            password_hash = hashlib.sha256(password.encode()).hexdigest()

            # 插入用户记录
            cur.execute(
                "INSERT INTO auth (username, password_hash, timestamp) VALUES (?, ?, ?)",
                (username, password_hash, timestamp)
            )
            conn.commit()
            self.par.info(f"添加用户 {username} 成功")

            cur.close()
            conn.close()
            return {"status": "success", "message": "添加成功"}
        except Exception as e:
            self.par.error(f"运行函数 [add_auth] 时发生错误：{e}")
            return {"status": "error", "message": str(e)}

    def remove_auth(self, username: str) -> dict:
        """移除用户
        Args:
            username: 用户名
        Returns:
            dict: 包含删除状态的字典
        """
        if not username:
            return {"status": "error", "message": "缺少用户名参数"}

        try:
            conn = _get_conn()
            cur = conn.cursor()

            # 检查用户是否存在
            cur.execute("SELECT username FROM auth WHERE username = ?", (username,))
            if not cur.fetchone():
                cur.close()
                conn.close()
                return {"status": "not_found", "message": f"用户 {username} 不存在"}

            # 删除用户记录
            cur.execute("DELETE FROM auth WHERE username = ?", (username,))
            conn.commit()
            self.par.info(f"删除用户 {username} 成功")

            cur.close()
            conn.close()
            return {"status": "success", "message": "删除成功"}
        except Exception as e:
            self.par.error(f"运行函数 [remove_auth] 时发生错误：{e}")
            return {"status": "error", "message": str(e)}

    def get_auth_pwd(self, username: str) -> dict:
        """获取用户的密码哈希
        Args:
            username: 用户名
        Returns:
            dict: 包含密码哈希的字典，格式：{"status": "success", "password_hash": "..."}
                  或错误信息：{"status": "not_found", "message": "..."}
        """
        if not username:
            return {"status": "error", "message": "缺少用户名参数"}

        try:
            conn = _get_conn()
            cur = conn.cursor()

            # 查询用户的密码哈希
            cur.execute("SELECT password_hash FROM auth WHERE username = ?", (username,))
            result = cur.fetchone()

            if result is None:
                cur.close()
                conn.close()
                return {"status": "not_found", "message": f"用户 {username} 不存在"}

            password_hash = result[0]
            self.par.info(f"获取用户 {username} 的密码哈希成功")

            cur.close()
            conn.close()
            return {"status": "success", "password_hash": password_hash}
        except Exception as e:
            self.par.error(f"运行函数 [get_auth_pwd] 时发生错误：{e}")
            return {"status": "error", "message": str(e)}

    def get_all_auth(self) -> dict:
        """获取所有用户
        Returns:
            dict: 包含用户列表的字典，格式：{"status": "success", "users": [{"id": ..., "username": ..., "timestamp": ...}, ...]}
        """
        try:
            conn = _get_conn()
            cur = conn.cursor()

            cur.execute("SELECT id, username, timestamp FROM auth ORDER BY id ASC")
            rows = cur.fetchall()

            cur.close()
            conn.close()

            users = [{"id": row[0], "username": row[1], "timestamp": row[2]} for row in rows]
            self.par.info(f"获取所有用户成功，共 {len(users)} 个用户")
            return {"status": "success", "users": users}
        except Exception as e:
            self.par.error(f"运行函数 [get_all_auth] 时发生错误：{e}")
            return {"status": "error", "message": str(e)}

    def update_auth(self, username: str, new_password: str) -> dict:
        """更新用户密码
        Args:
            username: 用户名
            new_password: 新密码（明文，会自动进行哈希处理）
        Returns:
            dict: 包含更新状态的字典
        """
        if not username:
            return {"status": "error", "message": "缺少用户名参数"}

        if not new_password:
            return {"status": "error", "message": "缺少新密码参数"}

        try:
            conn = _get_conn()
            cur = conn.cursor()

            # 检查用户是否存在
            cur.execute("SELECT username FROM auth WHERE username = ?", (username,))
            if not cur.fetchone():
                cur.close()
                conn.close()
                return {"status": "not_found", "message": f"用户 {username} 不存在"}

            # 对新密码进行哈希处理
            password_hash = hashlib.sha256(new_password.encode()).hexdigest()
            timestamp = str(time.time())

            # 更新用户密码
            cur.execute(
                "UPDATE auth SET password_hash = ?, timestamp = ? WHERE username = ?",
                (password_hash, timestamp, username)
            )
            conn.commit()
            self.par.info(f"更新用户 {username} 密码成功")

            cur.close()
            conn.close()
            return {"status": "success", "message": "更新成功"}
        except Exception as e:
            self.par.error(f"运行函数 [update_auth] 时发生错误：{e}")
            return {"status": "error", "message": str(e)}

    def insert_card_swipe(self, device_seq: str, rfid_serial: str, timestamp: str) -> dict:
        """插入刷卡记录
        Args:
            device_seq: 设备序列号
            rfid_serial: RFID卡序列号
            timestamp: 刷卡时间
        Returns:
            dict: 包含插入状态的字典
        """
        if not device_seq:
            return {"status": "error", "message": "缺少设备序列号参数"}

        if not rfid_serial:
            return {"status": "error", "message": "缺少RFID序列号参数"}

        try:
            conn = _get_conn()
            cur = conn.cursor()

            cur.execute(
                f"INSERT INTO {CARD_SWIPES_TABLE_NAME} (device_seq, rfid_serial, timestamp) VALUES (?, ?, ?)",
                (device_seq, rfid_serial, timestamp)
            )
            conn.commit()
            self.par.debug(f"写入刷卡记录成功：device_seq={device_seq}, rfid_serial={rfid_serial}")

            cur.close()
            conn.close()
            return {"status": "success", "message": "插入成功"}
        except Exception as e:
            self.par.error(f"运行函数 [insert_card_swipe] 时发生错误：{e}")
            return {"status": "error", "message": str(e)}

    def get_card_swipes(self, start: int, num: int, device_seq: str = None) -> dict:
        """获取刷卡记录
        Args:
            start: 起始位置（从 0 开始）
            num: 返回 n 条数据
            device_seq: 设备序列号（可选，为空则返回所有设备的记录）
        Returns:
            dict: 包含刷卡记录的字典
        """
        try:
            conn = _get_conn()
            cur = conn.cursor()

            if device_seq:
                cur.execute(
                    f"""
                    SELECT id, device_seq, rfid_serial, timestamp
                    FROM {CARD_SWIPES_TABLE_NAME}
                    WHERE device_seq = ?
                    ORDER BY id DESC
                    LIMIT ? OFFSET ?
                """,
                    (device_seq, num, start)
                )
            else:
                cur.execute(
                    f"""
                    SELECT id, device_seq, rfid_serial, timestamp
                    FROM {CARD_SWIPES_TABLE_NAME}
                    ORDER BY id DESC
                    LIMIT ? OFFSET ?
                """,
                    (num, start)
                )

            rows = cur.fetchall()
            swipes = [{"id": row[0], "device_seq": row[1], "rfid_serial": row[2], "timestamp": row[3]} for row in rows]
            self.par.info(f"获取刷卡记录成功，共 {len(swipes)} 条")

            cur.close()
            conn.close()
            return {"status": "success", "swipes": swipes}
        except Exception as e:
            self.par.error(f"运行函数 [get_card_swipes] 时发生错误：{e}")
            return {"status": "error", "message": str(e)}

    def get_rfid_cards(self, start: int = 0, num: int = 100) -> dict:
        """获取所有RFID卡
        Args:
            start: 起始位置
            num: 返回条数
        Returns:
            dict: {"status": "success", "cards": [...]}
        """
        try:
            conn = _get_conn()
            cur = conn.cursor()
            cur.execute(
                f"SELECT id, uid, balance, created_at, updated_at FROM {RFID_CARDS_TABLE_NAME} ORDER BY id DESC LIMIT ? OFFSET ?",
                (num, start)
            )
            rows = cur.fetchall()
            cur.close()
            conn.close()
            columns = ["id", "uid", "balance", "created_at", "updated_at"]
            return {"status": "success", "cards": [dict(zip(columns, row)) for row in rows]}
        except Exception as e:
            log.error(f"运行函数[get_rfid_cards]时发生错误：{e}")
            return {"status": "error", "message": str(e)}

    def get_rfid_card(self, uid: str) -> dict:
        """获取单个RFID卡
        Args:
            uid: RFID卡的UID
        Returns:
            dict: 包含卡信息的字典
        """
        if not uid:
            return {"status": "error", "message": "UID不能为空"}
        try:
            conn = _get_conn()
            cur = conn.cursor()
            cur.execute(
                f"SELECT id, uid, balance, created_at, updated_at FROM {RFID_CARDS_TABLE_NAME} WHERE uid = ?",
                (uid,)
            )
            row = cur.fetchone()
            cur.close()
            conn.close()
            if row is None:
                return {"status": "not_found", "message": f"RFID卡 {uid} 不存在"}
            columns = ["id", "uid", "balance", "created_at", "updated_at"]
            return {"status": "success", "card": dict(zip(columns, row))}
        except Exception as e:
            log.error(f"运行函数[get_rfid_card]时发生错误：{e}")
            return {"status": "error", "message": str(e)}

    def add_rfid_card(self, uid: str, balance: float = 0) -> dict:
        """添加RFID卡
        Args:
            uid: RFID卡的UID
            balance: 初始余额
        Returns:
            dict: 包含添加状态的字典
        """
        if not uid:
            return {"status": "error", "message": "UID不能为空"}
        try:
            timestamp = str(time.time())
            conn = _get_conn()
            cur = conn.cursor()
            cur.execute(
                f"INSERT INTO {RFID_CARDS_TABLE_NAME} (uid, balance, created_at, updated_at) VALUES (?, ?, ?, ?)",
                (uid, balance, timestamp, timestamp)
            )
            conn.commit()
            cur.close()
            conn.close()
            log.info(f"添加RFID卡 {uid} 成功，余额: {balance}")
            return {"status": "success", "message": "添加成功"}
        except Exception as e:
            log.error(f"运行函数[add_rfid_card]时发生错误：{e}")
            return {"status": "error", "message": str(e)}

    def update_rfid_card_balance(self, uid: str, amount: float, mode: str = "add") -> dict:
        """修改RFID卡余额
        Args:
            uid: RFID卡的UID
            amount: 金额（mode为"add"时增减，mode为"set"时设为绝对值）
            mode: "add" - 增加/扣除余额；"set" - 直接设置余额
        Returns:
            dict: 包含操作状态的字典
        """
        if not uid:
            return {"status": "error", "message": "UID不能为空"}
        try:
            timestamp = str(time.time())
            conn = _get_conn()
            cur = conn.cursor()

            # 检查卡是否存在
            cur.execute(f"SELECT id, balance FROM {RFID_CARDS_TABLE_NAME} WHERE uid = ?", (uid,))
            row = cur.fetchone()

            if row is None:
                # 卡不存在
                if mode == "add":
                    # 增加余额时自动创建
                    cur.execute(
                        f"INSERT INTO {RFID_CARDS_TABLE_NAME} (uid, balance, created_at, updated_at) VALUES (?, ?, ?, ?)",
                        (uid, amount, timestamp, timestamp)
                    )
                    conn.commit()
                    new_balance = amount
                    log.info(f"RFID卡 {uid} 不存在，已自动创建，余额: {new_balance}")
                    cur.close()
                    conn.close()
                    return {"status": "success", "message": "卡不存在，已自动创建", "balance": new_balance}
                else:
                    cur.close()
                    conn.close()
                    return {"status": "not_found", "message": f"RFID卡 {uid} 不存在"}
            else:
                current_id, current_balance = row
                if mode == "add":
                    new_balance = current_balance + amount
                elif mode == "set":
                    new_balance = amount
                else:
                    cur.close()
                    conn.close()
                    return {"status": "error", "message": f"无效的操作模式: {mode}"}

                cur.execute(
                    f"UPDATE {RFID_CARDS_TABLE_NAME} SET balance = ?, updated_at = ? WHERE id = ?",
                    (new_balance, timestamp, current_id)
                )
                conn.commit()
                log.info(f"RFID卡 {uid} 余额已更新: {current_balance} -> {new_balance}")
                cur.close()
                conn.close()
                return {"status": "success", "message": "余额更新成功", "balance": new_balance}
        except Exception as e:
            log.error(f"运行函数[update_rfid_card_balance]时发生错误：{e}")
            return {"status": "error", "message": str(e)}

    def delete_rfid_card(self, uid: str) -> dict:
        """删除RFID卡
        Args:
            uid: RFID卡的UID
        Returns:
            dict: 包含删除状态的字典
        """
        if not uid:
            return {"status": "error", "message": "UID不能为空"}
        try:
            conn = _get_conn()
            cur = conn.cursor()
            cur.execute(f"SELECT id FROM {RFID_CARDS_TABLE_NAME} WHERE uid = ?", (uid,))
            if not cur.fetchone():
                cur.close()
                conn.close()
                return {"status": "not_found", "message": f"RFID卡 {uid} 不存在"}
            cur.execute(f"DELETE FROM {RFID_CARDS_TABLE_NAME} WHERE uid = ?", (uid,))
            conn.commit()
            log.info(f"删除RFID卡 {uid} 成功")
            cur.close()
            conn.close()
            return {"status": "success", "message": "删除成功"}
        except Exception as e:
            log.error(f"运行函数[delete_rfid_card]时发生错误：{e}")
            return {"status": "error", "message": str(e)}

    def ensure_rfid_card(self, uid: str) -> dict:
        """确保RFID卡存在，不存在则创建（余额为0）。
        该方法用于刷卡记录提交时自动注册未知卡。
        Args:
            uid: RFID卡的UID（8字符十六进制小写）
        Returns:
            dict: 包含卡信息的字典
        """
        if not uid:
            return {"status": "error", "message": "UID不能为空"}
        try:
            conn = _get_conn()
            cur = conn.cursor()
            cur.execute(
                f"SELECT id, uid, balance, created_at, updated_at FROM {RFID_CARDS_TABLE_NAME} WHERE uid = ?",
                (uid,)
            )
            row = cur.fetchone()
            if row:
                cur.close()
                conn.close()
                columns = ["id", "uid", "balance", "created_at", "updated_at"]
                return {"status": "success", "card": dict(zip(columns, row))}
            timestamp = str(time.time())
            cur.execute(
                f"INSERT INTO {RFID_CARDS_TABLE_NAME} (uid, balance, created_at, updated_at) VALUES (?, ?, ?, ?)",
                (uid, 0, timestamp, timestamp)
            )
            conn.commit()
            log.info(f"刷卡记录触发自动注册RFID卡 {uid}，余额: 0")
            cur.execute(
                f"SELECT id, uid, balance, created_at, updated_at FROM {RFID_CARDS_TABLE_NAME} WHERE uid = ?",
                (uid,)
            )
            row = cur.fetchone()
            cur.close()
            conn.close()
            columns = ["id", "uid", "balance", "created_at", "updated_at"]
            return {"status": "success", "card": dict(zip(columns, row))}
        except Exception as e:
            log.error(f"运行函数[ensure_rfid_card]时发生错误：{e}")
            return {"status": "error", "message": str(e)}

    def quit_handler(self):
        """数据库退出"""
        return


db = dbObject(log)

if __name__ == "__main__":
    print(os.path.join(DATABASE_LOCATION, DATABASE_NAME))
