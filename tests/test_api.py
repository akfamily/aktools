# -*- coding:utf-8 -*-
# !/usr/bin/env python
"""
Date: 2026/10/28 10:00
Desc: 数据接口错误处理测试
"""

import akshare as ak
import requests

from aktools.core.api import call_interface


class _FakeRequest:
    def __init__(self, params=None):
        self.query_params = params or {}


def test_unknown_interface_returns_404():
    """接口名不存在时返回 404"""
    resp = call_interface("not_a_real_interface_xyz", _FakeRequest())
    assert resp.status_code == 404


def test_upstream_network_error_returns_502(monkeypatch):
    """上游数据源不可达（网络/代理错误）时返回 502，而不是误导用户升级 AKShare"""

    def _boom():
        raise requests.exceptions.ProxyError("Unable to connect to proxy")

    monkeypatch.setattr(ak, "aktools_fake_net", _boom, raising=False)
    resp = call_interface("aktools_fake_net", _FakeRequest())
    assert resp.status_code == 502
    assert "代理" in resp.body.decode("utf-8")


def test_other_call_error_returns_404(monkeypatch):
    """非网络类的调用错误仍按接口用法问题返回 404"""

    def _boom():
        raise ValueError("bad argument")

    monkeypatch.setattr(ak, "aktools_fake_err", _boom, raising=False)
    resp = call_interface("aktools_fake_err", _FakeRequest())
    assert resp.status_code == 404
