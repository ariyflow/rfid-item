import secrets
from model.dbObject import db
from model.logger import log

ROOT_USERNAME = "root"

def ensure_root_user():
    """确保 root 用户存在，每次启动时更新其密码为新随机密码"""
    password = secrets.token_hex(16) # 16字节
    result = db.get_auth_pwd(ROOT_USERNAME)
    if result["status"] == "not_found":
        db.add_auth(ROOT_USERNAME, password)
        log.info(f"Root 用户已创建，用户名: {ROOT_USERNAME}, 密码: {password}")
        print(f"\n{'='*60}")
        print(f"Root 用户已创建！")
        print(f"用户名: {ROOT_USERNAME}")
        print(f"密码: {password}")
        print(f"{'='*60}\n")
    else:
        db.update_auth(ROOT_USERNAME, password)
        log.info(f"Root 密码已更新，用户名: {ROOT_USERNAME}, 密码: {password}")
        print(f"\n{'='*60}")
        print(f"Root 密码已更新！")
        print(f"用户名: {ROOT_USERNAME}")
        print(f"密码: {password}")
        print(f"{'='*60}\n")