# -*- coding:utf-8 -*-
# !/usr/bin/env python
"""
Date: 2026/11/15 20:00
Desc: 数据落盘测试：save_data 把完整数据写成 CSV，供 AKQuant 等程序读取
"""

import os
import time
from pathlib import Path

import pandas as pd

from aktools.core import storage

DF = pd.DataFrame(
    {
        "date": pd.to_datetime(["2024-10-08", "2024-10-09"]),
        "open": [1771.63, 1576.85],
        "名称": ["贵州茅台", "贵州茅台"],
    }
)


def _env(tmp_path):
    return {storage.DATA_DIR_ENV: str(tmp_path / "data")}


def test_data_dir_defaults_to_user_home():
    assert storage.data_dir({}) == (Path.home() / ".aktools" / "data").resolve()


def test_data_dir_follows_env(tmp_path):
    assert storage.data_dir(_env(tmp_path)) == (tmp_path / "data").resolve()


def test_file_name_depends_on_interface_and_params_only():
    a = storage.file_name(
        "stock_zh_a_hist_sina", {"symbol": "sh600519", "adjust": "qfq"}
    )
    b = storage.file_name(
        "stock_zh_a_hist_sina", {"adjust": "qfq", "symbol": "sh600519"}
    )
    c = storage.file_name(
        "stock_zh_a_hist_sina", {"symbol": "sh600000", "adjust": "qfq"}
    )
    assert a == b != c
    assert a.startswith("stock_zh_a_hist_sina-") and a.endswith(".csv")


def test_save_csv_writes_utf8_without_bom_inside_data_dir(tmp_path):
    path, written = storage.save_csv(
        "aktools_fake", {"symbol": "1"}, DF, _env(tmp_path)
    )
    assert written is True
    assert path.parent == (tmp_path / "data").resolve()
    raw = path.read_bytes()
    # 给程序读的文件不带 BOM，否则第一列的列名会变成 "\ufeffdate"
    assert not raw.startswith(b"\xef\xbb\xbf")
    assert raw.decode("utf-8").splitlines()[0] == "date,open,名称"
    back = pd.read_csv(path)
    assert list(back.columns) == ["date", "open", "名称"]
    assert back["open"].tolist() == [1771.63, 1576.85]
    assert not list(path.parent.glob("*.tmp"))


def test_save_csv_does_not_rewrite_identical_content(tmp_path):
    """内容没变就不重写：AKQuant 按文件的修改时间识别数据集，重写一次就多缓存一份"""
    env = _env(tmp_path)
    path, _ = storage.save_csv("aktools_fake", {}, DF, env)
    os.utime(path, (1_700_000_000, 1_700_000_000))
    old = time.time() - 3600
    os.utime(path, (old, old))
    before = path.stat().st_mtime_ns
    same, written = storage.save_csv("aktools_fake", {}, DF, env)
    assert same == path and written is False
    assert path.stat().st_mtime_ns == before
    _, written = storage.save_csv("aktools_fake", {}, DF.assign(open=[1.0, 2.0]), env)
    assert written is True
    assert path.stat().st_mtime_ns != before


def test_save_csv_prunes_old_csv_files_only(tmp_path):
    directory = tmp_path / "data"
    directory.mkdir()
    old_csv, fresh_csv, other = (
        directory / "old.csv",
        directory / "fresh.csv",
        directory / "notes.txt",
    )
    for file in (old_csv, fresh_csv, other):
        file.write_text("x", encoding="utf-8")
    long_ago = time.time() - (storage.RETENTION_DAYS + 1) * 86400
    os.utime(old_csv, (long_ago, long_ago))
    os.utime(other, (long_ago, long_ago))
    storage.save_csv("aktools_fake", {}, DF, _env(tmp_path))
    assert not old_csv.exists()
    assert fresh_csv.exists()
    # 只清理本模块生成的 .csv，用户放在目录里的其他文件不动
    assert other.exists()
