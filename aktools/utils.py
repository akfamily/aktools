# -*- coding:utf-8 -*-
# !/usr/bin/env python
"""
Date: 2024/12/12 18:00
Desc: 工具函数
"""
from functools import lru_cache

import requests


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
    url = f"https://pypi.org/pypi/{package}/json"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/58.0.3029.110 Safari/537.3"
    }
    try:
        r = requests.get(url, headers=headers)
    except requests.exceptions.ProxyError:
        return "0.0.0"
    data_json = r.json()
    version = data_json['info']['version']
    return version
