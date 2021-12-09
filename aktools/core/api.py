# -*- coding:utf-8 -*-
# /usr/bin/env python
"""
Date: 2021/12/9 19:05
Desc: HTTP 模式主文件
"""
import json
import akshare as ak

from fastapi import FastAPI, Request

app = FastAPI()


@app.get("/{item_id}")
async def root(request: Request, item_id: str):
    """
    接收接口名称及其参数并返回 JSON 数据
    :param request: 请求信息
    :type request: Request
    :param item_id: 必选参数; 接口名; 比如 stock_zh_a_hist
    :type item_id: str
    :return: 指定 接口名称 和 参数 的数据
    :rtype: json
    """
    interface_list = dir(ak)
    if item_id not in interface_list:
        return {'error': '没有该接口'}
    eval_str = str(request.query_params).replace("&", '", ').replace("=", '="') + '"'
    if not bool(request.query_params):
        return json.loads(eval("ak." + item_id + f"()").to_json())
    else:
        return json.loads(eval("ak." + item_id + f"({eval_str})").to_json())
