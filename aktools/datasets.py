# -*- coding:utf-8 -*-
# !/usr/bin/env python
"""
Date: 2022/5/9 18:08
Desc: 导入文件工具，可以正确处理路径问题
"""
from importlib import resources
import pathlib


def get_pyscript_html(file: str = "akscript.html") -> pathlib.Path:
    """Get path to data "ths.js" text file."""
    with resources.path("aktools.assets.html", file) as f:
        data_file_path = f
    return data_file_path


def get_template_path():
    with resources.path("aktools.assets.html", "akscript.html") as f:
        data_file_path = f
    return data_file_path.parent


def get_homepage_html(file: str = "homepage.html") -> pathlib.Path:
    """Get path to data "ths.js" text file."""
    with resources.path("aktools.assets.html", file) as f:
        data_file_path = f
    return data_file_path


def get_favicon_path(file: str = "favicon.ico"):
    with resources.path("aktools.assets.images", file) as f:
        data_file_path = f
    return data_file_path


if __name__ == "__main__":
    get_pyscript_html_path = get_pyscript_html(file="akscript.html")
    print(get_pyscript_html_path)
