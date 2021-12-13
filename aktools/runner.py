# -*- coding:utf-8 -*-
# !/usr/bin/env python
"""
Date: 2021/12/13 15:59
Desc: 
"""
import os
from argparse import ArgumentParser
import aktools


class NullWriter(object):
    """数据流黑洞，类似 linux/unix 下 /dev/null 的效果。"""
    def write(self, string):
        pass


def get_parser():
    parser = ArgumentParser(description='AKShare\'s HTTP Server')
    parser.add_argument('-V', '--version', action='version',
                        version='{0} {1}'.format(
                            aktools.__title__, aktools.__version__
                        ))
    # 要执行的函数名称
    parser.add_argument('-f', '--func',
                        help='function name (default: "aktools")',
                        choices=['aktools', 'slug'],
                        default='aktools')
    return parser


def main():
    file_addr = os.path.join(os.path.dirname(os.path.abspath('__file__')), 'core')
    print(file_addr)
    order_str = f"uvicorn api:app --host 0.0.0.0 --port 8080 --app-dir {file_addr}"
    os.system(order_str)


if __name__ == '__main__':
    main()
