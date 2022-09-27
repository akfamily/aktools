# -*- coding:utf-8 -*-
# !/usr/bin/env python
"""
Date: 2022/9/27 16:29
Desc: 命令行运行主文件
"""
import os
import sys
from subprocess import run

from tap import Tap

import aktools


class SimpleArgumentParser(Tap):
    version: str
    host: str = "127.0.0.1"  # 添加主机名参数: 变量名为 host, 必须填, 默认为：127.0.0.1
    port: int = 8080  # 添加端口号参数: 变量名为 port, 必须填 默认 8080, int 类型,
    func: str  # 要执行的函数名称

    def configure(self):
        self.description = "AKShare's HTTP API Server"
        self.add_argument(
            "-V",
            "--version",
            default=f"{aktools.__title__} {aktools.__version__}",
        )
        self.add_argument(
            "-H",
            "--host",
            help="Server IP to use for connection",
        )
        self.add_argument(
            "-P",
            "--port",
            help="Port number to use for connection",
        )
        self.add_argument(
            "-f",
            "--func",
            help='function name (default: "aktools")',
            choices=["aktools", "slug"],
            default="aktools",
        )


def main() -> None:
    """
    主程序
    :return:
    :rtype:
    """
    args = sys.argv[1:]
    options = SimpleArgumentParser().parse_args(args)
    file_address = os.path.dirname(os.path.abspath(aktools.__file__))
    order_str = f"uvicorn run:app --host {options.host} --port {options.port} --app-dir {file_address}"
    print(f"点击打开 HTTP API 主页：http://{options.host}:{options.port}/")
    print(f"点击打开接口导览：http://{options.host}:{options.port}/docs")
    run(order_str, shell=True)


if __name__ == "__main__":
    main()
