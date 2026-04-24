import secrets
from model.dbObject import db
from model.logger import log
from utils.config import get_config

def ensure_root_user():
    """确保 root 用户存在，每次启动时更新其密码为新随机密码"""
    root_username = get_config().get("ROOT_USERNAME", None)

    if not root_username:
        log.critical("运行未找到ROOT_USERNAME! 请配置该项！")
        root_username = "root"

    password = secrets.token_hex(16) # 16字节
    result = db.get_auth_pwd(root_username)
    if result["status"] == "not_found":
        db.add_auth(root_username, password)
        log.info(f"Root 用户已创建，用户名: {root_username}, 密码: {password}")
        print(f"\n{'='*60}")
        print(f"Root 用户已创建！")
        print(f"用户名: {root_username}")
        print(f"密码: {password}")
        print(f"{'='*60}\n")
    else:
        db.update_auth(root_username, password)
        log.info(f"Root 密码已更新，用户名: {root_username}, 密码: {password}")
        print(f"\n{'='*60}")
        print(f"Root 密码已更新！")
        print(f"用户名: {root_username}")
        print(f"密码: {password}")
        print(f"{'='*60}\n")