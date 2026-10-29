# -*- coding:utf-8 -*-
# /usr/bin/env python
"""
Date: 2024/1/12 22:05
Desc: HTTP 模式主文件
"""

import json
import logging
import os
from logging.handlers import TimedRotatingFileHandler

import akshare as ak
import requests
from fastapi import APIRouter, Request, status
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates

from aktools.datasets import get_pyscript_html, get_template_path

app_core = APIRouter()

DOC_URL = "https://akshare.akfamily.xyz"

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


def call_interface(item_id: str, request: Request) -> JSONResponse:
    """
    根据接口名与查询参数调用对应的 AKShare 接口并返回 JSON 数据
    AKShare 为同步请求，接口以同步函数定义，由 uvicorn 的线程池支持并发访问
    :param request: 请求信息，查询参数即接口参数，如 symbol=000001
    :type request: Request
    :param item_id: 接口名，如 stock_zh_a_hist
    :type item_id: str
    :return: 接口数据或错误信息
    :rtype: JSONResponse
    """
    if item_id not in dir(ak):
        logger.info(f"未找到接口 {item_id}")
        return _error_response(
            f"未找到该接口，请升级 AKShare 到最新版本并在文档中确认该接口的使用方式：{DOC_URL}"
        )
    # FastAPI 已对查询串完成 URL 解码，参数值按第一个 = 切分，cookie 等含 = 的值也能正确取出
    params = dict(request.query_params)
    try:
        received_df = getattr(ak, item_id)(**params)
        if received_df is None:
            logger.info(f"接口 {item_id} 返回数据为空")
            return _error_response(f"该接口返回数据为空，请确认参数是否正确：{DOC_URL}")
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
    logger.info(f"获取到 {item_id} 的数据")
    return JSONResponse(status_code=status.HTTP_200_OK, content=content)


@app_core.get(
    path="/public/{item_id}",
    description="公开接口",
    summary="该接口主要提供公开访问来获取数据",
)
def public_root(request: Request, item_id: str):
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


def generate_html_response():
    file_path = get_pyscript_html(file="akscript.html")
    with open(file_path, encoding="utf8") as f:
        html_content = f.read()
    return HTMLResponse(content=html_content, status_code=200)


short_path = get_template_path()
templates = Jinja2Templates(directory=short_path)


@app_core.get(
    path="/show-temp/{interface}",
    response_class=HTMLResponse,
    description="展示 PyScript",
    summary="该接口主要展示 PyScript 浏览器运行 Python 代码",
)
def akscript_temp(request: Request, interface: str):
    return templates.TemplateResponse(
        request,
        "akscript.html",
        context={
            "ip": request.headers["host"],
            "interface": interface,
        },
    )


@app_core.get(
    path="/show",
    response_class=HTMLResponse,
    description="展示 PyScript",
    summary="该接口主要展示 PyScript 浏览器运行 Python 代码",
)
def akscript():
    return generate_html_response()
