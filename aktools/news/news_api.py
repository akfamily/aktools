# -*- coding:utf-8 -*-
# /usr/bin/env python
"""
Date: 2021/12/9 19:05
Desc: HTTP 模式主文件
"""
import json
import akshare as ak

from fastapi import FastAPI

app = FastAPI()


@app.get("/{item_id}")
async def root(item_id: str, query: str = None):
    """
    接收接口名称及其参数并返回 JSON 数据
    :param item_id: 必选参数; 接口名; 比如 stock_zh_a_hist
    :type item_id: str
    :param query: 可选参数; 参数字符串; 比如 symbol="大笔买入"
    :type query: str
    :return: 指定 接口名称 和 参数 的数据
    :rtype: json
    """
    ak.__version__
    if query is None:
        return json.loads(eval("ak." + item_id + f"()").to_json())
    else:
        return json.loads(eval("ak." + item_id + f"({query})").to_json())
