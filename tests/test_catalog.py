# -*- coding:utf-8 -*-
# !/usr/bin/env python
"""
Date: 2026/10/29 20:00
Desc: 接口目录与参数说明测试
只读取 AKShare 接口的签名与 docstring，不实际调用接口，因此无需联网
"""

import inspect
import types

import akshare as ak
from fastapi.testclient import TestClient

from aktools.core.catalog import describe_interface, parse_docstring
from aktools.main import app

client = TestClient(app)


def test_parse_docstring_extracts_title_source_and_params() -> None:
    doc = """
    东方财富网-沪深京 A 股-每日行情
    https://quote.eastmoney.com/concept/sh603777.html
    :param symbol: 股票代码
    :type symbol: str
    :param adjust: choice of {"qfq": "前复权", "": "不复权"}
    :type adjust: str
    :return: 每日行情
    :rtype: pandas.DataFrame
    """
    parsed = parse_docstring(inspect.cleandoc(doc))
    assert parsed["title"] == "东方财富网-沪深京 A 股-每日行情"
    assert parsed["source_url"] == "https://quote.eastmoney.com/concept/sh603777.html"
    assert parsed["params"]["symbol"] == {"description": "股票代码", "type": "str"}
    assert parsed["params"]["adjust"]["description"].startswith("choice of")


def test_parse_docstring_without_source_url() -> None:
    parsed = parse_docstring("新浪财经-交易日历\n:return: 交易日历")
    assert parsed["title"] == "新浪财经-交易日历"
    assert parsed["source_url"] == ""
    assert parsed["params"] == {}


def test_list_interfaces_contains_only_callable_interfaces() -> None:
    response = client.get("/api/interfaces")
    assert response.status_code == 200
    items = response.json()
    names = {item["name"] for item in items}
    assert "stock_zh_a_hist" in names
    title = next(i["title"] for i in items if i["name"] == "stock_zh_a_hist")
    assert title == inspect.getdoc(ak.stock_zh_a_hist).splitlines()[0].strip()
    # AKShare 顶层还导出了子模块和类，它们不是数据接口，不应出现在目录中
    module_names = {n for n in dir(ak) if isinstance(getattr(ak, n), types.ModuleType)}
    assert module_names and not names & module_names
    assert not any(name.startswith("_") for name in names)


def test_list_interfaces_filters_by_keyword() -> None:
    response = client.get("/api/interfaces", params={"q": "STOCK_ZH_A_HIST"})
    assert response.status_code == 200
    items = response.json()
    assert "stock_zh_a_hist" in {item["name"] for item in items}
    assert all(
        "stock_zh_a_hist" in item["name"] or "stock_zh_a_hist" in item["title"].lower()
        for item in items
    )


def test_describe_real_interface() -> None:
    response = client.get("/api/interfaces/stock_zh_a_hist")
    assert response.status_code == 200
    info = response.json()
    assert info["name"] == "stock_zh_a_hist"
    assert info["url"] == "/api/public/stock_zh_a_hist"
    assert info["source_url"].startswith("http")
    expected = list(inspect.signature(ak.stock_zh_a_hist).parameters)
    assert [p["name"] for p in info["params"]] == expected
    symbol = info["params"][0]
    assert symbol["default"] == "000001"
    assert symbol["required"] is False
    assert symbol["type"] == "str"
    assert symbol["description"]
    assert info["doc"] == inspect.getdoc(ak.stock_zh_a_hist)


def test_describe_interface_without_docstring(monkeypatch) -> None:
    """没有 docstring 的接口仍按签名返回参数；没有默认值的参数标记为必填"""

    def fake(code, limit: int = 10):
        return None

    monkeypatch.setattr(ak, "aktools_fake_nodoc", fake, raising=False)
    info = describe_interface("aktools_fake_nodoc")
    assert info["title"] == ""
    assert info["doc"] == ""
    assert info["params"] == [
        {
            "name": "code",
            "default": None,
            "required": True,
            "type": "",
            "description": "",
        },
        {
            "name": "limit",
            "default": 10,
            "required": False,
            "type": "int",
            "description": "",
        },
    ]


def test_describe_unknown_interface_returns_404() -> None:
    response = client.get("/api/interfaces/not_a_real_interface_xyz")
    assert response.status_code == 404
    assert "error" in response.json()


def test_describe_rejects_non_interface_names() -> None:
    """子模块等非函数对象不是数据接口，同样返回 404"""
    module_name = next(
        n for n in dir(ak) if isinstance(getattr(ak, n), types.ModuleType)
    )
    assert client.get(f"/api/interfaces/{module_name}").status_code == 404
