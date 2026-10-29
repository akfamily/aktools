# -*- coding:utf-8 -*-
# /usr/bin/env python
"""
Date: 2024/1/12 22:05
Desc: HTTP 模式主文件
"""

import io
import json
import logging
import os
import tempfile
from typing import Dict, Tuple
from logging.handlers import TimedRotatingFileHandler

import akshare as ak
import akshare.exceptions as ak_exceptions
import pandas as pd
import requests
from fastapi import APIRouter, Query, Request, status
from fastapi.responses import HTMLResponse, JSONResponse, Response
from fastapi.templating import Jinja2Templates

from aktools.core.cache import (
    AKSHARE_CACHE_CLEAR_ENV,
    CACHE_TTL_ENV,
    DEFAULT_AKSHARE_CACHE_CLEAR,
    DEFAULT_CACHE_TTL,
    AkshareCacheJanitor,
    ResultCache,
    env_seconds,
)
from aktools.core.catalog import describe_interface, is_interface, list_interfaces
from aktools.datasets import get_template_path

app_core = APIRouter()

DOC_URL = "https://akshare.akfamily.xyz"
# /api/show 演示页使用的接口：无需参数、数据量小且较为稳定
DEMO_INTERFACE = "tool_trade_date_hist_sina"

# 返回格式由保留参数 _format 指定，调用 AKShare 接口前会被移除；
# AKShare 的接口参数均不以下划线开头，不会与之冲突
FORMAT_PARAM = "_format"
MEDIA_TYPES = {
    "json": "application/json",
    "csv": "text/csv; charset=utf-8",
    "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
}
# Excel 单个工作表最多 1048576 行，其中 1 行是表头
EXCEL_MAX_ROWS = 1048575
# 响应头，标明本次数据是否来自结果缓存：hit 或 miss
CACHE_HEADER = "X-AKTools-Cache"

result_cache = ResultCache(ttl=env_seconds(CACHE_TTL_ENV, DEFAULT_CACHE_TTL))
akshare_janitor = AkshareCacheJanitor(
    interval=env_seconds(AKSHARE_CACHE_CLEAR_ENV, DEFAULT_AKSHARE_CACHE_CLEAR)
)


def _create_log_handler(filename: str) -> TimedRotatingFileHandler:
    """
    按天轮转的日志文件，保留最近 7 天
    AI 助手以 stdio 方式启动 aktools-mcp 时，工作目录可能不可写（如 macOS 上的 /），
    此时改写到系统临时目录，避免服务因无法创建日志文件而启动失败
    :param filename: 日志文件路径
    :type filename: str
    :return: 日志处理器
    :rtype: TimedRotatingFileHandler
    """
    options = {"when": "midnight", "interval": 1, "backupCount": 7, "encoding": "utf-8"}
    try:
        return TimedRotatingFileHandler(filename=filename, **options)
    except OSError:
        fallback = os.path.join(tempfile.gettempdir(), os.path.basename(filename))
        return TimedRotatingFileHandler(filename=fallback, **options)


# 日志目录由环境变量指定；测试据此把日志写到临时目录，避免在仓库中留下日志文件
LOG_DIR_ENV = "AKTOOLS_LOG_DIR"
LOG_FILENAME = "aktools_log.log"


def _log_path() -> str:
    """
    日志文件路径：优先使用 AKTOOLS_LOG_DIR 指定的目录；
    Vercel 环境只有 /tmp 可写；其余情况写到当前工作目录
    :return: 日志文件路径
    :rtype: str
    """
    log_dir = os.getenv(LOG_DIR_ENV)
    if log_dir:
        return os.path.join(log_dir, LOG_FILENAME)
    if os.getenv("VERCEL") == "1":
        return os.path.join("/tmp", LOG_FILENAME)
    return LOG_FILENAME


logger = logging.getLogger("AKToolsLog")
logger.setLevel(logging.INFO)
handler = _create_log_handler(_log_path())
handler.setFormatter(
    logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
)
logger.addHandler(handler)


def _error_response(
    message: str, status_code: int = status.HTTP_404_NOT_FOUND
) -> JSONResponse:
    """构造统一的错误响应"""
    return JSONResponse(status_code=status_code, content={"error": message})


def _file_response(
    item_id: str, df: pd.DataFrame, output_format: str, cache_status: str
) -> Response:
    """
    把接口数据转为 CSV 或 Excel 文件下载
    :param item_id: 接口名，用作下载文件名
    :type item_id: str
    :param df: 接口返回的数据
    :type df: pandas.DataFrame
    :param output_format: csv 或 xlsx
    :type output_format: str
    :param cache_status: 数据是否来自结果缓存，hit 或 miss
    :type cache_status: str
    :return: 文件下载响应
    :rtype: Response
    """
    if output_format == "csv":
        # utf-8-sig 带 BOM，Excel 直接打开时中文列名不会乱码
        body = df.to_csv(index=False).encode("utf-8-sig")
    else:
        if len(df) > EXCEL_MAX_ROWS:
            return _error_response(
                f"数据共 {len(df)} 行，超过 Excel 单个工作表的上限，请改用 {FORMAT_PARAM}=csv",
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        # Excel 不支持带时区的时间，写入前去掉时区信息，保留当地时间
        df = df.copy()
        for column in df.columns:
            if isinstance(df[column].dtype, pd.DatetimeTZDtype):
                df[column] = df[column].dt.tz_localize(None)
        buffer = io.BytesIO()
        df.to_excel(buffer, index=False, engine="openpyxl")
        body = buffer.getvalue()
    logger.info(f"获取到 {item_id} 的数据，格式为 {output_format}")
    return Response(
        content=body,
        media_type=MEDIA_TYPES[output_format],
        headers={
            "Content-Disposition": f'attachment; filename="{item_id}.{output_format}"',
            CACHE_HEADER: cache_status,
        },
    )


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
        "访问上游数据源失败，请检查网络或代理设置（如 HTTP_PROXY/HTTPS_PROXY 环境变量）：{e}",
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
    :raises InterfaceError: 接口不存在、调用出错、返回为空或上游数据源不可达
    """
    if not is_interface(item_id):
        logger.info(f"未找到接口 {item_id}")
        raise InterfaceError(
            f"未找到该接口，请升级 AKShare 到最新版本并在文档中确认该接口的使用方式：{DOC_URL}",
            status.HTTP_404_NOT_FOUND,
        )
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
            f"访问上游数据源失败，请检查网络或代理设置（如 HTTP_PROXY/HTTPS_PROXY 环境变量）：{e}",
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


def call_interface(item_id: str, request: Request) -> Response:
    """
    根据接口名与查询参数调用对应的 AKShare 接口并返回数据
    默认返回 JSON；查询参数 _format=csv 或 _format=xlsx 时返回文件下载
    :param request: 请求信息，查询参数即接口参数，如 symbol=000001
    :type request: Request
    :param item_id: 接口名，如 stock_zh_a_hist
    :type item_id: str
    :return: 接口数据或错误信息
    :rtype: Response
    """
    # FastAPI 已对查询串完成 URL 解码，参数值按第一个 = 切分，cookie 等含 = 的值也能正确取出
    params = dict(request.query_params)
    output_format = params.pop(FORMAT_PARAM, "json").lower()
    # 先校验格式再调用接口，避免格式写错时白白请求一次上游网站
    if output_format not in MEDIA_TYPES:
        return _error_response(
            f"不支持的返回格式 {output_format}，{FORMAT_PARAM} 可选值为：{'、'.join(MEDIA_TYPES)}",
            status_code=status.HTTP_400_BAD_REQUEST,
        )
    try:
        df, cache_status = fetch_dataframe(item_id, params)
    except InterfaceError as e:
        return _error_response(e.message, status_code=e.status_code)
    try:
        if output_format != "json":
            return _file_response(item_id, df, output_format, cache_status)
        content = json.loads(df.to_json(orient="records", date_format="iso"))
    except Exception as e:
        logger.info(f"接口 {item_id} 的数据转换为 {output_format} 失败：{e}")
        return _error_response(
            f"数据转换为 {output_format} 格式失败：{e}，可以改用 {FORMAT_PARAM}=json 获取数据",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
    logger.info(f"获取到 {item_id} 的数据，缓存 {cache_status}")
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content=content,
        headers={CACHE_HEADER: cache_status},
    )


@app_core.get(
    path="/public/{item_id}",
    description="调用与 item_id 同名的 AKShare 接口，接口参数以查询字符串传递，如 ?symbol=000001",
    summary="获取数据",
)
def public_root(
    request: Request,
    item_id: str,
    # 只用于在 /docs 中展示该参数；实际取值由 call_interface 从查询参数中读取
    output_format: str = Query(
        "json",
        alias=FORMAT_PARAM,
        description="返回格式：json（默认）、csv 或 xlsx，csv 与 xlsx 以文件形式下载",
    ),
):
    """
    公开接口，接收接口名与参数并返回 JSON 数据
    :param request: 请求信息
    :type request: Request
    :param item_id: 接口名，如 stock_zh_a_hist
    :type item_id: str
    :return: 指定接口名与参数的数据
    :rtype: JSONResponse
    """
    return call_interface(item_id, request)


@app_core.get(
    path="/interfaces",
    description="列出全部 AKShare 数据接口的名称与中文标题，可用 q 按接口名或标题过滤",
    summary="接口目录",
)
def interfaces(
    q: str = Query("", description="关键词，匹配接口名或中文标题，如 历史行情"),
):
    return list_interfaces(q)


@app_core.get(
    path="/interfaces/{item_id}",
    description="返回接口的标题、数据源地址、调用地址，以及各参数的默认值、类型和说明",
    summary="接口参数说明",
)
def interface_detail(item_id: str):
    info = describe_interface(item_id)
    if info is None:
        return _error_response(
            f"未找到该接口，请升级 AKShare 到最新版本或通过 /api/interfaces 查找接口名：{DOC_URL}"
        )
    return info


short_path = get_template_path()
templates = Jinja2Templates(directory=short_path)


def _render_akscript(request: Request, interface: str):
    """用 PyScript 页面模板渲染指定接口的数据展示页"""
    return templates.TemplateResponse(
        request,
        "akscript.html",
        context={
            "ip": request.headers["host"],
            "interface": interface,
        },
    )


@app_core.get(
    path="/show-temp/{interface}",
    response_class=HTMLResponse,
    description="用 PyScript 在浏览器中获取并展示指定接口的数据，并提供 JSON 下载",
    summary="PyScript 数据展示页",
)
def akscript_temp(request: Request, interface: str):
    return _render_akscript(request, interface)


@app_core.get(
    path="/show",
    response_class=HTMLResponse,
    description=f"PyScript 数据展示页的演示，展示 {DEMO_INTERFACE} 接口的数据",
    summary="PyScript 数据展示页演示",
)
def akscript(request: Request):
    return _render_akscript(request, DEMO_INTERFACE)
