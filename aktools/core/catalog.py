# -*- coding:utf-8 -*-
# !/usr/bin/env python
"""
Date: 2026/10/29 20:00
Desc: 接口目录与参数说明
只读取 AKShare 接口的函数签名与 docstring，不实际调用接口，因此不需要联网。
AKShare 的 docstring 约定为：首行是中文标题，第二行是数据源地址，
随后是 ":param 参数名: 说明" 与 ":type 参数名: 类型"
"""

import inspect
import re
from functools import lru_cache
from typing import Dict, List, Optional, Tuple

import akshare as ak

PARAM_RE = re.compile(r"^:param\s+(\w+)\s*:\s*(.*)$")
TYPE_RE = re.compile(r"^:type\s+(\w+)\s*:\s*(.*)$")


def is_interface(name: str) -> bool:
    """
    判断名称是否为 AKShare 的数据接口
    AKShare 顶层还导出了子模块与类，它们不是数据接口；
    部分接口被 functools.lru_cache 包装，不是普通函数但同样可调用
    :param name: 接口名
    :type name: str
    :return: 是否为数据接口
    :rtype: bool
    """
    if name.startswith("_"):
        return False
    obj = getattr(ak, name, None)
    return callable(obj) and not inspect.isclass(obj)


def parse_docstring(doc: str) -> Dict:
    """
    按 AKShare 的 docstring 约定解析标题、数据源地址与参数说明
    :param doc: 经 inspect.getdoc 清理缩进后的 docstring
    :type doc: str
    :return: {"title": ..., "source_url": ..., "params": {参数名: {"description", "type"}}}
    :rtype: dict
    """
    lines = [line.strip() for line in doc.splitlines() if line.strip()]
    title = lines[0] if lines and not lines[0].startswith(":") else ""
    source_url = ""
    if len(lines) > 1 and lines[1].startswith("http"):
        source_url = lines[1]
    params: Dict[str, Dict[str, str]] = {}
    for line in lines:
        for regex, key in ((PARAM_RE, "description"), (TYPE_RE, "type")):
            match = regex.match(line)
            if match:
                entry = params.setdefault(
                    match.group(1), {"description": "", "type": ""}
                )
                entry[key] = match.group(2).strip()
    return {"title": title, "source_url": source_url, "params": params}


def _json_default(value):
    """默认值只保留 JSON 可表示的基本类型，其余转为字符串"""
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    return str(value)


def _annotation_name(annotation) -> str:
    if annotation is inspect.Parameter.empty:
        return ""
    return getattr(annotation, "__name__", str(annotation))


def describe_interface(name: str) -> Optional[Dict]:
    """
    返回单个接口的说明：标题、数据源地址、调用地址与各参数的默认值、类型和说明
    :param name: 接口名，如 stock_zh_a_hist
    :type name: str
    :return: 接口说明；不是数据接口时返回 None
    :rtype: dict
    """
    if not is_interface(name):
        return None
    func = getattr(ak, name)
    doc = inspect.getdoc(func) or ""
    parsed = parse_docstring(doc)
    params: List[Dict] = []
    for param in inspect.signature(func).parameters.values():
        if param.kind in (param.VAR_POSITIONAL, param.VAR_KEYWORD):
            continue
        documented = parsed["params"].get(param.name, {})
        required = param.default is inspect.Parameter.empty
        params.append(
            {
                "name": param.name,
                "default": None if required else _json_default(param.default),
                "required": required,
                # docstring 中的类型说明通常比注解更具体，如 "str or None"
                "type": documented.get("type") or _annotation_name(param.annotation),
                "description": documented.get("description", ""),
            }
        )
    registered = _registry_info(name)
    return {
        "name": name,
        "title": parsed["title"],
        "source_url": parsed["source_url"],
        "url": f"/api/public/{name}",
        "params": params,
        # 以下三项取自 AKShare 的接口注册表（ak.interface_info），未登记的接口为空
        "outputs": [
            {key: column.get(key, "") for key in ("name", "type", "desc")}
            for column in registered.get("outputs") or []
        ],
        "limit_desc": registered.get("limit_desc") or "",
        "example": registered.get("example") or "",
        "doc": doc,
    }


def _registry_info(name: str) -> Dict:
    """
    AKShare 注册表中登记的接口信息：返回列、数据范围说明与调用示例
    AKShare 1.20.13 起提供 ak.interface_info；没有该函数或接口未登记时返回空字典
    """
    interface_info = getattr(ak, "interface_info", None)
    if interface_info is None:
        return {}
    try:
        return interface_info(name) or {}
    except Exception:
        return {}


@lru_cache(maxsize=1)
def _all_interfaces() -> List[Dict[str, str]]:
    """全部接口的名称与标题；AKShare 在服务运行期间不会变化，解析一次即可"""
    items = []
    for name in dir(ak):
        if is_interface(name):
            doc = inspect.getdoc(getattr(ak, name)) or ""
            items.append({"name": name, "title": parse_docstring(doc)["title"]})
    return items


def list_interfaces(q: str = "") -> List[Dict[str, str]]:
    """
    列出全部接口，可按关键词过滤
    :param q: 关键词，匹配接口名或中文标题，不区分大小写
    :type q: str
    :return: [{"name": 接口名, "title": 标题}]
    :rtype: list
    """
    keyword = q.strip().lower()
    if not keyword:
        return list(_all_interfaces())
    return [
        item
        for item in _all_interfaces()
        if keyword in item["name"].lower() or keyword in item["title"].lower()
    ]


def search_interfaces(keyword: str, limit: int) -> Tuple[int, List[Dict[str, str]]]:
    """
    按关键词检索接口，结果按相关度排序，供 MCP 的 search_interfaces 工具使用
    优先使用 AKShare 的 ak.search：支持“A股 日线”这类多个关键词，并按接口名、描述、
    返回列等综合打分；没有 ak.search 或其未找到结果时，退回接口名与标题的子串匹配
    :param keyword: 关键词，多个关键词用空格分隔
    :type keyword: str
    :param limit: 最多返回的条数
    :type limit: int
    :return: (匹配总数, [{"name": 接口名, "title": 标题, "category": 类目}])
    :rtype: tuple
    """
    titles = {item["name"]: item["title"] for item in _all_interfaces()}
    search = getattr(ak, "search", None)
    if search is not None and keyword.strip():
        try:
            found = search(keyword, limit=len(titles))
        except Exception:
            found = None
        if found is not None and len(found) and "接口名" in found:
            items = [
                {
                    "name": row["接口名"],
                    "title": titles.get(row["接口名"]) or str(row.get("描述", "")),
                    "category": str(row.get("类目", "")),
                }
                for _, row in found.iterrows()
                if row["接口名"] in titles
            ]
            if items:
                return len(items), items[:limit]
    items = [{**item, "category": ""} for item in list_interfaces(keyword)]
    return len(items), items[:limit]
