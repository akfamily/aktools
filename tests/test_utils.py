# -*- coding:utf-8 -*-
# !/usr/bin/env python
"""
Date: 2026/10/27 20:00
Desc: 工具函数测试
"""

import requests

from aktools import utils
from aktools.utils import FALLBACK_VERSION, get_latest_version


class _FakeResponse:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        pass

    def json(self):
        return self._payload


def test_get_latest_version_success(monkeypatch):
    """正常获取时返回 PyPI 的版本号，并写入缓存"""
    utils._version_cache.clear()
    monkeypatch.setattr(
        requests, "get", lambda *a, **k: _FakeResponse({"info": {"version": "1.2.3"}})
    )
    assert get_latest_version("akshare") == "1.2.3"
    assert utils._version_cache["akshare"] == "1.2.3"


def test_get_latest_version_network_error_returns_fallback(monkeypatch):
    """网络异常时返回占位版本，而不是向上抛出导致主页 500"""
    utils._version_cache.clear()

    def _raise(*a, **k):
        raise requests.exceptions.ConnectTimeout("timeout")

    monkeypatch.setattr(requests, "get", _raise)
    assert get_latest_version("akshare") == FALLBACK_VERSION


def test_get_latest_version_failure_not_cached(monkeypatch):
    """失败不写入缓存：网络恢复后下次请求应重新尝试并拿到真实版本"""
    utils._version_cache.clear()

    def _raise(*a, **k):
        raise requests.exceptions.ConnectionError("down")

    monkeypatch.setattr(requests, "get", _raise)
    assert get_latest_version("aktools") == FALLBACK_VERSION
    assert "aktools" not in utils._version_cache

    monkeypatch.setattr(
        requests, "get", lambda *a, **k: _FakeResponse({"info": {"version": "0.0.92"}})
    )
    assert get_latest_version("aktools") == "0.0.92"
