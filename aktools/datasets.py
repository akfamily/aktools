# -*- coding:utf-8 -*-
# !/usr/bin/env python
"""
Date: 2022/5/9 18:08
Desc: 定位打包进 wheel 的静态资源（HTML 模板与 favicon 图标）
"""

import pathlib
from importlib import resources

HTML_PACKAGE = "aktools.assets.html"
IMAGE_PACKAGE = "aktools.assets.images"


def _resource_path(package: str, file: str) -> pathlib.Path:
    """
    返回包内资源文件的真实路径
    使用 importlib.resources.files，替代 3.11 起已弃用的 resources.path
    :param package: 资源所在的包名
    :type package: str
    :param file: 资源文件名
    :type file: str
    :return: 资源文件路径
    :rtype: pathlib.Path
    """
    return pathlib.Path(str(resources.files(package) / file))


def get_homepage_html(file: str = "homepage.html") -> pathlib.Path:
    """主页模板的路径"""
    return _resource_path(HTML_PACKAGE, file)


def get_template_path() -> pathlib.Path:
    """Jinja2 模板目录，即 HTML 资源所在目录"""
    return pathlib.Path(str(resources.files(HTML_PACKAGE)))


def get_favicon_path(file: str = "favicon.ico") -> pathlib.Path:
    """favicon 图标的路径"""
    return _resource_path(IMAGE_PACKAGE, file)
