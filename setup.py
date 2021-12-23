# -*- coding:utf-8 -*-
# /usr/bin/env python
"""
Date: 2021/12/23 16:20
Desc: AKTools 的 PYPI 基本信息文件
"""
import re
import ast

import setuptools


with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()


def get_version_string() -> str:
    """
    Get the aktools version number
    :return: version number
    :rtype: str
    """
    with open("aktools/__init__.py", "rb") as f:
        version_line = re.search(
            r"__version__\s+=\s+(.*)", f.read().decode("utf-8")
        ).group(1)
        return str(ast.literal_eval(version_line))


setuptools.setup(
    name="aktools",
    version=get_version_string(),
    author="AKFamily",
    author_email="aktools@akfamily.email.cn",
    license="MIT",
    description="AKTools is a tool for AKShare HTTP Server!",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/akfamily/aktools",
    packages=setuptools.find_packages(),
    install_requires=[
        "akshare>=1.2.55",
        "fastapi>=0.70.0",
        "uvicorn>=0.16.0"
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
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
)
