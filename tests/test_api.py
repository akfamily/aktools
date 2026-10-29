# -*- coding:utf-8 -*-
# !/usr/bin/env python
"""
Date: 2026/10/28 10:00
Desc: 数据接口错误处理测试
"""

import codecs
import io

import akshare as ak
import openpyxl
import pandas as pd
import pytest
import requests

import aktools.core.api as api

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


def _fake_df():
    """不带参数的假接口：若 _format 被误传给 AKShare 接口，调用会直接报错"""
    return pd.DataFrame(
        {
            "日期": pd.to_datetime(["2024-01-25", "2024-01-26"]).tz_localize(
                "Asia/Shanghai"
            ),
            "收盘": [9.5, 9.62],
        }
    )


@pytest.fixture
def fake_interface(monkeypatch):
    monkeypatch.setattr(ak, "aktools_fake_df", _fake_df, raising=False)
    return "aktools_fake_df"


def test_default_format_is_json(fake_interface):
    resp = call_interface(fake_interface, _FakeRequest())
    assert resp.status_code == 200
    assert resp.media_type == "application/json"
    assert '"收盘":9.5' in resp.body.decode("utf-8")


def test_csv_format(fake_interface):
    resp = call_interface(fake_interface, _FakeRequest({"_format": "csv"}))
    assert resp.status_code == 200
    assert resp.media_type.startswith("text/csv")
    assert f'filename="{fake_interface}.csv"' in resp.headers["content-disposition"]
    # 带 BOM，Excel 直接打开时中文列名不会乱码
    assert resp.body.startswith(codecs.BOM_UTF8)
    text = resp.body.decode("utf-8-sig")
    assert text.splitlines()[0] == "日期,收盘"
    assert len(text.splitlines()) == 3


def test_xlsx_format(fake_interface):
    resp = call_interface(fake_interface, _FakeRequest({"_format": "xlsx"}))
    assert resp.status_code == 200
    assert "spreadsheetml" in resp.media_type
    assert f'filename="{fake_interface}.xlsx"' in resp.headers["content-disposition"]
    rows = list(openpyxl.load_workbook(io.BytesIO(resp.body)).active.values)
    assert rows[0] == ("日期", "收盘")
    assert len(rows) == 3
    assert rows[1][1] == 9.5


def test_invalid_format_returns_400(fake_interface):
    resp = call_interface(fake_interface, _FakeRequest({"_format": "pdf"}))
    assert resp.status_code == 400
    body = resp.body.decode("utf-8")
    assert "json" in body and "csv" in body and "xlsx" in body


def test_xlsx_too_many_rows_suggests_csv(fake_interface, monkeypatch):
    monkeypatch.setattr(api, "EXCEL_MAX_ROWS", 1)
    resp = call_interface(fake_interface, _FakeRequest({"_format": "xlsx"}))
    assert resp.status_code == 400
    assert "csv" in resp.body.decode("utf-8")


def test_format_param_via_http(fake_interface):
    """经过完整的 HTTP 路由，_format 同样生效"""
    from fastapi.testclient import TestClient

    from aktools.main import app

    resp = TestClient(app).get(f"/api/public/{fake_interface}?_format=csv")
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("text/csv")
