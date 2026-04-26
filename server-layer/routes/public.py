"""public子目录的路由"""

from flask import Flask, Blueprint, request, make_response, jsonify, send_from_directory
from pathlib import Path
import os
from .settings import *
from utils.config import get_config

config = get_config()
STATIC_DIR = config.get("STATIC_DIR", "static") if config else "static"

public_routes = Blueprint("public", __name__, url_prefix="/public")

@public_routes.route("/")
def public_main_handler():
    return make_response(send_from_directory(os.path.join(ROOT_DIR, STATIC_DIR, "html"), "public_index.html"), 200)

if __name__ == "__main__":
    print(ROOT_DIR)