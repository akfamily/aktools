# -*- coding:utf-8 -*-
# !/usr/bin/env python
"""
Date: 2021/12/13 15:59
Desc: 命令行运行主文件
"""
import os
import sys
from argparse import ArgumentParser

import aktools


def get_parser():
    parser = ArgumentParser(description="AKShare's HTTP Server")
    parser.add_argument(
        "-V",
        "--version",
        action="version",
        version=f"{aktools.__title__} {aktools.__version__}",
    )

    # 添加主机名参数 变量名为host, 必须填
    parser.add_argument(
        "--host",
        action="store",
        dest="host",
        help="Server IP to use for connection",
        default="127.0.0.1",
        type=str,
        required=False,
    )
    # 添加端口号参数 变量名为port, 默认9908, int类型,非必填
    parser.add_argument(
        "-P",
        "--port",
        action="store",
        dest="port",
        help="port number to use for connection",
        default=8080,
        type=int,
        required=False,
    )

    # 要执行的函数名称
    parser.add_argument(
        "-f",
        "--func",
        help='function name (default: "aktools")',
        choices=["aktools", "slug"],
        default="aktools",
    )
    return parser


def main():
    args = sys.argv[1:]
    parser = get_parser()
    options = parser.parse_args(args)
    print(options.host, options.port)
    file_address = os.path.join(
        os.path.dirname(os.path.abspath(aktools.__file__)), "core"
    )
    print(file_address)
    order_str = f"uvicorn api:app --host {options.host} --port {options.port} --app-dir {file_address}"
    # os.system(order_str)
    from subprocess import run
    run(order_str, shell=True)


if __name__ == "__main__":
    main()
