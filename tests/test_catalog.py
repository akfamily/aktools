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
    assert "stock_zh_a_hist_em" in names
    title = next(i["title"] for i in items if i["name"] == "stock_zh_a_hist_em")
    assert title == inspect.getdoc(ak.stock_zh_a_hist_em).splitlines()[0].strip()
    # AKShare 顶层还导出了子模块和类，它们不是数据接口，不应出现在目录中
    module_names = {n for n in dir(ak) if isinstance(getattr(ak, n), types.ModuleType)}
    assert module_names and not names & module_names
    assert not any(name.startswith("_") for name in names)


def test_list_interfaces_filters_by_keyword() -> None:
    response = client.get("/api/interfaces", params={"q": "STOCK_ZH_A_HIST"})
    assert response.status_code == 200
    items = response.json()
    assert "stock_zh_a_hist_em" in {item["name"] for item in items}
    assert all(
        "stock_zh_a_hist" in item["name"] or "stock_zh_a_hist" in item["title"].lower()
        for item in items
    )


def test_describe_real_interface() -> None:
    response = client.get("/api/interfaces/stock_zh_a_hist_em")
    assert response.status_code == 200
    info = response.json()
    assert info["name"] == "stock_zh_a_hist_em"
    assert info["url"] == "/api/public/stock_zh_a_hist_em"
    assert info["source_url"].startswith("http")
    expected = list(inspect.signature(ak.stock_zh_a_hist_em).parameters)
    assert [p["name"] for p in info["params"]] == expected
    symbol = info["params"][0]
    assert symbol["default"] == "000001"
    assert symbol["required"] is False
    assert symbol["type"] == "str"
    assert symbol["description"]
    assert info["doc"] == inspect.getdoc(ak.stock_zh_a_hist_em)


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


def test_describe_interface_without_registry_entry_has_empty_extras(
    monkeypatch,
) -> None:
    """AKShare 注册表中没有登记的接口，返回列与示例为空，不影响其余字段"""

    def fake(code="1"):
        return None

    monkeypatch.setattr(ak, "aktools_fake_unregistered", fake, raising=False)
    info = describe_interface("aktools_fake_unregistered")
    assert info["outputs"] == []
    assert info["example"] == ""
    assert info["params"][0]["name"] == "code"


# ---- 数据来源与东方财富 push2 限流 ----

import pytest  # noqa: E402

from aktools.core import catalog  # noqa: E402

PUSH2 = "eastmoney_push2"


def _fake_registry(monkeypatch, records):
    """用给定的登记信息代替 ak.interface_info，未列出的接口视为未登记"""
    monkeypatch.setattr(catalog, "_registry_info", lambda name: records.get(name, {}))


@pytest.mark.parametrize(
    ("url", "rate_limit", "expected"),
    [
        ("https://finance.sina.com.cn/realstock/", None, "新浪财经"),
        ("https://data.10jqka.com.cn/funds/ggzjl/", None, "同花顺"),
        ("https://gu.qq.com/sh000919/zs", None, "腾讯"),
        ("https://data.eastmoney.com/cjsj/cpi.html", None, "东方财富"),
        ("https://quote.eastmoney.com/center/", PUSH2, catalog.PUSH2_SOURCE),
        ("https://www.example.org/data", None, "example.org"),
    ],
)
def test_source_of_maps_domain_to_chinese_name(monkeypatch, url, rate_limit, expected):
    _fake_registry(
        monkeypatch, {"stock_zh_a_hist_em": {"url": url, "rate_limit": rate_limit}}
    )
    assert catalog.source_of("stock_zh_a_hist_em") == expected


def test_push2_source_tells_it_is_rate_limited():
    # 来源名本身要让 AI 一眼看出这类接口频繁访问会被限流，与东方财富数据中心区分开
    assert "东方财富" in catalog.PUSH2_SOURCE
    assert "限流" in catalog.PUSH2_SOURCE


def test_source_of_falls_back_to_docstring_url(monkeypatch):
    """AKShare 没有登记 url 时，取 docstring 第二行的数据源地址"""

    def fake():
        """
        新浪财经-测试接口
        https://vip.stock.finance.sina.com.cn/mkt/
        """

    monkeypatch.setattr(ak, "aktools_fake_source", fake, raising=False)
    _fake_registry(monkeypatch, {})
    assert catalog.source_of("aktools_fake_source") == "新浪财经"


def test_source_of_unknown_is_empty(monkeypatch):
    def fake():
        """没有数据源地址的接口"""

    monkeypatch.setattr(ak, "aktools_fake_nosource", fake, raising=False)
    _fake_registry(monkeypatch, {})
    assert catalog.source_of("aktools_fake_nosource") == ""


def test_rate_limit_of_reads_registry(monkeypatch):
    _fake_registry(
        monkeypatch,
        {"stock_zh_a_hist_em": {"rate_limit": PUSH2}, "macro_china_cpi": {}},
    )
    assert catalog.rate_limit_of("stock_zh_a_hist_em") == PUSH2
    # 旧版 AKShare 的登记没有 rate_limit 字段，按不限流处理
    assert catalog.rate_limit_of("macro_china_cpi") is None


def test_describe_interface_includes_source_and_rate_limit(monkeypatch):
    _fake_registry(
        monkeypatch,
        {
            "stock_zh_a_hist_em": {
                "url": "https://quote.eastmoney.com/",
                "rate_limit": PUSH2,
            }
        },
    )
    info = describe_interface("stock_zh_a_hist_em")
    assert info["source"] == catalog.PUSH2_SOURCE
    assert info["rate_limit"] == PUSH2


ALT_REGISTRY = {
    "stock_zh_a_hist_em": {
        "rate_limit": PUSH2,
        "alternatives": [
            "stock_zh_a_daily_sina",
            "stock_zh_a_spot_em",
            "aktools_removed_interface",
        ],
    },
    "stock_zh_a_daily_sina": {"url": "https://finance.sina.com.cn/"},
    "stock_zh_a_spot_em": {"rate_limit": PUSH2},
}


def test_registered_alternatives_come_from_akshare_registry(monkeypatch):
    """同类接口取自 AKShare 人工维护的对照表，登记了但当前版本没有的接口不列出"""
    _fake_registry(monkeypatch, ALT_REGISTRY)
    items = catalog.registered_alternatives("stock_zh_a_hist_em")
    assert [item["name"] for item in items] == [
        "stock_zh_a_daily_sina",
        "stock_zh_a_spot_em",
    ]
    assert items[0]["source"] == "新浪财经"
    assert items[1]["rate_limit"] == PUSH2


def test_find_alternatives_excludes_other_push2_interfaces(monkeypatch):
    """限流按 IP 生效，被限流时其他东方财富行情接口同样用不了，不能作为替代"""
    _fake_registry(monkeypatch, ALT_REGISTRY)
    names = [item["name"] for item in catalog.find_alternatives("stock_zh_a_hist_em")]
    assert names == ["stock_zh_a_daily_sina"]


def test_find_alternatives_does_not_guess(monkeypatch):
    """没有登记同类接口时不给候选：0.1.5 按名称猜测，会把 ST 股票列表配给日线"""
    _fake_registry(monkeypatch, {"stock_zh_a_st_em": {"rate_limit": PUSH2}})
    assert catalog.find_alternatives("stock_zh_a_st_em") == []


def test_describe_interface_lists_alternatives(monkeypatch):
    _fake_registry(monkeypatch, ALT_REGISTRY)
    info = describe_interface("stock_zh_a_hist_em")
    assert info["alternatives"] == [
        {
            "name": "stock_zh_a_daily_sina",
            "title": info["alternatives"][0]["title"],
            "source": "新浪财经",
        },
        {
            "name": "stock_zh_a_spot_em",
            "title": info["alternatives"][1]["title"],
            "source": catalog.PUSH2_SOURCE,
        },
    ]


def test_real_registry_has_alternatives_for_a_share_daily():
    """随依赖安装的 AKShare（不低于 1.20.39）登记了 A 股日线的同类接口"""
    names = [item["name"] for item in catalog.find_alternatives("stock_zh_a_hist_em")]
    assert names == ["stock_zh_a_daily_sina", "stock_zh_a_hist_tx"]


def test_similar_names_for_renamed_interface():
    # AKShare 1.20.31 把 get_futures_daily 更名为 futures_daily
    assert "futures_daily" in catalog.similar_names("get_futures_daily")
    assert catalog.similar_names("zzz_nothing_like_this_qq") == []


def test_unknown_interface_404_suggests_similar_names():
    resp = client.get("/api/interfaces/stock_zh_a_hists")
    assert resp.status_code == 404
    assert "stock_zh_a_hist_em" in resp.json()["error"]
    assert "名称相近的接口" in resp.json()["error"]
    # 没有相近名称时不出现这句提示
    resp = client.get("/api/interfaces/zzz_nothing_like_this_qq")
    assert "名称相近的接口" not in resp.json()["error"]


def test_source_of_names_more_data_sources(monkeypatch):
    _fake_registry(
        monkeypatch,
        {
            "bond_cb_jsl": {"url": "https://app.jisilu.cn/data/cbnew/"},
            "spot_golden_benchmark_sge": {"url": "https://www.sge.com.cn/sjzx/"},
        },
    )
    assert catalog.source_of("bond_cb_jsl") == "集思录"
    assert catalog.source_of("spot_golden_benchmark_sge") == "上海黄金交易所"


def test_not_found_hint_names_the_new_interface_for_renamed_names() -> None:
    """已更名的接口直接给出新名称，而不是按相似度猜"""
    hint = catalog.not_found_hint("stock_zh_a_hist")
    assert "更名为 stock_zh_a_hist_em" in hint
    assert "名称相近的接口" not in hint


def test_not_found_hint_tells_removed_version() -> None:
    hint = catalog.not_found_hint("index_yw")
    assert "移除" in hint and "1.20.54" in hint
    assert "名称相近的接口" not in hint


def test_not_found_hint_still_suggests_similar_names_for_typos() -> None:
    assert "stock_zh_a_hist_em" in catalog.not_found_hint("stock_zh_a_hist_emm")
    assert catalog.not_found_hint("zzz_nothing_like_this_qq") == ""


def test_public_route_reports_rename() -> None:
    response = client.get("/api/public/stock_zh_a_daily")
    assert response.status_code == 404
    assert "stock_zh_a_daily_sina" in response.json()["error"]
