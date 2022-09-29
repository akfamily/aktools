# -*- coding:utf-8 -*-
# !/usr/bin/env python
"""
Date: 2022/9/29 15:05
Desc: CLI 测试文件
运行 `python -m pytest tests/test_cli.py` 进行测试
"""
from typer.testing import CliRunner

from aktools import __title__, __version__, cli

runner = CliRunner()


def test_version() -> None:
    """
    测试版本
    """
    result = runner.invoke(cli.app, ["--version"])
    assert result.exit_code == 0
    assert f"{__title__} v{__version__}\n" in result.stdout
