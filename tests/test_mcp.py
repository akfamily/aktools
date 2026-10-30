# -*- coding:utf-8 -*-
# !/usr/bin/env python
"""
Date: 2026/10/29 22:00
Desc: MCP 服务测试
工具调用使用 MCP SDK 的内存客户端，不经过网络；HTTP 挂载使用 TestClient
"""

import json
import logging
import subprocess
import sys
import threading

import akshare as ak
import pandas as pd
import pytest
from fastapi.testclient import TestClient
from mcp.client import Client
from mcp.client.stdio import StdioServerParameters
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


# stdio 子进程中运行的脚本：换上离线的假接口，并故意向 stdout 打印，
# 验证 AKShare 接口中的 print 不会破坏 stdio 通信
STDIO_SERVER_SCRIPT = """
import akshare as ak
import pandas as pd

def fake(symbol="000001"):
    print("akshare 接口中的调试输出")
    return pd.DataFrame({"代码": [symbol] * 3})

ak.aktools_fake_stdio = fake
from aktools.mcp_server import main
main()
"""


@pytest.mark.anyio
async def test_stdio_server_end_to_end(tmp_path):
    server = StdioServerParameters(
        command=sys.executable,
        args=["-c", STDIO_SERVER_SCRIPT],
        cwd=str(tmp_path),
    )
    async with Client(server) as client:
        tools = await client.list_tools()
        assert {t.name for t in tools.tools} == {
            "search_interfaces",
            "describe_interface",
            "get_data",
        }
        search = _payload(
            await client.call_tool("search_interfaces", {"keyword": "交易日历"})
        )
        assert search["total"] >= 1
        data = _payload(
            await client.call_tool(
                "get_data", {"name": "aktools_fake_stdio", "params": {"symbol": "1"}}
            )
        )
    assert data["rows"] == [{"代码": "1"}] * 3
    # stdio 模式下没有 HTTP 服务，不提供下载地址
    assert data["csv_url"] is None


def test_stdio_stdout_carries_only_protocol_messages(tmp_path):
    """
    stdout 中只能有 JSON-RPC 消息。AKShare 接口中 print 的内容会先进入 Python 的输出缓冲区，
    若在会话结束、SDK 恢复 stdout 之后才写出，就会混入协议通道，因此逐行检查原始输出
    """
    messages = [
        INIT_REQUEST,
        {"jsonrpc": "2.0", "method": "notifications/initialized"},
        {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {"name": "get_data", "arguments": {"name": "aktools_fake_stdio"}},
        },
    ]
    proc = subprocess.Popen(
        [sys.executable, "-c", STDIO_SERVER_SCRIPT],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=str(tmp_path),
    )
    # 超时保护：服务端卡住时结束进程，readline 随之返回，测试以失败告终而不是挂起
    watchdog = threading.Timer(120, proc.kill)
    watchdog.start()
    try:
        for message in messages:
            proc.stdin.write((json.dumps(message) + "\n").encode("utf-8"))
        proc.stdin.flush()
        # 像真实客户端一样，收到两条响应之后才关闭 stdin；
        # 过早关闭会让服务端在取数完成前退出，测试结果不稳定
        responses = [proc.stdout.readline() for _ in range(2)]
        proc.stdin.close()
        # 会话结束后剩余的 stdout 必须为空：缓冲区中残留的 print 输出正是在退出时写出的
        rest, stderr = proc.stdout.read(), proc.stderr.read()
        proc.wait()
    finally:
        watchdog.cancel()
    for line in responses:
        assert json.loads(line.decode("utf-8"))["jsonrpc"] == "2.0"
    assert rest == b""
    assert "akshare 接口中的调试输出" in stderr.decode("utf-8", errors="replace")


def test_aktools_mcp_command_is_registered():
    """pip 安装后提供 aktools-mcp 命令，供 AI 助手以 stdio 方式启动"""
    from importlib.metadata import entry_points

    scripts = {ep.name: ep.value for ep in entry_points(group="console_scripts")}
    assert scripts.get("aktools-mcp") == "aktools.mcp_server:main"


def test_importing_mcp_server_leaves_root_logging_untouched():
    """
    MCP SDK 创建 MCPServer 时会调用 logging.basicConfig，给根日志记录器加上控制台输出。
    AKTools 必装 MCP，不能因此改变 python -m aktools 的控制台输出，也不能接管嵌入方程序的日志配置
    """
    code = (
        "import logging\n"
        "import aktools.main\n"
        "root = logging.getLogger()\n"
        "print(len(root.handlers), root.level)"
    )
    out = subprocess.run(
        [sys.executable, "-c", code], capture_output=True, text=True, check=True
    )
    assert out.stdout.split() == ["0", str(logging.WARNING)]


@pytest.mark.anyio
async def test_get_data_reports_akshare_rate_limit(monkeypatch):
    """MCP 与 HTTP 共用错误说明：上游限流时助手看到的是限流提示，而不是升级 AKShare"""
    import akshare.exceptions as ak_exceptions

    def boom():
        raise ak_exceptions.RateLimitError("请求过于频繁")

    monkeypatch.setattr(ak, "aktools_fake_rate_limit", boom, raising=False)
    async with Client(mcp) as client:
        result = await client.call_tool("get_data", {"name": "aktools_fake_rate_limit"})
    assert result.is_error
    assert "稍后重试" in result.content[0].text


@pytest.mark.anyio
async def test_get_data_reports_unknown_param(monkeypatch):
    """MCP 与 HTTP 共用参数检查：参数名写错时助手能看到支持的参数，从而自行改正"""

    def fake(symbol="000001"):
        return pd.DataFrame({"代码": [symbol]})

    monkeypatch.setattr(ak, "aktools_fake_param", fake, raising=False)
    async with Client(mcp) as client:
        result = await client.call_tool(
            "get_data", {"name": "aktools_fake_param", "params": {"symol": "1"}}
        )
    assert result.is_error
    assert "不支持参数 symol" in result.content[0].text
    assert "可用参数：symbol" in result.content[0].text
