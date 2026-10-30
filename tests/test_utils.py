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
    assert "akshare" in utils._version_cache


def test_get_latest_version_network_error_returns_fallback(monkeypatch):
    """网络异常时返回占位版本，而不是向上抛出导致主页 500"""
    utils._version_cache.clear()

    def _raise(*a, **k):
        raise requests.exceptions.ConnectTimeout("timeout")

    monkeypatch.setattr(requests, "get", _raise)
    assert get_latest_version("akshare") == FALLBACK_VERSION


class _Clock:
    def __init__(self):
        self.now = 1000.0

    def __call__(self):
        return self.now


def test_get_latest_version_success_expires(monkeypatch):
    """成功结果缓存 1 小时：服务长期运行时，过期后重新查询，最新版本不会一直停在启动时"""
    utils._version_cache.clear()
    clock = _Clock()
    monkeypatch.setattr(utils, "_clock", clock)
    versions = iter(["1.0.0", "1.0.1"])
    monkeypatch.setattr(
        requests,
        "get",
        lambda *a, **k: _FakeResponse({"info": {"version": next(versions)}}),
    )
    assert get_latest_version("aktools") == "1.0.0"
    clock.now += utils.SUCCESS_TTL - 1
    assert get_latest_version("aktools") == "1.0.0"
    clock.now += 2
    assert get_latest_version("aktools") == "1.0.1"


def test_get_latest_version_failure_cached_briefly(monkeypatch):
    """
    失败结果短暂缓存：内网或断网时不必每次打开主页都等待超时；
    过了较短的有效期后重新尝试，网络恢复后能拿到真实版本
    """
    utils._version_cache.clear()
    clock = _Clock()
    monkeypatch.setattr(utils, "_clock", clock)
    calls = []

    def _raise(*a, **k):
        calls.append(1)
        raise requests.exceptions.ConnectionError("down")

    monkeypatch.setattr(requests, "get", _raise)
    assert get_latest_version("aktools") == FALLBACK_VERSION
    assert get_latest_version("aktools") == FALLBACK_VERSION
    assert calls == [1]

    clock.now += utils.FAILURE_TTL + 1
    monkeypatch.setattr(
        requests, "get", lambda *a, **k: _FakeResponse({"info": {"version": "0.0.92"}})
    )
    assert get_latest_version("aktools") == "0.0.92"
