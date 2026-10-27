# -*- coding:utf-8 -*-
# !/usr/bin/env python
"""
Date: 2025/9/26 15:05
Desc: Vercel Entrypoint
"""

from aktools.main import app

# Vercel 从本文件中查找名为 app 的 ASGI 应用
__all__ = ["app"]
