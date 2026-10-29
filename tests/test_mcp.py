# -*- coding:utf-8 -*-
# !/usr/bin/env python
"""
Date: 2026/10/29 22:00
Desc: MCP 服务测试
工具调用使用 MCP SDK 的内存客户端，不经过网络；HTTP 挂载使用 TestClient
"""

import json
import subprocess
import sys

import akshare as ak
import pandas as pd
import pytest
from fastapi.testclient import TestClient
from mcp.client import Client
from starlette.applications import Starlette
from starlette.routing import Route

from aktools.mcp_server import build_mcp_app, mcp

INIT_REQUEST = {
    "jsonrpc": "2.0",
    "id": 1,
    "method": "initialize",
    "params": {
        "protocolVersion": "2025-06-18",
        "capabilities": {},
        "clientInfo": {"name": "test", "version": "0"},
    },
}
MCP_HEADERS = {"Accept": "application/json, text/event-stream"}


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
def fake_table(monkeypatch):
    """返回 250 行数据的假接口，用于验证行数截断"""

    def fake(symbol="000001"):
        return pd.DataFrame({"代码": [symbol] * 250, "序号": range(250)})

    monkeypatch.setattr(ak, "aktools_fake_table", fake, raising=False)
    return "aktools_fake_table"


def _payload(result):
    """取出工具返回的结构化结果"""
    assert not result.is_error, result.content
    if result.structured_content is not None:
        return result.structured_content.get("result", result.structured_content)
    return json.loads(result.content[0].text)


@pytest.mark.anyio
async def test_lists_three_generic_tools():
    async with Client(mcp) as client:
        tools = await client.list_tools()
    assert {t.name for t in tools.tools} == {
        "search_interfaces",
        "describe_interface",
        "get_data",
    }


@pytest.mark.anyio
async def test_search_interfaces():
    async with Client(mcp) as client:
        result = _payload(
            await client.call_tool("search_interfaces", {"keyword": "交易日历"})
        )
    names = {item["name"] for item in result["items"]}
    assert "tool_trade_date_hist_sina" in names
    assert result["total"] == len(result["items"])


@pytest.mark.anyio
async def test_search_interfaces_limits_results():
    """关键词很宽泛时只返回前 50 个，并告知总数，避免撑满助手的上下文"""
    async with Client(mcp) as client:
        result = _payload(
            await client.call_tool("search_interfaces", {"keyword": "stock"})
        )
    assert result["total"] > 50
    assert len(result["items"]) == 50


@pytest.mark.anyio
async def test_describe_interface():
    async with Client(mcp) as client:
        result = _payload(
            await client.call_tool("describe_interface", {"name": "stock_zh_a_hist"})
        )
    assert result["name"] == "stock_zh_a_hist"
    assert result["params"][0]["name"] == "symbol"


@pytest.mark.anyio
async def test_describe_unknown_interface_is_tool_error():
    async with Client(mcp) as client:
        result = await client.call_tool("describe_interface", {"name": "nope_xyz"})
    assert result.is_error
    assert "search_interfaces" in result.content[0].text


@pytest.mark.anyio
async def test_get_data_truncates_rows(fake_table):
    async with Client(mcp) as client:
        result = _payload(
            await client.call_tool(
                "get_data",
                {"name": fake_table, "params": {"symbol": 600519}, "max_rows": 10},
            )
        )
    assert result["total_rows"] == 250
    assert result["returned_rows"] == 10
    assert result["truncated"] is True
    assert result["columns"] == ["代码", "序号"]
    # 数字参数按文本传给 AKShare，与 HTTP 接口的行为一致
    assert result["rows"][0] == {"代码": "600519", "序号": 0}
    assert result["csv_url"] == f"/api/public/{fake_table}?symbol=600519&_format=csv"


@pytest.mark.anyio
async def test_get_data_unknown_interface_is_tool_error():
    async with Client(mcp) as client:
        result = await client.call_tool("get_data", {"name": "nope_xyz"})
    assert result.is_error
    assert "search_interfaces" in result.content[0].text


def _host_app(host: str) -> Starlette:
    """与 aktools.main 相同的挂载方式：由宿主应用的 lifespan 启动 MCP 会话管理器"""
    mcp_app, lifespan = build_mcp_app(host)
    return Starlette(routes=[Route("/mcp", endpoint=mcp_app)], lifespan=lifespan)


def test_http_accepts_localhost_when_listening_on_localhost():
    with TestClient(
        _host_app("127.0.0.1"), base_url="http://127.0.0.1:8080", follow_redirects=False
    ) as c:
        resp = c.post("/mcp", json=INIT_REQUEST, headers=MCP_HEADERS)
    assert resp.status_code == 200


def test_http_rejects_other_hosts_when_listening_on_localhost():
    """只监听本机时拒绝其他 Host，防止 DNS 重绑定攻击"""
    with TestClient(
        _host_app("127.0.0.1"), base_url="http://evil.example", follow_redirects=False
    ) as c:
        resp = c.post("/mcp", json=INIT_REQUEST, headers=MCP_HEADERS)
    assert resp.status_code == 421


def test_http_accepts_lan_host_when_listening_on_all_interfaces():
    with TestClient(
        _host_app("0.0.0.0"),
        base_url="http://192.168.1.10:8080",
        follow_redirects=False,
    ) as c:
        resp = c.post("/mcp", json=INIT_REQUEST, headers=MCP_HEADERS)
    assert resp.status_code == 200


def test_main_app_mounts_mcp():
    from aktools.main import app

    with TestClient(app, base_url="http://127.0.0.1:8080", follow_redirects=False) as c:
        resp = c.post("/mcp", json=INIT_REQUEST, headers=MCP_HEADERS)
        assert resp.status_code == 200
        # 原有的数据接口不受影响
        assert c.get("/api/interfaces/stock_zh_a_hist").status_code == 200


def test_main_app_works_without_mcp_installed():
    """未安装 mcp 时，服务照常启动，只是不提供 /mcp"""
    code = (
        "import sys; sys.modules['mcp'] = None\n"
        "from fastapi.testclient import TestClient\n"
        "from aktools.main import app\n"
        "c = TestClient(app, base_url='http://127.0.0.1:8080')\n"
        "print(c.get('/api/interfaces/stock_zh_a_hist').status_code, c.post('/mcp', json={}).status_code)"
    )
    out = subprocess.run(
        [sys.executable, "-c", code], capture_output=True, text=True, check=True
    )
    assert out.stdout.split()[-2:] == ["200", "404"]
