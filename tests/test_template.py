# -*- coding:utf-8 -*-
# !/usr/bin/env python
"""
Date: 2026/10/27 20:00
Desc: 模板页面测试
Starlette 1.x 起 TemplateResponse 只接受 (request, name, context) 的调用方式，
旧写法会导致页面返回 500，见 https://github.com/akfamily/aktools/issues/239
"""

import anyio
import pytest
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
    # 主页展示 MCP 地址，方便直接填入 AI 助手
    assert "/mcp" in response.text


@pytest.mark.parametrize(
    "path", ["/api/show", "/api/show-temp/tool_trade_date_hist_sina"]
)
def test_pyscript_pages_removed(path) -> None:
    """PyScript 数据展示页已移除：它依赖外部 CDN、首次加载需下载数十 MB，取数请使用 /api/public"""
    assert client.get(path).status_code == 404


@pytest.mark.anyio
@pytest.mark.parametrize("path", ["/", "/version"])
async def test_slow_version_lookup_does_not_block_other_requests(monkeypatch, path):
    """
    查询 PyPI 最新版本是同步的网络请求，若在异步路由中直接执行会阻塞事件循环，
    内网等无法访问 PyPI 的环境中，其他请求（取数据、/mcp）都会跟着卡住
    """
    import time

    import httpx2

    def slow_lookup(package):
        time.sleep(1)
        return "0.0.0"

    monkeypatch.setattr(aktools.main, "get_latest_version", slow_lookup)
    finished = []
    transport = httpx2.ASGITransport(app=app)
    async with httpx2.AsyncClient(
        transport=transport, base_url="http://127.0.0.1:8080"
    ) as client:

        async def fetch(url):
            resp = await client.get(url)
            finished.append(url)
            return resp

        async with anyio.create_task_group() as tg:
            tg.start_soon(fetch, path)
            await anyio.sleep(0.1)
            tg.start_soon(fetch, "/api/interfaces/stock_zh_a_hist")
    assert finished == ["/api/interfaces/stock_zh_a_hist", path]


@pytest.fixture
def anyio_backend():
    return "asyncio"
