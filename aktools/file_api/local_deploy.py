# -*- coding:utf-8 -*-
# /usr/bin/env python
"""
Date: 2020/2/27 16:39
Desc:
"""
import requests
import pandas as pd


url = "http://127.0.0.1:8000/stock_em_account"
r = requests.get(url)
temp_df = pd.DataFrame.from_dict(r.json())
print(temp_df)
