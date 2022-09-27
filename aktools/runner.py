# -*- coding:utf-8 -*-
# !/usr/bin/env python
"""
Date: 2022/9/27 16:29
Desc: 命令行运行主文件
"""
import os
import sys
import warnings
from subprocess import run

from tap import Tap

import aktools


class SimpleArgumentParser(Tap):
    version: str = f"{aktools.__title__} {aktools.__version__}"  # AKShare 的版本
    host: str = "127.0.0.1"  # 添加主机名参数: 变量名为 host, 必须填, 默认为：127.0.0.1
    port: int = 8080  # 添加端口号参数: 变量名为 port, 必须填 默认 8080, int 类型,
    func: str  # 要执行的函数名称

    def configure(self):
        self.description = "AKShare's HTTP API Server"
        self.add_argument(
            "-V",
            "--version",
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


# def get_parser():
#     """
#     增加 解析属性
#     :return:
#     :rtype:
#     """
#     parser = ArgumentParser(description="AKShare's HTTP API Server")
#     parser.add_argument(
#         "-V",
#         "--version",
#         action="version",
#         version=f"{aktools.__title__} {aktools.__version__}",
#     )
#
#     # 添加主机名参数 变量名为host, 必须填
#     parser.add_argument(
#         "--host",
#         action="store",
#         dest="host",
#         help="Server IP to use for connection",
#         default="127.0.0.1",
#         type=str,
#         required=False,
#     )
#
#     # 添加端口号参数 变量名为port, 默认9908, int类型, 非必填
#     parser.add_argument(
#         "-P",
#         "--port",
#         action="store",
#         dest="port",
#         help="port number to use for connection",
#         default=8080,
#         type=int,
#         required=False,
#     )
#
#     # 要执行的函数名称
#     parser.add_argument(
#         "-f",
#         "--func",
#         help='function name (default: "aktools")',
#         choices=["aktools", "slug"],
#         default="aktools",
#     )
#     return parser


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
    warnings.warn(f"点击打开接口导览：http://{options.host}:{options.port}/docs")
    run(order_str, shell=True)


if __name__ == "__main__":
    main()
