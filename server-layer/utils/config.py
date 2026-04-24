import yaml
import os
from model.logger import log

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_FILE_NAME = "config.yaml"
ENCODING = "UTF-8"

_config = None

def get_config() -> dict | None:
    global _config
    if _config is not None:
        return _config
    
    path = os.path.join(ROOT_DIR, CONFIG_FILE_NAME)
    try:
        with open(path, "r", encoding=ENCODING) as file:
            _config = yaml.safe_load(file)

        return _config
    except Exception as e:
        log.error(f"运行函数[get_config]时出错： {e}")
    
    return None