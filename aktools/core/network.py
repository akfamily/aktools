# -*- coding:utf-8 -*-
# !/usr/bin/env python
"""
Date: 2026/10/30 10:00
Desc: 全局代理与请求超时
服务启动时读取环境变量，通过 AKShare 1.20.4 起提供的 ak.set_proxies、ak.set_timeout 设置一次：
    AKTOOLS_PROXY：代理地址，如 http://127.0.0.1:7890，同时用于 http 与 https 请求
    AKTOOLS_TIMEOUT：读取超时（秒），连接超时固定为 10 秒
环境变量由命令行参数 --proxy、--timeout 设置，也可在 Gunicorn、Docker 部署或 MCP 客户端配置中直接设置。
AKShare 的这两项是进程级的全局配置，不能按请求切换：AKTools 在线程池中同时处理多个请求，
按请求修改会相互影响，因此只在启动时设置
"""

import os
from typing import List, Mapping, Optional

import akshare as ak

PROXY_ENV = "AKTOOLS_PROXY"
TIMEOUT_ENV = "AKTOOLS_TIMEOUT"
CONNECT_TIMEOUT = 10
UPGRADE_HINT = "当前 AKShare 版本为 {version}，需要 1.20.4 及以上版本才支持{feature}，请升级 AKShare"


def _parse_timeout(value: str) -> Optional[float]:
    """解析读取超时；不是正数时返回 None"""
    try:
        seconds = float(value)
    except ValueError:
        return None
    return seconds if seconds > 0 else None


def apply_network_settings(env: Mapping[str, str] = os.environ) -> List[str]:
    """
    按环境变量设置 AKShare 的全局代理与请求超时；未设置的项保持 AKShare 的默认行为
    :param env: 环境变量，默认为 os.environ
    :type env: Mapping
    :return: 设置结果或提示，供启动时写入日志
    :rtype: list
    """
    messages: List[str] = []
    proxy = env.get(PROXY_ENV, "").strip()
    if proxy:
        if hasattr(ak, "set_proxies"):
            ak.set_proxies({"http": proxy, "https": proxy})
            messages.append(f"已设置代理：{proxy}")
        else:
            messages.append(
                UPGRADE_HINT.format(version=ak.__version__, feature=PROXY_ENV)
            )
    raw_timeout = env.get(TIMEOUT_ENV, "").strip()
    if raw_timeout:
        timeout = _parse_timeout(raw_timeout)
        if timeout is None:
            messages.append(f"{TIMEOUT_ENV}={raw_timeout} 不是正数，已忽略")
        elif hasattr(ak, "set_timeout"):
            ak.set_timeout((CONNECT_TIMEOUT, timeout))
            messages.append(
                f"已设置请求超时：连接 {CONNECT_TIMEOUT} 秒，读取 {timeout:g} 秒"
            )
        else:
            messages.append(
                UPGRADE_HINT.format(version=ak.__version__, feature=TIMEOUT_ENV)
            )
    return messages
