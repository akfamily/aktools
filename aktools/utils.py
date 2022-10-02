# -*- coding:utf-8 -*-
# !/usr/bin/env python
"""
Date: 2022/9/27 21:58
Desc: 工具函数
"""
from functools import lru_cache

import requests
from bs4 import BeautifulSoup


@lru_cache()
def get_latest_version(package: str = "akshare") -> str:
    """
    获取开源库的最新版本
    https://pypi.org/project/akshare/
    :param package: 库名称
    :type package: str
    :return: 版本
    :rtype: str
    """
    url = f"https://pypi.org/project/{package}"
    try:
        r = requests.get(url, verify=False)
    except requests.exceptions.ProxyError:
        return "0.0.0"
    soup = BeautifulSoup(r.text, "lxml")
    version = (
        soup.find("h1", attrs={"class": "package-header__name"})
        .text.strip()
        .split(" ")[1]
    )
    return version
