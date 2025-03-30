# -*- coding:utf-8 -*-
# !/usr/bin/env python
"""
Date: 2022/9/27 19:05
Desc: CLI 执行入口文件
运行 `python -m aktools` 相当于运行 `python -m aktools.__main__.py`
"""
from aktools import cli, __title__


def main():
    cli.app(prog_name=__title__)


if __name__ == "__main__":
    main()
