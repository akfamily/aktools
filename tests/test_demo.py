# -*- coding:utf-8 -*-
# /usr/bin/env python
"""
Date: 2021/12/9 17:20
Desc: Just for test file
"""
import akshare as ak


def test_demo():
    """
    Just for test
    :return: Error
    :rtype: assert result
    """
    cost_living_df = ak.cost_living()
    assert cost_living_df.shape[0] != 0


if __name__ == "__main__":
    test_demo()
