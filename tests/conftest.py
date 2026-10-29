# -*- coding:utf-8 -*-
# !/usr/bin/env python
"""
Date: 2026/10/27 20:00
Desc: pytest 配置，使 tests 可以导入 scripts 目录下的脚本
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))


import pytest  # noqa: E402


@pytest.fixture(autouse=True)
def _fresh_result_cache(monkeypatch):
    """结果缓存是模块级对象，每个测试换上一份新的，避免测试之间互相影响"""
    import aktools.core.api as api
    from aktools.core.cache import ResultCache

    monkeypatch.setattr(api, "result_cache", ResultCache(ttl=60))
