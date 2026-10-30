# -*- coding:utf-8 -*-
# !/usr/bin/env python
"""
Date: 2022/9/28 15:05
Desc: 主程序入口文件
"""

import os

import akshare
import aktools
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.templating import Jinja2Templates

from aktools.core.api import app_core
from aktools.core.auth import TokenAuthMiddleware, load_tokens
from aktools.datasets import get_favicon_path, get_homepage_html, get_template_path
from aktools.mcp_server import build_mcp_app
from aktools.utils import get_latest_version
from aktools.schema.version import VersionBase

favicon_path = get_favicon_path(file="favicon.ico")
html_path = get_homepage_html(file="homepage.html")
templates = Jinja2Templates(directory=get_template_path())

# MCP 服务的监听地址由命令行通过该环境变量传入；Gunicorn、Docker 部署时请按实际监听地址设置
HOST_ENV = "AKTOOLS_HOST"


mcp_app, mcp_lifespan = build_mcp_app(os.getenv(HOST_ENV, "127.0.0.1"))

app = FastAPI(
    title="欢迎访问 AKTools 为 AKShare 打造的 HTTP API 在线文档",
    description="AKTools 是 AKShare 的 HTTP API 工具：把 AKShare 的数据接口部署为 HTTP 服务，任何编程语言都可以通过 HTTP 获取财经数据。接口名与 AKShare 的函数名一致，参数以查询字符串传递，详见 [AKTools 文档](https://aktools.akfamily.xyz/) 与 [AKShare 数据字典](https://akshare.akfamily.xyz/data/index.html)",
    version=akshare.__version__,
    redoc_url=None,
    # Starlette 不会运行被挂载子应用的 lifespan，MCP 的会话管理器需要由主应用启动
    lifespan=mcp_lifespan,
)


@app.get(
    path="/favicon.ico",
    include_in_schema=False,
    description="获取 ico 的路径",
    summary="ico 的路径",
)
async def favicon() -> FileResponse:
    """
    返回自定义的 favicon
    替换 aktools/assets/images/favicon.ico 文件则可以替换 icon
    :return: favicon 的路径
    :rtype: FileResponse
    """
    return FileResponse(favicon_path)


# 主页与 /version 会同步查询 PyPI 上的最新版本，因此定义为普通函数，由线程池执行；
# 定义为 async 会阻塞事件循环，无法访问 PyPI 时其他请求（取数据、/mcp）都会跟着卡住
@app.get(path="/", tags=["主页"], description="主要展示网站首页", summary="网站首页")
def get_homepage(request: Request):
    return templates.TemplateResponse(
        request,
        "homepage.html",  # 此处的 homepage.html 可以自定义，主要采用 jinja2 模版
        context={
            "ip_address": request.headers["host"],
            # 含协议与路径前缀，经反向代理以 HTTPS 访问时为 https://…；
            # uvicorn 默认信任本机反向代理传来的 X-Forwarded-Proto
            "base_url": str(request.base_url).rstrip("/"),
            "ak_current_version": akshare.__version__,
            "at_current_version": aktools.__version__,
            "ak_latest_version": get_latest_version("akshare"),
            "at_latest_version": get_latest_version("aktools"),
        },
    )


@app.get(
    path="/version",
    tags=["版本"],
    description="获取 AKTools 和 AKShare 的版本",
    summary="获取开源库版本",
    response_model=VersionBase,
)
def get_version():
    return {
        "ak_current_version": akshare.__version__,
        "at_current_version": aktools.__version__,
        "ak_latest_version": get_latest_version("akshare"),
        "at_latest_version": get_latest_version("aktools"),
    }


# 允许任意来源访问，便于浏览器中的网页直接调用数据接口；服务不使用 cookie 等凭证，
# 因此 allow_credentials 设为 False——通配来源与携带凭证不能并存，否则浏览器会拒绝跨域请求
origins = ["*"]

# 可选的访问令牌（AKTOOLS_TOKEN），须先于 CORS 添加：后添加的中间件在外层，
# 这样未通过令牌校验的 401 响应同样带有跨域响应头，浏览器中的网页能读到错误说明
app.add_middleware(TokenAuthMiddleware, tokens=load_tokens())
app.add_middleware(
    middleware_class=CORSMiddleware,
    allow_origins=origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(app_core, prefix="/api", tags=["数据接口"])

# 精确路由而不是 mount：mount 会把 /mcp 重定向到 /mcp/，MCP 客户端不一定会跟随
app.add_route("/mcp", mcp_app, include_in_schema=False)
