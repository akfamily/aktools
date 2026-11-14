# -*- coding:utf-8 -*-
# !/usr/bin/env python
"""
Date: 2026/10/27 20:00
Desc: pytest 配置，使 tests 可以导入 scripts 目录下的脚本
"""

import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

# 必须在任何测试导入 aktools 之前设置：aktools.core.log 导入时即创建日志文件。
# 写到临时目录，避免在仓库根目录留下 aktools_log.log 及其轮转文件；
# 测试中启动的子进程会继承该环境变量
os.environ["AKTOOLS_LOG_DIR"] = tempfile.mkdtemp(prefix="aktools-test-log-")


import pytest  # noqa: E402


@pytest.fixture(autouse=True)
def _fresh_result_cache(monkeypatch):
    """结果缓存是模块级对象，每个测试换上一份新的，避免测试之间互相影响"""
    import aktools.core.fetch as fetch
    from aktools.core.cache import ResultCache

    monkeypatch.setattr(fetch, "result_cache", ResultCache(ttl=60))


@pytest.fixture(autouse=True)
def _fake_interfaces_count_as_registered(monkeypatch):
    """
    只有 AKShare 接口登记中的名称才算数据接口。测试用 monkeypatch 挂到 akshare 上的
    aktools_fake_* 函数不在登记里，这里把它们算作已登记；其余名称仍按真实的登记判断
    """
    import akshare as ak

    import aktools.core.catalog as catalog

    real = catalog._registered_names()

    def names():
        fakes = {name for name in dir(ak) if name.startswith("aktools_fake")}
        return real | fakes

    monkeypatch.setattr(catalog, "_registered_names", names)
