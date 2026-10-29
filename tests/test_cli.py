# -*- coding:utf-8 -*-
# !/usr/bin/env python
"""
Date: 2025/10/29 20:05
Desc: CLI 测试文件
运行 `python -m pytest tests/test_cli.py` 进行测试
"""

import sys

import pytest
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
    monkeypatch.setattr(
        cli, "run", lambda *args, **kwargs: calls.append((args, kwargs))
    )
    result = runner.invoke(cli.app, args=["--port", "8081"])
    assert result.exit_code == 0
    (command,), kwargs = calls[0]
    assert command[0] == executable
    assert command[command.index("--port") + 1] == "8081"
    assert not kwargs.get("shell")


@pytest.mark.parametrize(
    ("host", "local_url"),
    [
        ("0.0.0.0", "http://127.0.0.1:8888/"),
        ("::", "http://[::1]:8888/"),
        ("127.0.0.1", "http://127.0.0.1:8888/"),
        ("192.168.1.10", "http://192.168.1.10:8888/"),
        ("::1", "http://[::1]:8888/"),
    ],
)
def test_wildcard_host_shows_reachable_url(monkeypatch, host, local_url) -> None:
    """
    0.0.0.0 / :: 只表示“监听所有网卡”，不能作为访问地址：打印的链接与 --auto 打开的页面
    必须换成本机回环地址，而 uvicorn 仍按用户指定的地址监听
    """
    calls, launched = [], []
    monkeypatch.setattr(cli, "run", lambda command, **kwargs: calls.append(command))
    monkeypatch.setattr(cli.typer, "launch", lambda url: launched.append(url))
    result = runner.invoke(cli.app, args=["--host", host, "--port", "8888", "--auto"])
    assert result.exit_code == 0
    assert launched == [local_url]
    assert f"{local_url}docs" in result.stdout
    assert "http://0.0.0.0" not in result.stdout
    assert "http://::" not in result.stdout
    command = calls[0]
    assert command[command.index("--host") + 1] == host


def test_cache_options_passed_to_server_via_env(monkeypatch) -> None:
    """缓存配置通过环境变量传给 uvicorn 子进程"""
    calls = []
    monkeypatch.setattr(cli, "run", lambda command, **kwargs: calls.append(kwargs))
    result = runner.invoke(
        cli.app, args=["--cache-ttl", "0", "--akshare-cache-clear", "600"]
    )
    assert result.exit_code == 0
    env = calls[0]["env"]
    assert env["AKTOOLS_CACHE_TTL"] == "0"
    assert env["AKTOOLS_AKSHARE_CACHE_CLEAR"] == "600"


def test_cache_options_default_values(monkeypatch) -> None:
    calls = []
    monkeypatch.setattr(cli, "run", lambda command, **kwargs: calls.append(kwargs))
    assert runner.invoke(cli.app, args=[]).exit_code == 0
    env = calls[0]["env"]
    assert env["AKTOOLS_HOST"] == "127.0.0.1"
    assert env["AKTOOLS_CACHE_TTL"] == "60"
    assert env["AKTOOLS_AKSHARE_CACHE_CLEAR"] == "3600"
