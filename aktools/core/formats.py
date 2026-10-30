# -*- coding:utf-8 -*-
# !/usr/bin/env python
"""
Date: 2026/10/30 12:00
Desc: 把接口返回的 DataFrame 转为 JSON、CSV 或 Excel
返回格式由保留参数 _format 指定，调用 AKShare 接口前会被移除；AKShare 的接口参数均不以下划线开头，不会与之冲突
"""

import io
import json
from typing import Any, List

import pandas as pd

FORMAT_PARAM = "_format"
MEDIA_TYPES = {
    "json": "application/json",
    "csv": "text/csv; charset=utf-8",
    "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
}
# Excel 单个工作表最多 1048576 行，其中 1 行是表头
EXCEL_MAX_ROWS = 1048575


class TooManyRowsError(ValueError):
    """数据行数超过 Excel 单个工作表的上限"""


def to_records(df: pd.DataFrame) -> List[Any]:
    """按行转为 JSON 可表示的对象列表，日期时间为 ISO 8601 格式"""
    return json.loads(df.to_json(orient="records", date_format="iso"))


def to_file_bytes(df: pd.DataFrame, output_format: str) -> bytes:
    """
    把数据转为 CSV 或 Excel 文件内容
    :param df: 接口返回的数据
    :type df: pandas.DataFrame
    :param output_format: csv 或 xlsx
    :type output_format: str
    :return: 文件内容
    :rtype: bytes
    :raises TooManyRowsError: 数据行数超过 Excel 单个工作表的上限
    """
    if output_format == "csv":
        # utf-8-sig 带 BOM，Excel 直接打开时中文列名不会乱码
        return df.to_csv(index=False).encode("utf-8-sig")
    if len(df) > EXCEL_MAX_ROWS:
        raise TooManyRowsError(
            f"数据共 {len(df)} 行，超过 Excel 单个工作表的上限，请改用 {FORMAT_PARAM}=csv"
        )
    # Excel 不支持带时区的时间，写入前去掉时区信息，保留当地时间
    df = df.copy()
    for column in df.columns:
        if isinstance(df[column].dtype, pd.DatetimeTZDtype):
            df[column] = df[column].dt.tz_localize(None)
    buffer = io.BytesIO()
    df.to_excel(buffer, index=False, engine="openpyxl")
    return buffer.getvalue()
