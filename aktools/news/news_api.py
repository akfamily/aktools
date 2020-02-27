# -*- coding:utf-8 -*-
# /usr/bin/env python
"""
Author: Albert King
date: 2020/2/27 16:19
contact: jindaxiang@163.com
desc: 
"""
import json

from fastapi import FastAPI
import akshare as ak

app = FastAPI()


@app.get("/charity_china_trust")
async def root():
    charity_china_trust_df = ak.charity_china_trust()
    return json.loads(charity_china_trust_df.to_json())


@app.get("/stock_js_weibo_report_df")
async def root():
    stock_js_weibo_report_df = ak.stock_js_weibo_report_df()
    return json.loads(stock_js_weibo_report_df.to_json())


@app.get("/stock_em_account")
async def root():
    stock_em_account_df = ak.stock_em_account()
    return json.loads(stock_em_account_df.to_json())
