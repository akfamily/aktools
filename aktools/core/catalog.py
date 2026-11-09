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
from urllib.parse import urlparse

import akshare as ak

PARAM_RE = re.compile(r"^:param\s+(\w+)\s*:\s*(.*)$")
TYPE_RE = re.compile(r"^:type\s+(\w+)\s*:\s*(.*)$")

# AKShare 接口登记中 rate_limit 字段的取值：请求东方财富 push2 行情服务器的接口。
# 这类服务器在短时间内请求较多时会临时封禁来源 IP，首次约 5 分钟恢复，期间所有
# 东方财富行情接口都无法使用；东方财富数据中心、基金、F10 等其他服务器不受影响
EASTMONEY_PUSH2 = "eastmoney_push2"
PUSH2_SOURCE = "东方财富·行情（频繁访问易限流）"

# 数据源域名 -> 中文名称，按域名后缀匹配；未列出的域名直接显示域名
SOURCE_NAMES = (
    ("eastmoney.com", "东方财富"),
    ("sina.com.cn", "新浪财经"),
    ("sina.com", "新浪财经"),
    ("10jqka.com.cn", "同花顺"),
    ("qq.com", "腾讯"),
    ("gtimg.cn", "腾讯"),
    ("xueqiu.com", "雪球"),
    ("baidu.com", "百度"),
    ("jin10.com", "金十数据"),
    ("cninfo.com.cn", "巨潮资讯"),
    ("legulegu.com", "乐咕乐股"),
    ("csindex.com.cn", "中证指数"),
    ("cnindex.com.cn", "国证指数"),
    ("swsresearch.com", "申万宏源研究"),
    ("sse.com.cn", "上海证券交易所"),
    ("szse.cn", "深圳证券交易所"),
    ("bse.cn", "北京证券交易所"),
    ("cffex.com.cn", "中国金融期货交易所"),
    ("shfe.com.cn", "上海期货交易所"),
    ("dce.com.cn", "大连商品交易所"),
    ("czce.com.cn", "郑州商品交易所"),
    ("gfex.com.cn", "广州期货交易所"),
    ("chinamoney.com.cn", "中国货币网"),
    ("stats.gov.cn", "国家统计局"),
    ("pbc.gov.cn", "中国人民银行"),
    ("amac.org.cn", "中国证券投资基金业协会"),
)

# 查找其他来源的同类接口时，接口名末尾的数据源缩写不参与前缀比较
SOURCE_SUFFIXES = {"em", "sina", "ths", "tx", "xq", "cninfo", "lg", "cx", "sw", "cni"}
# 标题中的来源与栏目名称不能体现数据内容，检索同类接口前先去掉
TITLE_NOISE_RE = re.compile(r"东方财富网?|行情中心|数据中心|[-—_()（）；;，,。]")
ALTERNATIVES_LIMIT = 3


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
        "source": source_of(name),
        "source_url": parsed["source_url"],
        # 访问限制，取自 AKShare 的接口登记；"eastmoney_push2" 表示频繁访问会被东方财富临时限流
        "rate_limit": registered.get("rate_limit"),
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


def rate_limit_of(name: str) -> Optional[str]:
    """
    接口的访问限制，取自 AKShare 接口登记的 rate_limit 字段
    旧版 AKShare 的登记没有这个字段，此时返回 None，即按不限流处理
    :param name: 接口名
    :type name: str
    :return: 如 "eastmoney_push2"；没有限制或未登记时为 None
    :rtype: str
    """
    return _registry_info(name).get("rate_limit")


def source_of(name: str) -> str:
    """
    接口的数据来源，用中文名称表示，如“新浪财经”“东方财富”
    数据源地址优先取 AKShare 登记的 url，没有时取 docstring 第二行；
    请求东方财富 push2 行情服务器的接口单独标出，以便与不限流的东方财富数据中心区分
    :param name: 接口名
    :type name: str
    :return: 来源名称；无法判断时为空字符串
    :rtype: str
    """
    registered = _registry_info(name)
    if registered.get("rate_limit") == EASTMONEY_PUSH2:
        return PUSH2_SOURCE
    url = registered.get("url") or ""
    if not url:
        func = getattr(ak, name, None)
        url = parse_docstring(inspect.getdoc(func) or "")["source_url"] if func else ""
    host = (urlparse(url).hostname or "").lower()
    if not host:
        return ""
    for domain, label in SOURCE_NAMES:
        if host == domain or host.endswith("." + domain):
            return label
    return host.removeprefix("www.")


def _name_tokens(name: str) -> List[str]:
    """接口名按下划线切分，去掉末尾的数据源缩写，如 stock_zh_a_spot_em -> stock zh a spot"""
    tokens = name.split("_")
    return tokens[:-1] if tokens[-1] in SOURCE_SUFFIXES else tokens


def _common_prefix(a: str, b: str) -> int:
    """两个接口名开头有几段相同，如 stock_zh_a_hist 与 stock_zh_a_daily 为 3"""
    count = 0
    for x, y in zip(_name_tokens(a), _name_tokens(b)):
        if x != y:
            break
        count += 1
    return count


def find_alternatives(name: str) -> List[Dict[str, str]]:
    """
    为东方财富行情接口推测其他来源的同类接口，供被限流时参考
    用去掉来源词的标题调用 ak.search，只保留同类目、且不请求 push2 行情服务器的接口，
    并要求接口名前缀至少 3 段相同，或 2 段相同且匹配分不低于 20；把握不大时宁可不给。
    结果是按名称与描述推测的，参数与返回列可能不同，调用前需要查看参数说明
    :param name: 接口名，如 stock_zh_a_hist
    :type name: str
    :return: 最多 3 个 {"name": 接口名, "title": 标题, "source": 来源}
    :rtype: list
    """
    search = getattr(ak, "search", None)
    registered = _registry_info(name)
    if search is None or not registered:
        return []
    title = (
        registered.get("desc")
        or parse_docstring(inspect.getdoc(getattr(ak, name, None)) or "")["title"]
    )
    query = " ".join(TITLE_NOISE_RE.sub(" ", title).split())
    if not query:
        return []
    try:
        found = search(query, limit=300)
    except Exception:
        return []
    if found is None or "接口名" not in found:
        return []
    candidates = []
    for _, row in found.iterrows():
        candidate = row["接口名"]
        if candidate == name or not is_interface(candidate):
            continue
        info = _registry_info(candidate)
        if info.get("category") != registered.get("category"):
            continue
        if info.get("rate_limit") == EASTMONEY_PUSH2:
            continue
        prefix = _common_prefix(name, candidate)
        score = float(row.get("匹配分", 0) or 0)
        if prefix >= 3 or (prefix >= 2 and score >= 20):
            candidates.append((-prefix, -score, candidate))
    titles = {item["name"]: item["title"] for item in _all_interfaces()}
    return [
        {"name": n, "title": titles.get(n, ""), "source": source_of(n)}
        for _, _, n in sorted(candidates)[:ALTERNATIVES_LIMIT]
    ]


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
    :return: (匹配总数, [{"name": 接口名, "title": 标题, "category": 类目, "source": 来源}])
    :rtype: tuple
    """
    total, items = _search(keyword, limit)
    # 只为返回的条目查来源，不为全部匹配结果查
    return total, [{**item, "source": source_of(item["name"])} for item in items]


def _search(keyword: str, limit: int) -> Tuple[int, List[Dict[str, str]]]:
    """search_interfaces 的检索部分，不含来源"""
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
