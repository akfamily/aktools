# -*- coding:utf-8 -*-
# /usr/bin/env python
"""
Date: 2022/9/28 12:05
Desc: /version 接口的响应模型
"""

from pydantic import BaseModel


class VersionBase(BaseModel):
    ak_current_version: str
    ak_latest_version: str
    at_current_version: str
    at_latest_version: str
