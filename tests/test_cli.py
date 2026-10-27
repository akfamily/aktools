# -*- coding:utf-8 -*-
# !/usr/bin/env python
"""
Date: 2025/10/29 20:05
Desc: CLI 测试文件
运行 `python -m pytest tests/test_cli.py` 进行测试
"""
import sys

from typer.testing import CliRunner

from aktools import __title__, __version__, cli

runner = CliRunner()


def test_version() -> None:
    """
    测试版本
    """
    result = runner.invoke(cli.app, args=["--version"])
    assert result.exit_code == 0
    assert f"{__title__} v{__version__}\n" in result.stdout


def test_start_command_with_space_in_path(monkeypatch) -> None:
    """
    测试启动命令以参数列表传入，路径中含空格时不会被截断
    见 https://github.com/akfamily/aktools/issues/238
    """
    calls = []
    executable = "C:/Program Files/Python/python.exe"
    monkeypatch.setattr(sys, "executable", executable)
    monkeypatch.setattr(cli, "run", lambda *args, **kwargs: calls.append((args, kwargs)))
    result = runner.invoke(cli.app, args=["--port", "8081"])
    assert result.exit_code == 0
    (command,), kwargs = calls[0]
    assert command[0] == executable
    assert command[command.index("--port") + 1] == "8081"
    assert not kwargs.get("shell")
