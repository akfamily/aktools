# -*- coding:utf-8 -*-
# /usr/bin/env python
"""
Date: 2022/9/28 12:05
Desc: scheme 模型层
"""
from pydantic import BaseModel


class VersionBase(BaseModel):
    ak_current_version: str = "1.7.30"
    ak_latest_version: str = "1.7.30"
    at_current_version: str = "0.0.75"
    at_latest_version: str = "0.0.75"
