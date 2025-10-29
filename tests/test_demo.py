# -*- coding:utf-8 -*-
# /usr/bin/env python
"""
Date: 2025/10/29 17:20
Desc: Just for test file
"""
import akshare as ak


def test_demo():
    """
    Just for test
    :return: Error
    :rtype: assert result
    """
    stock_zh_a_hist_df = ak.stock_zh_a_hist()
    assert stock_zh_a_hist_df.shape[0] != 0


if __name__ == "__main__":
    test_demo()
