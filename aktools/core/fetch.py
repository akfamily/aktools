# -*- coding:utf-8 -*-
# !/usr/bin/env python
"""
Date: 2026/10/30 12:00
Desc: 调用 AKShare 接口获取数据，HTTP 路由（/api/public）与 MCP 工具（get_data）共用
包括接口校验、结果缓存、AKShare 内部缓存清理，以及把各类异常对应到 HTTP 状态码与处理建议
"""

import inspect
from typing import Dict, List, Optional, Tuple

import akshare as ak
import akshare.exceptions as ak_exceptions
import pandas as pd
import requests
from fastapi import status

from aktools.core.cache import (
    AKSHARE_CACHE_CLEAR_ENV,
    CACHE_TTL_ENV,
    DEFAULT_AKSHARE_CACHE_CLEAR,
    DEFAULT_CACHE_TTL,
    AkshareCacheJanitor,
    ResultCache,
    env_seconds,
)
from aktools.core.catalog import is_interface
from aktools.core.log import logger
from aktools.core.network import apply_network_settings

DOC_URL = "https://akshare.akfamily.xyz"

result_cache = ResultCache(ttl=env_seconds(CACHE_TTL_ENV, DEFAULT_CACHE_TTL))
akshare_janitor = AkshareCacheJanitor(
    interval=env_seconds(AKSHARE_CACHE_CLEAR_ENV, DEFAULT_AKSHARE_CACHE_CLEAR)
)

# 服务进程启动时按 AKTOOLS_PROXY、AKTOOLS_TIMEOUT 设置一次 AKShare 的全局代理与超时；
# 放在本模块而不是路由模块中，以 stdio 方式运行的 MCP 服务也会执行
for _message in apply_network_settings():
    logger.info(_message)


class InterfaceError(Exception):
    """调用接口失败，附带对应的 HTTP 状态码；HTTP 路由与 MCP 工具共用同一套错误说明"""

    def __init__(self, message: str, status_code: int):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


# AKShare 自定义的异常不继承 requests 的异常类，需要单独对应状态码与处理建议；
# 未列出的异常（含 AkshareException 基类）仍按接口用法错误处理
AKSHARE_ERRORS = (
    (
        ak_exceptions.NetworkError,
        status.HTTP_502_BAD_GATEWAY,
        "访问上游数据源失败，请检查网络或代理设置（HTTP_PROXY/HTTPS_PROXY 环境变量，或启动参数 --proxy）：{e}",
    ),
    (
        ak_exceptions.RateLimitError,
        status.HTTP_429_TOO_MANY_REQUESTS,
        "上游数据源限制了访问频率，请稍后重试，或调大 --cache-ttl 减少重复请求：{e}",
    ),
    (
        ak_exceptions.InvalidParameterError,
        status.HTTP_400_BAD_REQUEST,
        "参数不合法：{e}，请通过 /api/interfaces/{item_id} 查看参数说明",
    ),
    (
        ak_exceptions.APIError,
        status.HTTP_502_BAD_GATEWAY,
        "上游数据源返回错误：{e}，请稍后重试",
    ),
    (
        ak_exceptions.DataParsingError,
        status.HTTP_502_BAD_GATEWAY,
        "解析上游数据失败：{e}，上游页面可能已改版，请升级 AKShare 到最新版本，仍有问题请到 AKShare 反馈：https://github.com/akfamily/akshare/issues",
    ),
)


def _unknown_param_message(func, item_id: str, params: Dict[str, str]) -> Optional[str]:
    """
    按函数签名检查参数名，返回错误说明；参数名均有效，或接口接受 **kwargs 无法检查时返回 None
    参数名写错时接口会抛出 TypeError，事先检查可以给出可用参数，也不会白白请求一次上游网站
    """
    try:
        signature = inspect.signature(func)
    except (TypeError, ValueError):
        return None
    accepted = signature.parameters.values()
    if any(p.kind == p.VAR_KEYWORD for p in accepted):
        return None
    names: List[str] = [
        p.name for p in accepted if p.kind in (p.POSITIONAL_OR_KEYWORD, p.KEYWORD_ONLY)
    ]
    unknown = [key for key in params if key not in names]
    if not unknown:
        return None
    message = f"接口 {item_id} 不支持参数 {'、'.join(unknown)}；可用参数：{'、'.join(names) or '无'}"
    if "timeout" in unknown:
        # AKShare 1.20.13 起各接口不再有 timeout 参数，超时统一由全局设置
        message += (
            "。超时请在启动 AKTools 时用 --timeout 或环境变量 AKTOOLS_TIMEOUT 设置"
        )
    return message + f"，参数说明见 /api/interfaces/{item_id}"


def fetch_dataframe(item_id: str, params: Dict[str, str]) -> Tuple[pd.DataFrame, str]:
    """
    调用 AKShare 接口获取数据，经过结果缓存与 AKShare 内部缓存清理
    AKShare 为同步请求，调用方以同步函数定义，由 uvicorn 的线程池支持并发访问
    :param item_id: 接口名，如 stock_zh_a_hist
    :type item_id: str
    :param params: 接口参数，值均为文本，如 {"symbol": "000001"}
    :type params: dict
    :return: 接口数据，以及是否来自结果缓存（hit 或 miss）
    :rtype: tuple
    :raises InterfaceError: 接口不存在、参数名无效、调用出错、返回为空或上游数据源不可达
    """
    if not is_interface(item_id):
        logger.info(f"未找到接口 {item_id}")
        raise InterfaceError(
            f"未找到该接口，请升级 AKShare 到最新版本并在文档中确认该接口的使用方式：{DOC_URL}",
            status.HTTP_404_NOT_FOUND,
        )
    unknown = _unknown_param_message(getattr(ak, item_id), item_id, params)
    if unknown:
        logger.info(unknown)
        raise InterfaceError(unknown, status.HTTP_400_BAD_REQUEST)
    akshare_janitor.maybe_clear()
    # 返回格式不影响数据本身，因此调用方不应把 _format 放进 params，JSON、CSV、Excel 共用同一份缓存
    cache_key = (item_id, tuple(sorted(params.items())))
    cached = result_cache.get(cache_key)
    if cached is not None:
        return cached, "hit"
    try:
        df = getattr(ak, item_id)(**params)
    except requests.exceptions.RequestException as e:
        # 网络、代理、连接、超时等上游数据源不可达的错误，与接口用法无关。
        # 返回 502 并提示排查网络/代理，避免误导用户去升级 AKShare。
        logger.info(f"接口 {item_id} 访问上游数据源失败：{e}")
        raise InterfaceError(
            f"访问上游数据源失败，请检查网络或代理设置（HTTP_PROXY/HTTPS_PROXY 环境变量，或启动参数 --proxy）：{e}",
            status.HTTP_502_BAD_GATEWAY,
        ) from e
    except tuple(error for error, _, _ in AKSHARE_ERRORS) as e:
        logger.info(f"调用接口 {item_id} 出错：{type(e).__name__}: {e}")
        for error, status_code, message in AKSHARE_ERRORS:
            if isinstance(e, error):
                raise InterfaceError(
                    message.format(e=e, item_id=item_id), status_code
                ) from e
    except Exception as e:
        logger.info(f"调用接口 {item_id} 出错：{e}")
        raise InterfaceError(
            f"调用接口出错 {e}，请升级 AKShare 到最新版本并在文档中确认该接口的使用方式：{DOC_URL}",
            status.HTTP_404_NOT_FOUND,
        ) from e
    if df is None:
        logger.info(f"接口 {item_id} 返回数据为空")
        raise InterfaceError(
            f"该接口返回数据为空，请确认参数是否正确：{DOC_URL}",
            status.HTTP_404_NOT_FOUND,
        )
    result_cache.set(cache_key, df)
    return df, "miss"
