# -*- coding:utf-8 -*-
# !/usr/bin/env python
"""
Date: 2022/2/23 20:05
Desc: 主程序入口
"""
import uvicorn
from fastapi import FastAPI

from core import app_core
from login import app_user_login

app = FastAPI()

app.include_router(app_core, prefix="/api", tags=["数据接口"])
app.include_router(app_user_login, prefix="/auth", tags=["登录接口"])

if __name__ == "__main__":
    uvicorn.run("run:app", host="127.0.0.1", port=8080, reload=True, debug=True)
