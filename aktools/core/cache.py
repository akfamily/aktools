# -*- coding:utf-8 -*-
# !/usr/bin/env python
"""
Date: 2026/10/29 21:00
Desc: 结果缓存与 AKShare 内部缓存清理
1. 结果缓存：同一接口、同样参数在有效期内直接返回上次的数据，减少对上游网站的重复请求，
   降低被封 IP 的风险。有效期由环境变量 AKTOOLS_CACHE_TTL 指定（秒，默认 60，0 为关闭）
2. AKShare 内部缓存清理：AKShare 为脚本场景设计，部分函数用 lru_cache 缓存了板块名称、
   代码映射等数据；AKTools 长期运行时这些缓存永不过期，数据会停在服务启动时的状态。
   因此按间隔清空，间隔由环境变量 AKTOOLS_AKSHARE_CACHE_CLEAR 指定（秒，默认 3600，0 为关闭）
环境变量由命令行参数设置，也可在 Gunicorn、Docker 部署时直接设置；多进程部署时每个进程各有一份缓存
"""

import os
import sys
import threading
import time
from collections import OrderedDict
from typing import Any, Callable, Hashable, List, Optional

# 导入 akshare 时会加载其全部子模块，find_akshare_caches 依赖这些子模块已在 sys.modules 中
import akshare  # noqa: F401

CACHE_TTL_ENV = "AKTOOLS_CACHE_TTL"
AKSHARE_CACHE_CLEAR_ENV = "AKTOOLS_AKSHARE_CACHE_CLEAR"
DEFAULT_CACHE_TTL = 60
DEFAULT_AKSHARE_CACHE_CLEAR = 3600
CACHE_MAXSIZE = 256


def env_seconds(name: str, default: int) -> int:
    """读取以秒为单位的环境变量；未设置或不是非负整数时使用默认值"""
    value = os.getenv(name, "").strip()
    if value.isdigit():
        return int(value)
    return default


class ResultCache:
    """
    带有效期的 LRU 缓存，线程安全
    AKShare 接口在 uvicorn 的线程池中执行，多个请求会同时读写缓存
    """

    def __init__(
        self,
        ttl: int,
        maxsize: int = CACHE_MAXSIZE,
        clock: Callable[[], float] = time.monotonic,
    ):
        self.ttl = ttl
        self.maxsize = maxsize
        self._clock = clock
        self._data: "OrderedDict[Hashable, tuple]" = OrderedDict()
        self._lock = threading.Lock()

    def get(self, key: Hashable) -> Optional[Any]:
        """返回有效期内的缓存值，没有或已过期时返回 None"""
        if self.ttl <= 0:
            return None
        with self._lock:
            item = self._data.get(key)
            if item is None:
                return None
            expires_at, value = item
            if self._clock() >= expires_at:
                del self._data[key]
                return None
            self._data.move_to_end(key)
            return value

    def set(self, key: Hashable, value: Any) -> None:
        """写入缓存，超过容量时淘汰最久未使用的一条"""
        if self.ttl <= 0:
            return
        with self._lock:
            self._data[key] = (self._clock() + self.ttl, value)
            self._data.move_to_end(key)
            while len(self._data) > self.maxsize:
                self._data.popitem(last=False)


def find_akshare_caches() -> List[Callable]:
    """
    找出 AKShare 中所有带 lru_cache 的函数
    其中多数是模块内部的私有函数（如 __stock_board_concept_name_em），
    不会出现在 akshare 顶层，因此遍历全部已导入的 akshare 子模块
    :return: 带 cache_clear 方法的函数列表
    :rtype: list
    """
    found = {}
    for name, module in list(sys.modules.items()):
        if module is None or not (name == "akshare" or name.startswith("akshare.")):
            continue
        for obj in list(vars(module).values()):
            if callable(getattr(obj, "cache_clear", None)) and str(
                getattr(obj, "__module__", "")
            ).startswith("akshare"):
                found[id(obj)] = obj
    return list(found.values())


def clear_akshare_caches() -> int:
    """清空 AKShare 的全部 lru_cache，返回清理的函数个数"""
    caches = find_akshare_caches()
    for func in caches:
        func.cache_clear()
    return len(caches)


class AkshareCacheJanitor:
    """
    按间隔清空 AKShare 内部缓存
    不使用后台线程：每次调用接口前检查一次，距上次清理超过间隔时才清理
    """

    def __init__(self, interval: int, clock: Callable[[], float] = time.monotonic):
        self.interval = interval
        self._clock = clock
        self._last = clock()
        self._lock = threading.Lock()

    def maybe_clear(self) -> bool:
        """到期则清理并返回 True，否则返回 False"""
        if self.interval <= 0:
            return False
        with self._lock:
            now = self._clock()
            if now - self._last < self.interval:
                return False
            self._last = now
        clear_akshare_caches()
        return True
