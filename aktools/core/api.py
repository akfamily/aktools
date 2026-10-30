# -*- coding:utf-8 -*-
# /usr/bin/env python
"""
Date: 2024/1/12 22:05
Desc: HTTP 路由：获取数据（/api/public）与接口目录（/api/interfaces）
取数逻辑见 aktools.core.fetch，格式转换见 aktools.core.formats
"""

from fastapi import APIRouter, Query, Request, status
from fastapi.responses import JSONResponse, Response

from aktools.core.catalog import describe_interface, list_interfaces
from aktools.core.fetch import DOC_URL, InterfaceError, fetch_dataframe
from aktools.core.formats import (
    FORMAT_PARAM,
    MEDIA_TYPES,
    TooManyRowsError,
    to_file_bytes,
    to_records,
)
from aktools.core.log import logger

app_core = APIRouter()

# 响应头，标明本次数据是否来自结果缓存：hit 或 miss
CACHE_HEADER = "X-AKTools-Cache"


def _error_response(
    message: str, status_code: int = status.HTTP_404_NOT_FOUND
) -> JSONResponse:
    """构造统一的错误响应"""
    return JSONResponse(status_code=status_code, content={"error": message})


def call_interface(item_id: str, request: Request) -> Response:
    """
    根据接口名与查询参数调用对应的 AKShare 接口并返回数据
    默认返回 JSON；查询参数 _format=csv 或 _format=xlsx 时返回文件下载
    :param request: 请求信息，查询参数即接口参数，如 symbol=000001
    :type request: Request
    :param item_id: 接口名，如 stock_zh_a_hist
    :type item_id: str
    :return: 接口数据或错误信息
    :rtype: Response
    """
    # FastAPI 已对查询串完成 URL 解码，参数值按第一个 = 切分，cookie 等含 = 的值也能正确取出
    params = dict(request.query_params)
    output_format = params.pop(FORMAT_PARAM, "json").lower()
    # 先校验格式再调用接口，避免格式写错时白白请求一次上游网站
    if output_format not in MEDIA_TYPES:
        return _error_response(
            f"不支持的返回格式 {output_format}，{FORMAT_PARAM} 可选值为：{'、'.join(MEDIA_TYPES)}",
            status_code=status.HTTP_400_BAD_REQUEST,
        )
    try:
        df, cache_status = fetch_dataframe(item_id, params)
    except InterfaceError as e:
        return _error_response(e.message, status_code=e.status_code)
    try:
        if output_format == "json":
            body = None
            content = to_records(df)
        else:
            body = to_file_bytes(df, output_format)
    except TooManyRowsError as e:
        return _error_response(str(e), status_code=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.info(f"接口 {item_id} 的数据转换为 {output_format} 失败：{e}")
        return _error_response(
            f"数据转换为 {output_format} 格式失败：{e}，可以改用 {FORMAT_PARAM}=json 获取数据",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
    logger.info(f"获取到 {item_id} 的数据，格式 {output_format}，缓存 {cache_status}")
    if body is None:
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=content,
            headers={CACHE_HEADER: cache_status},
        )
    return Response(
        content=body,
        media_type=MEDIA_TYPES[output_format],
        headers={
            "Content-Disposition": f'attachment; filename="{item_id}.{output_format}"',
            CACHE_HEADER: cache_status,
        },
    )


@app_core.get(
    path="/public/{item_id}",
    description="调用与 item_id 同名的 AKShare 接口，接口参数以查询字符串传递，如 ?symbol=000001",
    summary="获取数据",
)
def public_root(
    request: Request,
    item_id: str,
    # 只用于在 /docs 中展示该参数；实际取值由 call_interface 从查询参数中读取
    output_format: str = Query(
        "json",
        alias=FORMAT_PARAM,
        description="返回格式：json（默认）、csv 或 xlsx，csv 与 xlsx 以文件形式下载",
    ),
):
    """
    公开接口，接收接口名与参数并返回 JSON 数据
    :param request: 请求信息
    :type request: Request
    :param item_id: 接口名，如 stock_zh_a_hist
    :type item_id: str
    :return: 指定接口名与参数的数据
    :rtype: JSONResponse
    """
    return call_interface(item_id, request)


@app_core.get(
    path="/interfaces",
    description="列出全部 AKShare 数据接口的名称与中文标题，可用 q 按接口名或标题过滤",
    summary="接口目录",
)
def interfaces(
    q: str = Query("", description="关键词，匹配接口名或中文标题，如 历史行情"),
):
    return list_interfaces(q)


@app_core.get(
    path="/interfaces/{item_id}",
    description="返回接口的标题、数据源地址、调用地址，以及各参数的默认值、类型和说明",
    summary="接口参数说明",
)
def interface_detail(item_id: str):
    info = describe_interface(item_id)
    if info is None:
        return _error_response(
            f"未找到该接口，请升级 AKShare 到最新版本或通过 /api/interfaces 查找接口名：{DOC_URL}"
        )
    return info
