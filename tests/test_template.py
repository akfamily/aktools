# -*- coding:utf-8 -*-
# !/usr/bin/env python
"""
Date: 2026/10/27 20:00
Desc: 模板页面测试
Starlette 1.x 起 TemplateResponse 只接受 (request, name, context) 的调用方式，
旧写法会导致页面返回 500，见 https://github.com/akfamily/aktools/issues/239
"""

from fastapi.testclient import TestClient

import aktools.main
from aktools.main import app

client = TestClient(app)


def test_homepage(monkeypatch) -> None:
    """
    测试主页可以正常渲染；主页会联网查询最新版本，此处替换为固定值，避免测试依赖网络
    """
    monkeypatch.setattr(aktools.main, "get_latest_version", lambda package: "0.0.0")
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]


def test_show_temp() -> None:
    """
    测试 PyScript 模板页面可以正常渲染
    """
    response = client.get("/api/show-temp/stock_zh_a_hist")
    assert response.status_code == 200
    assert "stock_zh_a_hist" in response.text


def test_show_renders_default_interface() -> None:
    """
    /api/show 以示例接口渲染 PyScript 页面，不能把未渲染的模板原文（{{ ip }} 等）返回给浏览器
    """
    response = client.get("/api/show")
    assert response.status_code == 200
    assert "{{" not in response.text
    assert "/api/public/tool_trade_date_hist_sina" in response.text
