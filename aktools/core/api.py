# -*- coding:utf-8 -*-
# /usr/bin/env python
"""
Date: 2021/12/9 19:05
Desc: HTTP 模式主文件
"""
import json
import urllib.parse

import akshare as ak
from fastapi import FastAPI, Request

app = FastAPI()


@app.get("/api/{item_id}")
def root(request: Request, item_id: str):
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
    decode_params = urllib.parse.unquote(str(request.query_params))
    if item_id not in interface_list:
        return {'error': '未找到该接口，请升级 AKShare 到最新版本并在文档中确认该接口的使用方式：https://www.akshare.xyz'}
    eval_str = decode_params.replace("&", '", ').replace("=", '="') + '"'
    if not bool(request.query_params):
        try:
            received_df = eval("ak." + item_id + f"()")
            if received_df is None:
                return {'error': '该接口返回数据为空，请确认参数是否正确：https://www.akshare.xyz'}
            temp_df = received_df.to_json(orient='records', date_format='iso')
        except KeyError as e:
            return {'error': f'请输入正确的参数错误 {e}，请升级 AKShare 到最新版本并在文档中确认该接口的使用方式：https://www.akshare.xyz'}
        return json.loads(temp_df)
    else:
        try:
            received_df = eval("ak." + item_id + f"({eval_str})")
            if received_df is None:
                return {'error': '该接口返回数据为空，请确认参数是否正确：https://www.akshare.xyz'}
            temp_df = received_df.to_json(orient='records', date_format='iso')
        except KeyError as e:
            return {'error': f'请输入正确的参数错误 {e}，请升级 AKShare 到最新版本并在文档中确认该接口的使用方式：https://www.akshare.xyz'}
        return json.loads(temp_df)
