# -*- coding:utf-8 -*-
# /usr/bin/env python
"""
Author: Albert King
date: 2019/10/16 13:58
contact: jindaxiang@163.com
desc: AkShare 的 pypi 基本信息文件
"""
import re
import ast

import setuptools

with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()


def get_version_string():
    """
    Get the aktools version number
    :return: str version number
    """
    with open("aktools/__init__.py", "rb") as f:
        version_line = re.search(
            r"__version__\s+=\s+(.*)", f.read().decode("utf-8")
        ).group(1)
        return str(ast.literal_eval(version_line))


setuptools.setup(
    name="aktools",
    version=get_version_string(),
    author="Albert King",
    author_email="jindaxiang@163.com",
    license="MIT",
    description="A tool for local http server!",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/jindaxiang/aktools",
    packages=setuptools.find_packages(),
    install_requires=[
        "akshare>=0.4.15",
        "fastapi>=0.49.0",
    ],
    package_data={"": ["*.py", "*.json", "*.pk", "*.woff"]},
    keywords=[
        "stock",
        "option",
        "futures",
        "bond",
        "index",
        "air",
        "others",
        "finance",
        "spider",
        "quant",
        "quantitative",
        "investment",
        "trading",
        "algotrading",
    ],
    classifiers=[
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
)
