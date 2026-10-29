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
from logging.handlers import TimedRotatingFileHandler

import akshare as ak
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

# 按天轮转的日志记录器，保留最近 7 天；Vercel 环境只有 /tmp 可写
logger = logging.getLogger("AKToolsLog")
logger.setLevel(logging.INFO)
handler = TimedRotatingFileHandler(
    filename="/tmp/aktools_log.log"
    if os.getenv("VERCEL") == "1"
    else "aktools_log.log",
    when="midnight",
    interval=1,
    backupCount=7,
    encoding="utf-8",
)
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


def call_interface(item_id: str, request: Request) -> JSONResponse:
    """
    根据接口名与查询参数调用对应的 AKShare 接口并返回数据
    默认返回 JSON；查询参数 _format=csv 或 _format=xlsx 时返回文件下载
    AKShare 为同步请求，接口以同步函数定义，由 uvicorn 的线程池支持并发访问
    :param request: 请求信息，查询参数即接口参数，如 symbol=000001
    :type request: Request
    :param item_id: 接口名，如 stock_zh_a_hist
    :type item_id: str
    :return: 接口数据或错误信息
    :rtype: Response
    """
    if not is_interface(item_id):
        logger.info(f"未找到接口 {item_id}")
        return _error_response(
            f"未找到该接口，请升级 AKShare 到最新版本并在文档中确认该接口的使用方式：{DOC_URL}"
        )
    # FastAPI 已对查询串完成 URL 解码，参数值按第一个 = 切分，cookie 等含 = 的值也能正确取出
    params = dict(request.query_params)
    output_format = params.pop(FORMAT_PARAM, "json").lower()
    if output_format not in MEDIA_TYPES:
        return _error_response(
            f"不支持的返回格式 {output_format}，{FORMAT_PARAM} 可选值为：{'、'.join(MEDIA_TYPES)}",
            status_code=status.HTTP_400_BAD_REQUEST,
        )
    akshare_janitor.maybe_clear()
    # 返回格式不影响数据本身，因此不计入缓存键，JSON、CSV、Excel 共用同一份缓存
    cache_key = (item_id, tuple(sorted(params.items())))
    try:
        received_df = result_cache.get(cache_key)
        cache_status = "hit" if received_df is not None else "miss"
        if received_df is None:
            received_df = getattr(ak, item_id)(**params)
            if received_df is None:
                logger.info(f"接口 {item_id} 返回数据为空")
                return _error_response(
                    f"该接口返回数据为空，请确认参数是否正确：{DOC_URL}"
                )
            result_cache.set(cache_key, received_df)
        if output_format != "json":
            return _file_response(item_id, received_df, output_format, cache_status)
        content = json.loads(received_df.to_json(orient="records", date_format="iso"))
    except requests.exceptions.RequestException as e:
        # 网络、代理、连接、超时等上游数据源不可达的错误，与接口用法无关。
        # 返回 502 并提示排查网络/代理，避免误导用户去升级 AKShare。
        logger.info(f"接口 {item_id} 访问上游数据源失败：{e}")
        return _error_response(
            f"访问上游数据源失败，请检查网络或代理设置（如 HTTP_PROXY/HTTPS_PROXY 环境变量）：{e}",
            status_code=status.HTTP_502_BAD_GATEWAY,
        )
    except Exception as e:
        logger.info(f"调用接口 {item_id} 出错：{e}")
        return _error_response(
            f"调用接口出错 {e}，请升级 AKShare 到最新版本并在文档中确认该接口的使用方式：{DOC_URL}"
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
