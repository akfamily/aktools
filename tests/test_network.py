# -*- coding:utf-8 -*-
# !/usr/bin/env python
"""
Date: 2026/10/30 10:00
Desc: 全局代理与请求超时设置的测试
"""

import akshare as ak
import pytest

from aktools.core import network


@pytest.fixture
def recorder(monkeypatch):
    """替换 AKShare 的设置函数，记录调用而不改动真实的全局配置"""
    calls = {}
    monkeypatch.setattr(
        ak, "set_proxies", lambda proxies: calls.setdefault("proxies", proxies)
    )
    monkeypatch.setattr(
        ak, "set_timeout", lambda timeout: calls.setdefault("timeout", timeout)
    )
    return calls


def test_nothing_applied_when_unset(recorder):
    """未设置时不改动 AKShare 的默认行为：沿用默认超时与 HTTP_PROXY 等环境变量"""
    assert network.apply_network_settings({}) == []
    assert recorder == {}


def test_proxy_applies_to_http_and_https(recorder):
    messages = network.apply_network_settings(
        {"AKTOOLS_PROXY": "http://127.0.0.1:7890"}
    )
    assert recorder["proxies"] == {
        "http": "http://127.0.0.1:7890",
        "https": "http://127.0.0.1:7890",
    }
    assert any("http://127.0.0.1:7890" in m for m in messages)


def test_timeout_sets_read_timeout_with_fixed_connect_timeout(recorder):
    network.apply_network_settings({"AKTOOLS_TIMEOUT": "120"})
    assert recorder["timeout"] == (10, 120.0)


@pytest.mark.parametrize("value", ["abc", "0", "-5"])
def test_invalid_timeout_is_ignored(recorder, value):
    """取值无效时不设置，并给出提示，服务照常启动"""
    messages = network.apply_network_settings({"AKTOOLS_TIMEOUT": value})
    assert "timeout" not in recorder
    assert any("AKTOOLS_TIMEOUT" in m for m in messages)


def test_old_akshare_without_settings_is_skipped(monkeypatch):
    """AKShare 1.20.4 之前没有 set_proxies、set_timeout，此时跳过并提示升级"""
    monkeypatch.delattr(ak, "set_proxies", raising=False)
    monkeypatch.delattr(ak, "set_timeout", raising=False)
    messages = network.apply_network_settings(
        {"AKTOOLS_PROXY": "http://127.0.0.1:7890", "AKTOOLS_TIMEOUT": "30"}
    )
    assert len(messages) == 2
    assert all("1.20.4" in m for m in messages)


def test_applies_to_real_akshare_config():
    """与真实的 AKShare 配置联动；测试结束后恢复原值，避免影响其他测试"""
    old_proxies, old_timeout = ak.get_proxies(), ak.get_timeout()
    try:
        network.apply_network_settings(
            {"AKTOOLS_PROXY": "http://127.0.0.1:7890", "AKTOOLS_TIMEOUT": "30"}
        )
        assert ak.get_timeout() == (10, 30.0)
        assert ak.get_proxies()["https"] == "http://127.0.0.1:7890"
    finally:
        ak.set_proxies(old_proxies)
        ak.set_timeout(old_timeout)
