# -*- coding:utf-8 -*-
# !/usr/bin/env python
"""
Date: 2026/10/30 14:00
Desc: 可选的访问令牌
设置环境变量 AKTOOLS_TOKEN（或启动参数 --token）后，数据接口（/api/）与 /mcp 需要携带令牌：
    请求头 Authorization: Bearer <令牌>，适合程序与 MCP 客户端
    查询参数 _token=<令牌>，适合 Excel、Stata、浏览器等不便设置请求头的场景
多个令牌用逗号分隔，任意一个均可访问，便于每人一个、单独撤销。
主页、/version 与 /docs 只展示版本与使用说明，保持公开；未设置令牌时行为与原来一致。
这里只做共享令牌，不做用户登录：多人分别管理权限时，请在前面加 OAuth2 Proxy 等现成的认证网关
"""

import json
import os
import secrets
from typing import List, Mapping, Sequence
from urllib.parse import parse_qsl

TOKEN_ENV = "AKTOOLS_TOKEN"
# 查询参数中的令牌由 AKTools 处理，调用 AKShare 接口前会被移除
TOKEN_PARAM = "_token"
PROTECTED_PREFIXES = ("/api/", "/mcp")


def load_tokens(env: Mapping[str, str] = os.environ) -> List[str]:
    """从环境变量读取令牌，多个令牌用逗号分隔；未设置时返回空列表"""
    return [
        token.strip() for token in env.get(TOKEN_ENV, "").split(",") if token.strip()
    ]


def _matches(candidate: str, tokens: Sequence[str]) -> bool:
    """以恒定时间比较，避免通过响应耗时逐字符猜出令牌"""
    value = candidate.encode("utf-8")
    return any(secrets.compare_digest(value, t.encode("utf-8")) for t in tokens)


class TokenAuthMiddleware:
    """
    纯 ASGI 中间件：不读取请求体、不包装响应，/mcp 的流式响应不受影响
    """

    def __init__(self, app, tokens: Sequence[str]):
        self.app = app
        self.tokens = list(tokens)

    def _authorized(self, scope) -> bool:
        for name, value in scope.get("headers", []):
            if name == b"authorization":
                scheme, _, credential = value.decode("latin-1").partition(" ")
                if scheme.lower() == "bearer" and _matches(
                    credential.strip(), self.tokens
                ):
                    return True
        query = scope.get("query_string", b"").decode("latin-1")
        for key, value in parse_qsl(query, keep_blank_values=True):
            if key == TOKEN_PARAM and _matches(value, self.tokens):
                return True
        return False

    async def __call__(self, scope, receive, send):
        if (
            not self.tokens
            or scope["type"] != "http"
            # 浏览器的跨域预检请求不会携带令牌
            or scope["method"] == "OPTIONS"
            or not scope["path"].startswith(PROTECTED_PREFIXES)
            or self._authorized(scope)
        ):
            await self.app(scope, receive, send)
            return
        body = json.dumps(
            {
                "error": "需要访问令牌：请在请求头加上 Authorization: Bearer <令牌>，"
                f"或在网址中加上 {TOKEN_PARAM}=<令牌>"
            },
            ensure_ascii=False,
        ).encode("utf-8")
        await send(
            {
                "type": "http.response.start",
                "status": 401,
                "headers": [
                    (b"content-type", b"application/json"),
                    (b"content-length", str(len(body)).encode()),
                    (b"www-authenticate", b"Bearer"),
                ],
            }
        )
        await send({"type": "http.response.body", "body": body})
