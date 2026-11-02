# -*- coding:utf-8 -*-
# !/usr/bin/env python
"""
Date: 2026/10/29 22:00
Desc: MCP（Model Context Protocol）服务，让 Claude、Cursor 等 AI 助手通过 AKTools 获取 AKShare 数据
只提供 3 个通用工具，而不是把一千多个接口逐个注册成工具，以免撑满助手的上下文：
助手先用 search_interfaces 找到接口，再用 describe_interface 查看参数，最后用 get_data 获取数据。
两种运行方式：随 HTTP 服务挂载在 aktools.main 的 /mcp 路径下；或以 aktools-mcp 命令通过 stdio 运行，
由 AI 助手自行启动，不需要先运行 HTTP 服务
"""

import contextlib
import io
import json
import logging
import sys
from typing import Annotated, Any, AsyncIterator, Callable, Dict, Optional, Tuple, Union
from urllib.parse import urlencode

from mcp.server import MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from mcp.types import ToolAnnotations
from pydantic import Field
from starlette.applications import Starlette

import aktools
from aktools.core.fetch import InterfaceError, fetch_dataframe
from aktools.core.formats import FORMAT_PARAM
from aktools.core.catalog import describe_interface as _describe_interface
from aktools.core.catalog import is_interface
from aktools.core.catalog import search_interfaces as _search_interfaces

# 搜索结果最多返回的条数；关键词很宽泛时（如 stock）可能匹配数百个接口
SEARCH_LIMIT = 50
# get_data 默认与最多返回的行数，完整数据可通过返回的 csv_url 下载
DEFAULT_ROWS = 100
MAX_ROWS = 1000
# stdio 方式运行时没有 HTTP 服务，get_data 不提供 CSV 下载地址；由 main() 关闭
_csv_url_enabled = True

INSTRUCTIONS = """AKTools 提供 AKShare 的一千多个财经数据接口（股票、期货、期权、基金、债券、外汇、宏观等）。
使用步骤：
1. 用 search_interfaces 搜索接口，可用多个关键词，例如“A股 日线”“交易日历”“期货持仓”“stock_zh_a”
2. 用 describe_interface 查看接口的参数、默认值、返回列与调用示例
3. 用 get_data 传入接口名和参数获取数据；数据量大时一次最多返回 max_rows 行，
   用 offset 翻页，offset 为负数时从末尾倒数（按日期升序的数据，最新的行在末尾，如 offset=-20 取最近 20 行）
参数值一律按文本传给 AKShare，日期通常写成 20240101 的形式。"""


def _create_server() -> MCPServer:
    """
    创建 MCPServer，且不改动根日志记录器
    SDK 在构造时调用 logging.basicConfig(level=INFO)，会让 python -m aktools 的每次请求都多打一行日志，
    也会接管嵌入 AKTools 的程序的日志配置；因此构造后恢复根日志记录器原有的处理器与级别
    """
    root = logging.getLogger()
    handlers, level = list(root.handlers), root.level
    try:
        return MCPServer(
            "AKTools",
            instructions=INSTRUCTIONS,
            version=aktools.__version__,
            website_url="https://aktools.akfamily.xyz/",
        )
    finally:
        root.handlers[:] = handlers
        root.setLevel(level)


mcp = _create_server()

# 三个工具都只读取数据：不修改任何状态，可重复调用，会访问外部数据源
READ_ONLY = ToolAnnotations(
    read_only_hint=True,
    destructive_hint=False,
    idempotent_hint=True,
    open_world_hint=True,
)


@mcp.tool(annotations=READ_ONLY)
def search_interfaces(
    keyword: Annotated[
        str,
        Field(
            description="关键词，多个关键词用空格分隔，如“A股 日线”“交易日历”“期货持仓”"
        ),
    ],
) -> Dict[str, Any]:
    """按关键词搜索 AKShare 数据接口，结果按相关度排序，返回接口名、中文标题与类目。最多返回前 50 个"""
    total, items = _search_interfaces(keyword, SEARCH_LIMIT)
    return {"total": total, "items": items}


@mcp.tool(annotations=READ_ONLY)
def describe_interface(
    name: Annotated[str, Field(description="接口名，如 stock_zh_a_hist")],
) -> Dict[str, Any]:
    """查看接口的标题、数据源地址、各参数的默认值、类型和说明，以及返回列、数据范围说明与调用示例"""
    info = _describe_interface(name)
    if info is None:
        raise ToolError(f"未找到接口 {name}，请先用 search_interfaces 搜索正确的接口名")
    return info


@mcp.tool(annotations=READ_ONLY)
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
    offset: Annotated[
        int,
        Field(
            description="从第几行开始返回（从 0 开始）；负数表示从末尾倒数，如 -20 取最后 20 行"
        ),
    ] = 0,
) -> Dict[str, Any]:
    """调用 AKShare 接口获取数据。一次最多返回 max_rows 行，用 offset 翻页或取最后若干行；返回总行数与本次的起始行，随 HTTP 服务运行时还给出完整数据的 CSV 下载地址"""
    if not is_interface(name):
        raise ToolError(f"未找到接口 {name}，请先用 search_interfaces 搜索正确的接口名")
    # 与 HTTP 接口一致：参数值一律按文本传给 AKShare
    text_params = {key: str(value) for key, value in (params or {}).items()}
    try:
        df, _ = fetch_dataframe(name, text_params)
    except InterfaceError as e:
        raise ToolError(e.message) from e
    # 负数从末尾倒数；越界时夹到表的范围内，与 Python 切片的语义一致
    start = max(len(df) + offset, 0) if offset < 0 else min(offset, len(df))
    page = df.iloc[start : start + max_rows]
    rows = json.loads(page.to_json(orient="records", date_format="iso"))
    query = urlencode({**text_params, FORMAT_PARAM: "csv"})
    return {
        "name": name,
        "total_rows": len(df),
        "offset": start,
        "returned_rows": len(rows),
        # 本次返回的不是完整的表
        "truncated": len(df) > len(rows),
        "columns": [str(column) for column in df.columns],
        "rows": rows,
        "csv_url": f"/api/public/{name}?{query}" if _csv_url_enabled else None,
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


def main() -> None:
    """
    aktools-mcp 命令的入口：通过 stdio 运行 MCP 服务，由 AI 助手自行启动
    stdio 方式下 stdout 专门传输协议消息。会话期间 MCP SDK 把文件描述符 1 转到 stderr，
    协议消息另走一个复制出的描述符；但 print 写入的是 Python 的输出缓冲区，
    若在会话结束、描述符恢复后才刷新，AKShare 接口中 print 的内容就会混进协议通道。
    因此换成无缓冲的 stdout，让每次写入立即落到描述符 1，会话期间自然进入 stderr
    """
    global _csv_url_enabled
    _csv_url_enabled = False
    sys.stdout.flush()
    sys.stdout = io.TextIOWrapper(
        io.FileIO(sys.stdout.fileno(), "w", closefd=False),
        encoding="utf-8",
        errors="replace",
        write_through=True,
    )
    mcp.run("stdio")


if __name__ == "__main__":
    main()
