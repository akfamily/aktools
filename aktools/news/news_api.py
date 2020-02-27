# -*- coding:utf-8 -*-
# /usr/bin/env python
"""
Author: Albert King
date: 2020/2/27 16:19
contact: jindaxiang@163.com
desc: 
"""
import json

import akshare as ak
from fastapi import FastAPI

app = FastAPI()


@app.get("/charity_china_trust")
async def root():
    """
    for charity_china_trust test
    :return: 慈善中国数据
    :rtype: json
    """
    return json.loads(ak.charity_china_trust().to_json())


@app.get("/stock_js_weibo_report")
async def root():
    """
    for charity_china_trust test
    :return: 慈善中国数据
    :rtype: json
    """
    return json.loads(ak.stock_js_weibo_report().to_json())


@app.get("/stock_em_account")
async def root():
    """
    for charity_china_trust test
    :return: 慈善中国数据
    :rtype: json
    """
    return json.loads(ak.stock_em_account().to_json())


@app.get("/amac_manager_xxgs_hmd")
async def root():
    """
    for charity_china_trust test
    :return: 慈善中国数据
    :rtype: json
    """
    return json.loads(ak.amac_manager_xxgs_hmd().to_json())


@app.get("/amac_person_org_list")
async def root():
    """
    for charity_china_trust test
    :return: 中国基金协会数据-人
    :rtype: json
    """
    return json.loads(ak.amac_person_org_list().to_json())


@app.get("/amac_manager_xxgs_cxdj")
async def root():
    """
    for charity_china_trust test
    :return: 中国基金协会数据-人
    :rtype: json
    """
    return json.loads(ak.amac_manager_xxgs_cxdj().to_json())


@app.get("/amac_fund_abs")
async def root():
    """
    for charity_china_trust test
    :return: 中国基金协会数据-人
    :rtype: json
    """
    return json.loads(ak.amac_fund_abs().to_json())

