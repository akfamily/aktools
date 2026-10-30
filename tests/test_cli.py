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


def test_startup_message_shows_mcp_url(monkeypatch) -> None:
    """启动提示中给出 MCP 地址，方便直接填入 AI 助手"""
    monkeypatch.setattr(cli, "run", lambda command, **kwargs: None)
    result = runner.invoke(cli.app, args=["--port", "8888"])
    assert result.exit_code == 0
    assert "http://127.0.0.1:8888/mcp" in result.stdout


def test_mcp_subcommand_starts_stdio_server(monkeypatch) -> None:
    """aktools mcp 以 stdio 方式启动 MCP，不启动 HTTP 服务；MCP 注册表据此登记为 uvx aktools mcp"""
    import aktools.mcp_server

    started, http = [], []
    monkeypatch.setattr(aktools.mcp_server, "main", lambda: started.append(1))
    monkeypatch.setattr(cli, "run", lambda *args, **kwargs: http.append(1))
    result = runner.invoke(cli.app, args=["mcp"])
    assert result.exit_code == 0, result.output
    assert started == [1]
    assert http == []
    # stdout 是 MCP 的协议通道，不能打印 HTTP 服务的启动提示
    assert result.stdout == ""


def test_aktools_command_is_registered() -> None:
    """pip 安装后提供 aktools 命令，与 python -m aktools 相同"""
    from importlib.metadata import entry_points

    scripts = {ep.name: ep.value for ep in entry_points(group="console_scripts")}
    assert scripts.get("aktools") == "aktools.__main__:main"


def test_proxy_and_timeout_passed_to_server_via_env(monkeypatch) -> None:
    """代理与超时通过环境变量传给 uvicorn 子进程，与 Gunicorn、Docker 部署时的配置方式一致"""
    calls = []
    monkeypatch.setattr(cli, "run", lambda command, **kwargs: calls.append(kwargs))
    result = runner.invoke(
        cli.app, args=["--proxy", "http://127.0.0.1:7890", "--timeout", "120"]
    )
    assert result.exit_code == 0, result.output
    env = calls[0]["env"]
    assert env["AKTOOLS_PROXY"] == "http://127.0.0.1:7890"
    assert env["AKTOOLS_TIMEOUT"] == "120.0"


def test_proxy_and_timeout_not_set_by_default(monkeypatch) -> None:
    """不传参数时不设置，沿用已有的环境变量，否则沿用 AKShare 的默认值"""
    monkeypatch.delenv("AKTOOLS_PROXY", raising=False)
    monkeypatch.delenv("AKTOOLS_TIMEOUT", raising=False)
    calls = []
    monkeypatch.setattr(cli, "run", lambda command, **kwargs: calls.append(kwargs))
    assert runner.invoke(cli.app, args=[]).exit_code == 0
    env = calls[0]["env"]
    assert "AKTOOLS_PROXY" not in env
    assert "AKTOOLS_TIMEOUT" not in env


def test_token_passed_via_env_and_not_printed(monkeypatch) -> None:
    """令牌经环境变量传给服务进程，启动提示中不显示令牌本身"""
    calls = []
    monkeypatch.setattr(cli, "run", lambda command, **kwargs: calls.append(kwargs))
    result = runner.invoke(cli.app, args=["--token", "s3cr3t-value"])
    assert result.exit_code == 0, result.output
    assert calls[0]["env"]["AKTOOLS_TOKEN"] == "s3cr3t-value"
    assert "s3cr3t-value" not in result.stdout
    assert "令牌" in result.stdout
