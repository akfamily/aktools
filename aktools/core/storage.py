# -*- coding:utf-8 -*-
# !/usr/bin/env python
"""
Date: 2026/11/15 20:00
Desc: 把接口返回的完整数据保存为本机的 CSV 文件，供 MCP 的 save_data 工具使用
文件只写入固定的数据目录，文件名由接口名与参数生成，调用方不能指定路径。
AKQuant 的 MCP 服务约定读取同一个目录，两边通过环境变量 AKTOOLS_DATA_DIR 保持一致
"""

import hashlib
import json
import os
import time
from pathlib import Path
from typing import Dict, Mapping, Optional, Tuple

import pandas as pd

DATA_DIR_ENV = "AKTOOLS_DATA_DIR"
# 数据目录中的文件保留的天数；每次保存时顺带清理更早的文件，避免长期使用后越积越多
RETENTION_DAYS = 7


def data_dir(env: Optional[Mapping[str, str]] = None) -> Path:
    """
    数据目录：优先使用 AKTOOLS_DATA_DIR，否则为用户目录下的 .aktools/data
    用用户目录而不是当前目录：Claude Desktop 等客户端启动 MCP 服务时的当前目录不确定
    :param env: 环境变量，默认取 os.environ
    :type env: Mapping
    :return: 数据目录的绝对路径，不保证已存在
    :rtype: pathlib.Path
    """
    configured = (os.environ if env is None else env).get(DATA_DIR_ENV, "").strip()
    base = (
        Path(configured).expanduser()
        if configured
        else Path.home() / ".aktools" / "data"
    )
    return base.resolve()


def file_name(name: str, params: Dict[str, str]) -> str:
    """
    文件名：接口名加参数的哈希，相同的请求对应同一个文件
    接口名来自 AKShare 的接口登记，只含小写字母、数字与下划线，可以直接用作文件名
    """
    raw = json.dumps(sorted(params.items()), ensure_ascii=False)
    return f"{name}-{hashlib.sha1(raw.encode('utf-8')).hexdigest()[:10]}.csv"


def _prune(directory: Path, keep: Path, now: float) -> None:
    """删除数据目录中超过保留天数的 CSV 文件；只处理本模块生成的 .csv，不动其他文件"""
    deadline = now - RETENTION_DAYS * 86400
    for path in directory.glob("*.csv"):
        try:
            if path != keep and path.is_file() and path.stat().st_mtime < deadline:
                path.unlink()
        except OSError:
            # 文件正被其他程序占用或已被删除，留到下次清理
            continue


def save_csv(
    name: str,
    params: Dict[str, str],
    df: pd.DataFrame,
    env: Optional[Mapping[str, str]] = None,
) -> Tuple[Path, bool]:
    """
    把数据保存为 CSV 文件
    不带 BOM 的 UTF-8：文件是给程序读的，BOM 会混进第一列的列名；
    内容与已有文件相同时不重写，文件的修改时间保持不变——AKQuant 按“路径加修改时间”
    识别数据集，每重写一次就会多缓存一份。先写临时文件再改名，读的一方不会看到写了一半的文件
    :param name: 接口名
    :type name: str
    :param params: 接口参数
    :type params: dict
    :param df: 接口返回的完整数据
    :type df: pandas.DataFrame
    :param env: 环境变量，默认取 os.environ
    :type env: Mapping
    :return: (文件的绝对路径, 本次是否写入了文件)
    :rtype: tuple
    :raises OSError: 数据目录无法创建或写入
    """
    directory = data_dir(env)
    directory.mkdir(parents=True, exist_ok=True)
    target = directory / file_name(name, params)
    content = df.to_csv(index=False, lineterminator="\n").encode("utf-8")
    written = not (target.is_file() and target.read_bytes() == content)
    if written:
        temporary = target.with_name(target.name + ".tmp")
        temporary.write_bytes(content)
        os.replace(temporary, target)
    _prune(directory, target, time.time())
    return target, written
