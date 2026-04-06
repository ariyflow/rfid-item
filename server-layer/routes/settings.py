"""本文件夹存放所有和路由相关的设置"""

from pathlib import Path

ROOT_DIR = Path(__file__).parent.parent # 项目的根目录
STATIC_DIR = "static" # 存放静态文件的目录


"""放弃提供修改这里参数的接口"""
# def set_root_dir(path: Path | str):
#     """设置当前的项目根目录"""
#     global ROOT_DIR
#     if isinstance(path, Path):
#         ROOT_DIR = path
#     elif isinstance(path, str):
#         ROOT_DIR = Path(path)
#     else:
#         raise TypeError(
#             "ROOT_DIR must be a path."
#         )
    
# def set_static_dir(path: Path | str):
#     """设置静态文件存储的目录"""
#     global STATIC_DIR
#     if isinstance(path, Path):
#         STATIC_DIR = path
#     elif isinstance(path, str):
#         STATIC_DIR = Path(path)
#     else:
#         raise TypeError(
#             "STATIC_DIR must be a path."
#         )