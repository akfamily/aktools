# -*- coding:utf-8 -*-
# !/usr/bin/env python
"""
Date: 2026/10/29 22:00
Desc: MCP（Model Context Protocol）服务，让 Claude、Cursor 等 AI 助手通过 AKTools 获取 AKShare 数据
只提供 3 个通用工具，而不是把一千多个接口逐个注册成工具，以免撑满助手的上下文：
助手先用 search_interfaces 找到接口，再用 describe_interface 查看参数，最后用 get_data 获取数据。
需要安装可选依赖：pip install aktools[mcp]；挂载在 aktools.main 的 /mcp 路径下
"""

import contextlib
import json
from typing import Annotated, Any, AsyncIterator, Callable, Dict, Optional, Tuple, Union
from urllib.parse import urlencode

from mcp.server import MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from pydantic import Field
from starlette.applications import Starlette

import aktools
from aktools.core.api import FORMAT_PARAM, InterfaceError, fetch_dataframe
from aktools.core.catalog import describe_interface as _describe_interface
from aktools.core.catalog import is_interface, list_interfaces

# 搜索结果最多返回的条数；关键词很宽泛时（如 stock）可能匹配数百个接口
SEARCH_LIMIT = 50
# get_data 默认与最多返回的行数，完整数据可通过返回的 csv_url 下载
DEFAULT_ROWS = 100
MAX_ROWS = 1000

INSTRUCTIONS = """AKTools 提供 AKShare 的一千多个财经数据接口（股票、期货、期权、基金、债券、外汇、宏观等）。
使用步骤：
1. 用 search_interfaces 按中文关键词或接口名搜索，例如“个股的历史行情”“交易日历”“stock_zh_a”
2. 用 describe_interface 查看接口的参数、默认值和说明
3. 用 get_data 传入接口名和参数获取数据；数据量大时只返回前若干行，完整数据可通过 csv_url 下载
参数值一律按文本传给 AKShare，日期通常写成 20240101 的形式。"""

mcp = MCPServer(
    "AKTools",
    instructions=INSTRUCTIONS,
    version=aktools.__version__,
    website_url="https://aktools.akfamily.xyz/",
)


@mcp.tool()
def search_interfaces(
    keyword: Annotated[
        str,
        Field(description="关键词，匹配接口名或中文标题，如“历史行情”“交易日历”"),
    ],
) -> Dict[str, Any]:
    """按关键词搜索 AKShare 数据接口，返回接口名与中文标题。结果较多时只返回前 50 个，请换用更具体的关键词"""
    items = list_interfaces(keyword)
    return {"total": len(items), "items": items[:SEARCH_LIMIT]}


@mcp.tool()
def describe_interface(
    name: Annotated[str, Field(description="接口名，如 stock_zh_a_hist")],
) -> Dict[str, Any]:
    """查看接口的标题、数据源地址，以及各参数的默认值、类型和说明"""
    info = _describe_interface(name)
    if info is None:
        raise ToolError(f"未找到接口 {name}，请先用 search_interfaces 搜索正确的接口名")
    return info


@mcp.tool()
def get_data(
    name: Annotated[str, Field(description="接口名，如 stock_zh_a_hist")],
    params: Annotated[
        Optional[Dict[str, Union[str, int, float, bool]]],
        Field(
            description='接口参数，如 {"symbol": "000001", "start_date": "20240101"}'
        ),
    ] = None,
    max_rows: Annotated[
        int, Field(ge=1, le=MAX_ROWS, description="最多返回的行数，默认 100")
    ] = DEFAULT_ROWS,
) -> Dict[str, Any]:
    """调用 AKShare 接口获取数据。数据量大时只返回前 max_rows 行，并给出总行数与完整数据的 CSV 下载地址"""
    if not is_interface(name):
        raise ToolError(f"未找到接口 {name}，请先用 search_interfaces 搜索正确的接口名")
    # 与 HTTP 接口一致：参数值一律按文本传给 AKShare
    text_params = {key: str(value) for key, value in (params or {}).items()}
    try:
        df, _ = fetch_dataframe(name, text_params)
    except InterfaceError as e:
        raise ToolError(e.message) from e
    rows = json.loads(df.head(max_rows).to_json(orient="records", date_format="iso"))
    query = urlencode({**text_params, FORMAT_PARAM: "csv"})
    return {
        "name": name,
        "total_rows": len(df),
        "returned_rows": len(rows),
        "truncated": len(df) > len(rows),
        "columns": [str(column) for column in df.columns],
        "rows": rows,
        "csv_url": f"/api/public/{name}?{query}",
    }


def build_mcp_app(
    host: str,
) -> Tuple[Starlette, Callable[[Any], contextlib.AbstractAsyncContextManager]]:
    """
    构建 MCP 应用，以及启动其会话管理器的 lifespan
    Starlette 不会运行子应用的 lifespan，宿主应用必须使用这里返回的 lifespan，
    否则第一个请求就会报错；会话管理器只能启动一次，因此每次构建都返回各自的 lifespan
    :param host: 服务的监听地址。为 127.0.0.1 / localhost / ::1 时只接受发往本机的请求，
                 防止 DNS 重绑定攻击；为 0.0.0.0 等其他地址时允许局域网访问
    :type host: str
    :return: (MCP 应用, lifespan)
    :rtype: tuple
    """
    # stateless_http：每个请求独立处理，不保存会话；本服务的工具都是一次性查询，不需要会话状态。
    # 端点路径为 /mcp，宿主应用须以精确路由 Route("/mcp", endpoint=app) 接入而不是 Mount：
    # Mount 会把 /mcp 重定向到 /mcp/，而 MCP 客户端不一定会跟随 POST 的重定向
    app = mcp.streamable_http_app(
        streamable_http_path="/mcp", stateless_http=True, host=host
    )
    session_manager = mcp.session_manager

    @contextlib.asynccontextmanager
    async def lifespan(_app) -> AsyncIterator[None]:
        async with session_manager.run():
            yield

    return app, lifespan
