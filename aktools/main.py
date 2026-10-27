# -*- coding:utf-8 -*-
# !/usr/bin/env python
"""
Date: 2022/9/28 15:05
Desc: 主程序入口文件
"""

import akshare
import aktools
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from aktools.core.api import app_core, templates
from aktools.datasets import get_favicon_path, get_homepage_html
from aktools.login import app_user_login
from aktools.utils import get_latest_version
from aktools.schema.version import VersionBase

favicon_path = get_favicon_path(file="favicon.ico")
html_path = get_homepage_html(file="homepage.html")


app = FastAPI(
    title="欢迎访问 AKTools 为 AKShare 打造的 HTTP API 在线文档",
    description="AKTools 是 AKShare 的 HTTP API 工具, 主要目的是使 AKShare 的数据接口部署到服务器，从而让用户通过 HTTP 访问相关接口来获取所需要的数据",
    version=akshare.__version__,
    redoc_url=None,
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


@app.get(path="/", tags=["主页"], description="主要展示网站首页", summary="网站首页")
async def get_homepage(request: Request):
    return templates.TemplateResponse(
        request,
        "homepage.html",  # 此处的 homepage.html 可以自定义，主要采用 jinja2 模版
        context={
            "ip_address": request.headers["host"],
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
async def get_version():
    return {
        "ak_current_version": akshare.__version__,
        "at_current_version": aktools.__version__,
        "ak_latest_version": get_latest_version("akshare"),
        "at_latest_version": get_latest_version("aktools"),
    }


# 允许任意来源访问；认证通过 Authorization 头的 Bearer token 完成，不使用 cookie，
# 因此 allow_credentials 设为 False——通配来源与携带凭证不能并存，否则浏览器会拒绝跨域请求
origins = ["*"]

app.add_middleware(
    middleware_class=CORSMiddleware,
    allow_origins=origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(app_core, prefix="/api", tags=["数据接口"])
app.include_router(app_user_login, prefix="/auth", tags=["登录接口"])
