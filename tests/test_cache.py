# -*- coding:utf-8 -*-
# !/usr/bin/env python
"""
Date: 2026/10/29 21:00
Desc: 结果缓存与 AKShare 内部缓存清理测试
"""

import functools
import subprocess
import sys

import akshare as ak
import pandas as pd
import pytest

import aktools.core.api as api
import aktools.core.fetch as fetch
from aktools.core.cache import (
    AkshareCacheJanitor,
    ResultCache,
    clear_akshare_caches,
    find_akshare_caches,
)


class _Clock:
    """可手动拨动的时钟，避免测试依赖真实时间"""

    def __init__(self):
        self.now = 1000.0

    def __call__(self):
        return self.now


class _FakeRequest:
    def __init__(self, params=None):
        self.query_params = params or {}


def test_result_cache_hit_within_ttl_and_expire_after():
    clock = _Clock()
    cache = ResultCache(ttl=60, maxsize=10, clock=clock)
    cache.set(("a", ()), "value")
    clock.now += 59
    assert cache.get(("a", ())) == "value"
    clock.now += 2
    assert cache.get(("a", ())) is None


def test_result_cache_disabled_when_ttl_is_zero():
    cache = ResultCache(ttl=0, maxsize=10)
    cache.set(("a", ()), "value")
    assert cache.get(("a", ())) is None


def test_result_cache_evicts_least_recently_used():
    cache = ResultCache(ttl=60, maxsize=2)
    cache.set("a", 1)
    cache.set("b", 2)
    assert cache.get("a") == 1  # 访问 a 后，b 成为最久未用的一条
    cache.set("c", 3)
    assert cache.get("b") is None
    assert cache.get("a") == 1 and cache.get("c") == 3


def test_find_akshare_caches_includes_private_module_functions():
    """模块内部的私有缓存函数也要找到，Issue 中板块名称不更新就出在这里"""
    names = {f.__qualname__ for f in find_akshare_caches()}
    assert "__stock_board_concept_name_em" in names
    assert "stock_info_a_code_name" in names


def test_find_akshare_caches_works_in_fresh_process():
    """单独导入 cache 模块时也要找到 AKShare 的缓存函数，不能依赖调用方先导入了 akshare"""
    code = (
        "from aktools.core.cache import find_akshare_caches;"
        "print(len(find_akshare_caches()))"
    )
    out = subprocess.run(
        [sys.executable, "-c", code], capture_output=True, text=True, check=True
    )
    assert int(out.stdout.strip()) > 13


def test_clear_akshare_caches_clears_module_level_cache(monkeypatch):
    module = sys.modules["akshare.stock.board.stock_board_concept_em"]

    @functools.lru_cache
    def fake_cached(x):
        return x * 2

    fake_cached.__module__ = module.__name__
    monkeypatch.setattr(module, "aktools_fake_cached", fake_cached, raising=False)
    fake_cached(1)
    assert fake_cached.cache_info().currsize == 1
    assert clear_akshare_caches() >= 1
    assert fake_cached.cache_info().currsize == 0


def test_janitor_clears_only_after_interval(monkeypatch):
    clock = _Clock()
    cleared = []
    monkeypatch.setattr(
        "aktools.core.cache.clear_akshare_caches", lambda: cleared.append(1) or 0
    )
    janitor = AkshareCacheJanitor(interval=3600, clock=clock)
    janitor.maybe_clear()
    clock.now += 3599
    janitor.maybe_clear()
    assert cleared == []
    clock.now += 2
    janitor.maybe_clear()
    assert cleared == [1]
    janitor.maybe_clear()
    assert cleared == [1]


def test_janitor_disabled_when_interval_is_zero(monkeypatch):
    clock = _Clock()
    cleared = []
    monkeypatch.setattr(
        "aktools.core.cache.clear_akshare_caches", lambda: cleared.append(1) or 0
    )
    janitor = AkshareCacheJanitor(interval=0, clock=clock)
    clock.now += 10**6
    janitor.maybe_clear()
    assert cleared == []


@pytest.fixture
def counting_interface(monkeypatch):
    """记录调用次数的假接口，并为每个测试换上一份全新的结果缓存"""
    calls = []

    def fake(symbol="000001"):
        calls.append(symbol)
        return pd.DataFrame({"代码": [symbol], "收盘": [9.5]})

    monkeypatch.setattr(ak, "aktools_fake_count", fake, raising=False)
    monkeypatch.setattr(fetch, "result_cache", ResultCache(ttl=60, maxsize=10))
    return calls


def test_repeated_request_uses_cache(counting_interface):
    first = api.call_interface("aktools_fake_count", _FakeRequest({"symbol": "1"}))
    second = api.call_interface("aktools_fake_count", _FakeRequest({"symbol": "1"}))
    assert counting_interface == ["1"]
    assert first.headers["x-aktools-cache"] == "miss"
    assert second.headers["x-aktools-cache"] == "hit"
    assert first.body == second.body


def test_cache_key_depends_on_params_not_format(counting_interface):
    api.call_interface("aktools_fake_count", _FakeRequest({"symbol": "1"}))
    csv = api.call_interface(
        "aktools_fake_count", _FakeRequest({"symbol": "1", "_format": "csv"})
    )
    api.call_interface("aktools_fake_count", _FakeRequest({"symbol": "2"}))
    # 同样的参数换成 CSV 格式仍命中缓存；参数不同则重新调用
    assert counting_interface == ["1", "2"]
    assert csv.headers["x-aktools-cache"] == "hit"


def test_empty_result_is_not_cached(monkeypatch):
    calls = []
    monkeypatch.setattr(ak, "aktools_fake_none", lambda: calls.append(1), raising=False)
    monkeypatch.setattr(fetch, "result_cache", ResultCache(ttl=60, maxsize=10))
    for _ in range(2):
        assert (
            api.call_interface("aktools_fake_none", _FakeRequest()).status_code == 404
        )
    assert calls == [1, 1]


def test_identical_concurrent_requests_hit_upstream_once(monkeypatch):
    """
    几个相同的请求同时到达时只访问上游一次，其余的等它结束后从缓存取：
    结果缓存只对之后的请求生效，并发的相同请求原先各自访问上游，会加重上游的限流
    """
    import threading
    import time

    import aktools.core.fetch as fetch

    calls = []

    def slow(symbol="1"):
        calls.append(symbol)
        time.sleep(0.3)
        return pd.DataFrame({"a": [len(calls)]})

    monkeypatch.setattr(ak, "aktools_fake_slow", slow, raising=False)
    results = []
    threads = [
        threading.Thread(
            target=lambda: results.append(
                fetch.fetch_dataframe("aktools_fake_slow", {"symbol": "1"})[1]
            )
        )
        for _ in range(6)
    ]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    assert len(calls) == 1
    assert sorted(results) == ["hit"] * 5 + ["miss"]
    # 参数不同的请求互不等待
    fetch.fetch_dataframe("aktools_fake_slow", {"symbol": "2"})
    assert calls == ["1", "2"]
    assert fetch.in_flight._locks == {}


def test_no_queueing_when_result_cache_is_off(monkeypatch):
    """关闭结果缓存后不排队：排队只会把相同的请求变成串行"""
    import threading
    import time

    import aktools.core.fetch as fetch
    from aktools.core.cache import ResultCache

    monkeypatch.setattr(fetch, "result_cache", ResultCache(ttl=0))
    calls = []

    def slow():
        calls.append(1)
        time.sleep(0.3)
        return pd.DataFrame({"a": [1]})

    monkeypatch.setattr(ak, "aktools_fake_slow_off", slow, raising=False)
    threads = [
        threading.Thread(
            target=lambda: fetch.fetch_dataframe("aktools_fake_slow_off", {})
        )
        for _ in range(4)
    ]
    started = time.time()
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    assert len(calls) == 4
    assert time.time() - started < 1.0
