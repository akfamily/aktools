# -*- coding:utf-8 -*-
# !/usr/bin/env python
"""
Date: 2026/10/30 14:00
Desc: 可选访问令牌的测试
"""

import subprocess
import sys

import pytest
from fastapi.testclient import TestClient
from starlette.applications import Starlette
from starlette.responses import PlainTextResponse
from starlette.routing import Route

from aktools.core.auth import TokenAuthMiddleware, load_tokens


def _ok(request):
    return PlainTextResponse("ok")


def _client(tokens):
    app = Starlette(
        routes=[
            Route(path, _ok, methods=["GET", "POST", "OPTIONS"])
            for path in ["/", "/version", "/docs", "/api/public/x", "/mcp"]
        ]
    )
    app.add_middleware(TokenAuthMiddleware, tokens=tokens)
    return TestClient(app)


def test_load_tokens_splits_and_strips():
    assert load_tokens({}) == []
    assert load_tokens({"AKTOOLS_TOKEN": " "}) == []
    assert load_tokens({"AKTOOLS_TOKEN": "a1, b2 ,,c3"}) == ["a1", "b2", "c3"]


def test_no_token_configured_keeps_everything_open():
    """不设置令牌时行为与原来完全一致"""
    client = _client([])
    for path in ["/api/public/x", "/mcp"]:
        assert client.get(path).status_code == 200


@pytest.mark.parametrize("path", ["/api/public/x", "/mcp"])
def test_protected_paths_require_token(path):
    client = _client(["secret"])
    resp = client.get(path)
    assert resp.status_code == 401
    assert resp.headers["www-authenticate"] == "Bearer"
    assert "令牌" in resp.json()["error"]


@pytest.mark.parametrize("path", ["/", "/version", "/docs"])
def test_homepage_and_docs_stay_public(path):
    """主页、/version 与 /docs 只展示版本与使用说明，不提供数据，保持公开"""
    assert _client(["secret"]).get(path).status_code == 200


def test_bearer_header_accepted():
    client = _client(["secret"])
    for value in ["Bearer secret", "bearer secret"]:
        resp = client.get("/api/public/x", headers={"Authorization": value})
        assert resp.status_code == 200
    resp = client.get("/api/public/x", headers={"Authorization": "Bearer wrong"})
    assert resp.status_code == 401


def test_query_param_accepted():
    """Excel、Stata、浏览器等不便设置请求头的场景，可以在网址中带 _token"""
    client = _client(["secret"])
    assert client.get("/api/public/x?_token=secret").status_code == 200
    assert client.get("/api/public/x?_token=wrong").status_code == 401


def test_any_of_multiple_tokens_accepted():
    """多个令牌（如每人一个）中任意一个都可以访问，便于单独撤销"""
    client = _client(["alice", "bob"])
    for token in ["alice", "bob"]:
        assert client.get(f"/api/public/x?_token={token}").status_code == 200
    assert client.get("/api/public/x?_token=carol").status_code == 401


def test_cors_preflight_passes_without_token():
    """浏览器的跨域预检请求不会携带令牌，需要放行，否则网页无法调用接口"""
    resp = _client(["secret"]).options("/api/public/x")
    assert resp.status_code == 200


def test_main_app_enforces_token_from_env(tmp_path):
    """通过 AKTOOLS_TOKEN 启动的真实应用：数据接口与 /mcp 需要令牌，主页公开"""
    code = (
        "import aktools.main as m\n"
        "m.get_latest_version = lambda p: '0.0.0'\n"
        "from fastapi.testclient import TestClient\n"
        "init = {'jsonrpc': '2.0', 'id': 1, 'method': 'initialize', 'params': "
        "{'protocolVersion': '2025-06-18', 'capabilities': {}, "
        "'clientInfo': {'name': 't', 'version': '0'}}}\n"
        "h = {'Accept': 'application/json, text/event-stream'}\n"
        "auth = {**h, 'Authorization': 'Bearer secret'}\n"
        "with TestClient(m.app, base_url='http://127.0.0.1:8080', "
        "follow_redirects=False) as c:\n"
        "    print(c.get('/').status_code,\n"
        "          c.get('/api/interfaces/stock_zh_a_hist').status_code,\n"
        "          c.get('/api/interfaces/stock_zh_a_hist?_token=secret').status_code,\n"
        "          c.post('/mcp', json=init, headers=h).status_code,\n"
        "          c.post('/mcp', json=init, headers=auth).status_code)\n"
    )
    env = {**__import__("os").environ, "AKTOOLS_TOKEN": "secret"}
    out = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
        check=True,
        env=env,
        cwd=str(tmp_path),
    )
    assert out.stdout.split()[-5:] == ["200", "401", "200", "401", "200"]
