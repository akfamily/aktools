# -*- coding:utf-8 -*-
# !/usr/bin/env python
"""
Date: 2022/9/27 19:05
Desc: CLI 命令文件
"""

import sys
from subprocess import run
from typing import Optional

import akshare as ak
import typer

import aktools

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


@app.command()
def main(
    host: str = typer.Option("127.0.0.1", "--host", "-H", help="设置主机地址"),
    port: int = typer.Option(
        8080, "--port", "-P", min=0, max=65535, clamp=True, help="设置端口"
    ),
    auto: bool = typer.Option(
        False, "--auto", "-A", help="自动打开浏览器，默认为不打开"
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
    if host in _WILDCARD_HOSTS:
        typer.echo(
            f"已监听所有网卡，局域网内的其他机器请通过 http://<本机 IP>:{port}/ 访问"
        )
    if auto:
        typer.launch(f"{base_url}/")
    run(command)


if __name__ == "__main__":
    typer.run(main)
