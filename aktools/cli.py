# -*- coding:utf-8 -*-
# !/usr/bin/env python
"""
Date: 2022/9/27 19:05
Desc: CLI 命令文件
"""

import os
import sys
from subprocess import run
from typing import Optional

import akshare as ak
import typer

import aktools
from aktools.core.cache import (
    AKSHARE_CACHE_CLEAR_ENV,
    CACHE_TTL_ENV,
    DEFAULT_AKSHARE_CACHE_CLEAR,
    DEFAULT_CACHE_TTL,
)

app = typer.Typer()

# 通配地址只表示“监听所有网卡”，浏览器无法用它访问，需换成本机回环地址
_WILDCARD_HOSTS = {"0.0.0.0": "127.0.0.1", "::": "::1"}


def local_base_url(host: str, port: int) -> str:
    """
    返回本机浏览器可以打开的服务地址，用于终端提示与 --auto 自动打开
    :param host: 监听地址，如 127.0.0.1、0.0.0.0、::
    :type host: str
    :param port: 监听端口
    :type port: int
    :return: 形如 http://127.0.0.1:8080 的地址，IPv6 地址按 URL 规范加方括号
    :rtype: str
    """
    host = _WILDCARD_HOSTS.get(host, host)
    if ":" in host:
        host = f"[{host}]"
    return f"http://{host}:{port}"


def version_callback(value: bool):
    if value:
        typer.echo(f"{aktools.__title__} v{aktools.__version__}")
        raise typer.Exit()


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    host: str = typer.Option("127.0.0.1", "--host", "-H", help="设置主机地址"),
    port: int = typer.Option(
        8080, "--port", "-P", min=0, max=65535, clamp=True, help="设置端口"
    ),
    auto: bool = typer.Option(
        False, "--auto", "-A", help="自动打开浏览器，默认为不打开"
    ),
    cache_ttl: int = typer.Option(
        DEFAULT_CACHE_TTL,
        "--cache-ttl",
        min=0,
        help="结果缓存的有效期（秒），同一接口与参数在有效期内直接返回上次的数据，0 为关闭",
    ),
    akshare_cache_clear: int = typer.Option(
        DEFAULT_AKSHARE_CACHE_CLEAR,
        "--akshare-cache-clear",
        min=0,
        help="清空 AKShare 内部缓存的间隔（秒），避免板块名称等数据停在服务启动时，0 为关闭",
    ),
    version: Optional[bool] = typer.Option(
        None,
        "--version",
        "-v",
        help="查看 AKTools 的版本",
        callback=version_callback,
        is_eager=True,
    ),
) -> None:
    """启动 AKTools 的 HTTP 服务；带子命令（如 mcp）时只执行子命令"""
    if ctx.invoked_subcommand is not None:
        return
    # 以参数列表传入且不经过 shell，Python 或 aktools 的安装路径中含空格时也能正确启动；
    # aktools.main:app 按包路径加载，无需再通过 --app-dir 指定目录
    command = [
        sys.executable,
        "-m",
        "uvicorn",
        "aktools.main:app",
        "--host",
        host,
        "--port",
        str(port),
    ]
    base_url = local_base_url(host, port)
    typer.echo(
        f"请访问：{base_url}/version 来获取最新的库版本信息，确保使用最新版本的 AKShare 和 AKTools"
    )
    typer.echo(
        f"当前的 AKTools 版本为：{aktools.__version__}，AKShare 版本为：{ak.__version__}"
    )
    typer.echo(f"点击打开 HTTP API 主页：{base_url}/")
    typer.echo(f"点击打开接口导览：{base_url}/docs")
    typer.echo(f"AI 助手（MCP）地址：{base_url}/mcp")
    if host in _WILDCARD_HOSTS:
        typer.echo(
            f"已监听所有网卡，局域网内的其他机器请通过 http://<本机 IP>:{port}/ 访问"
        )
    if auto:
        typer.launch(f"{base_url}/")
    # 缓存配置通过环境变量传给 uvicorn 子进程，与 Gunicorn、Docker 部署时的配置方式一致
    env = {
        **os.environ,
        # MCP 据此决定是否只接受发往本机的请求，见 aktools.mcp_server.build_mcp_app
        "AKTOOLS_HOST": host,
        CACHE_TTL_ENV: str(cache_ttl),
        AKSHARE_CACHE_CLEAR_ENV: str(akshare_cache_clear),
    }
    run(command, env=env)


@app.command(
    "mcp", help="以 stdio 方式启动 MCP 服务，供 AI 助手自行启动（与 aktools-mcp 相同）"
)
def mcp() -> None:
    """
    以 stdio 方式启动 MCP 服务，供 AI 助手自行启动，与 aktools-mcp 命令相同。
    MCP 官方注册表的客户端按包名运行 uvx aktools，因此在 server.json 中登记为 uvx aktools mcp
    """
    import aktools.mcp_server

    aktools.mcp_server.main()


if __name__ == "__main__":
    app()
