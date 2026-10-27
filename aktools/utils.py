# -*- coding:utf-8 -*-
# !/usr/bin/env python
"""
Date: 2024/12/12 18:00
Desc: 工具函数
"""

import logging

import requests

logger = logging.getLogger("AKToolsLog")

# 获取失败时返回的占位版本，避免主页因网络问题而报错
FALLBACK_VERSION = "0.0.0"

# 仅缓存成功获取到的版本：失败不写入缓存，网络恢复后下次请求可重试
_version_cache: dict[str, str] = {}


def get_latest_version(package: str = "akshare") -> str:
    """
    获取开源库在 PyPI 上的最新版本
    https://pypi.org/project/akshare/
    网络异常或响应格式异常时返回占位版本，保证主页与 /version 接口不会因此报错
    :param package: 库名称
    :type package: str
    :return: 版本号
    :rtype: str
    """
    if package in _version_cache:
        return _version_cache[package]
    url = f"https://pypi.org/pypi/{package}/json"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/58.0.3029.110 Safari/537.3"
    }
    try:
        r = requests.get(url, headers=headers, timeout=5)
        r.raise_for_status()
        version = r.json()["info"]["version"]
    except (requests.exceptions.RequestException, ValueError, KeyError) as e:
        logger.info(f"获取 {package} 最新版本失败：{e}")
        return FALLBACK_VERSION
    _version_cache[package] = version
    return version
