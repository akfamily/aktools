# -*- coding:utf-8 -*-
# !/usr/bin/env python
"""
Date: 2026/10/28 10:00
Desc: 数据接口错误处理测试
"""

import codecs
import datetime
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


def test_format_conversion_error_returns_readable_message(monkeypatch):
    """
    数据无法写入 Excel 时返回说明，而不是未处理的 500 错误。
    object 列中的带时区时间不会被统一去掉时区，openpyxl 会拒绝写入
    """
    aware = datetime.datetime(2024, 1, 1, tzinfo=datetime.timezone.utc)
    monkeypatch.setattr(
        ak,
        "aktools_fake_mixed",
        lambda: pd.DataFrame({"时间": pd.Series([aware, "2024-01-02"], dtype=object)}),
        raising=False,
    )
    resp = call_interface("aktools_fake_mixed", _FakeRequest({"_format": "xlsx"}))
    assert resp.status_code == 500
    assert "_format=json" in resp.body.decode("utf-8")


def test_log_handler_falls_back_when_directory_not_writable(tmp_path):
    """
    AI 助手以 stdio 方式启动时，工作目录可能不可写（如 macOS 上的 /），
    日志文件无法创建时应改写到系统临时目录，而不是让服务启动失败
    """
    import tempfile

    unwritable = tmp_path / "missing-dir" / "aktools_log.log"
    handler = api._create_log_handler(str(unwritable))
    try:
        assert handler.baseFilename.startswith(tempfile.gettempdir())
    finally:
        handler.close()


def test_log_path_follows_log_dir_env(monkeypatch, tmp_path):
    """AKTOOLS_LOG_DIR 指定日志目录；未设置时写到当前工作目录"""
    monkeypatch.setenv("AKTOOLS_LOG_DIR", str(tmp_path))
    assert api._log_path() == str(tmp_path / "aktools_log.log")
    monkeypatch.delenv("AKTOOLS_LOG_DIR")
    monkeypatch.delenv("VERCEL", raising=False)
    assert api._log_path() == "aktools_log.log"


def test_tests_do_not_write_log_into_repository():
    """测试运行时日志写到临时目录，不在仓库中留下 aktools_log.log 及其轮转文件"""
    import pathlib

    repo_root = pathlib.Path(__file__).resolve().parent.parent
    log_file = pathlib.Path(api.handler.baseFilename).resolve()
    assert repo_root not in log_file.parents
