# -*- coding:utf-8 -*-
# !/usr/bin/env python
"""
Date: 2022/2/23 20:05
Desc: 主程序入口
"""
import akshare
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core import app_core
from login import app_user_login

app = FastAPI(
    title="欢迎来到为 AKShare 打造的 HTTP API 文档",
    description="AKTools 是 AKShare 的 HTTP API 工具, 主要目的是使 AKShare 的数据接口部署到本地从而通过 HTTP 访问来获取所需要的数据",
    version=akshare.__version__,
)

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(app_core, prefix="/api", tags=["数据接口"])
app.include_router(app_user_login, prefix="/auth", tags=["登录接口"])

if __name__ == "__main__":
    uvicorn.run("run:app", host="127.0.0.1", port=8080, reload=True, debug=True)
