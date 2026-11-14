# -*- coding:utf-8 -*-
# !/usr/bin/env python
"""
Date: 2026/10/29 20:00
Desc: 接口目录与参数说明
只读取 AKShare 接口的函数签名与 docstring，不实际调用接口，因此不需要联网。
AKShare 的 docstring 约定为：首行是中文标题，第二行是数据源地址，
随后是 ":param 参数名: 说明" 与 ":type 参数名: 类型"
"""

import difflib
import inspect
import re
from functools import lru_cache
from typing import Dict, FrozenSet, List, Optional, Tuple
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
    ("1234567.com.cn", "天天基金网"),
    ("danjuanfunds.com", "雪球基金"),
    ("futunn.com", "富途牛牛"),
    ("jisilu.cn", "集思录"),
    ("optbbs.com", "期权论坛"),
    ("ccxe.com.cn", "财新数据"),
    ("caixin.com", "财新数据"),
    ("cls.cn", "财联社"),
    ("wallstreetcn.com", "华尔街见闻"),
    ("chinascope.com", "数库"),
    ("joinquant.com", "聚宽"),
    ("swhyresearch.com", "申万宏源研究"),
    ("ccidx.com", "中证商品指数"),
    ("chinabond.com.cn", "中国债券信息网"),
    ("nafmii.org.cn", "中国银行间市场交易商协会"),
    ("safe.gov.cn", "国家外汇管理局"),
    ("sse.org.cn", "深圳证券交易所"),
    ("sge.com.cn", "上海黄金交易所"),
    ("ine.cn", "上海国际能源交易中心"),
    ("gtjaqh.com", "国泰君安期货"),
    ("9qihuo.com", "九期网"),
    ("99qh.com", "99 期货网"),
    ("100ppi.com", "生意社"),
    ("soozhu.com", "搜猪"),
    ("zhuwang.com.cn", "玄田数据"),
    ("msweet.com.cn", "沐甜科技"),
    ("cpcadata.com", "乘联会"),
    ("endata.com.cn", "艺恩"),
    ("endata.cn", "艺恩"),
)

DOC_URL = "https://akshare.akfamily.xyz"

# 接口名写错时，最多给出几个名称相近的接口
SIMILAR_LIMIT = 3


@lru_cache(maxsize=1)
def _registered_names() -> FrozenSet[str]:
    """
    AKShare 接口登记中的全部接口名；AKShare 在服务运行期间不会变化，读取一次即可
    登记只收录数据接口，不含 set_proxies、set_timeout、set_token、pro_api 等设置函数，
    也不含 search、interface_info 等检索函数
    """
    names = set()
    for name in dir(ak):
        if name.startswith("_"):
            continue
        try:
            ak.interface_info(name)
        except Exception:
            continue
        names.add(name)
    return frozenset(names)


def is_interface(name: str) -> bool:
    """
    判断名称是否为 AKShare 的数据接口
    以 AKShare 的接口登记为准，只有登记在册的接口才能被调用（白名单）。
    不能只看它是不是 akshare 顶层的可调用对象：AKShare 顶层还导出了 set_proxies、
    set_timeout、set_token 等设置函数，经 /api/public 或 MCP 调用它们会改掉整个服务的
    代理、超时与令牌，任何能访问服务的人都可以借此把上游请求转到自己指定的代理
    :param name: 接口名
    :type name: str
    :return: 是否为数据接口
    :rtype: bool
    """
    if name.startswith("_") or name not in _registered_names():
        return False
    # 部分接口被 functools.lru_cache 包装，不是普通函数但同样可调用
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
    :param name: 接口名，如 stock_zh_a_hist_em
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
        # 来自其他数据源的同类接口，取自 AKShare 人工维护的对照表；参数与返回列可能不同
        "alternatives": [
            {"name": item["name"], "title": item["title"], "source": item["source"]}
            for item in registered_alternatives(name)
        ],
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


def registered_alternatives(name: str) -> List[Dict[str, Optional[str]]]:
    """
    AKShare 登记的同类接口：来自其他数据源、内容属于同一类的接口
    取自 AKShare 接口登记的 alternatives 字段（1.20.39 起提供，人工维护）；AKTools 不自行推测，
    按名称与描述猜测时会把 ST 股票列表配给日线、把 B 股配给科创板。旧版 AKShare 没有该字段时为空
    :param name: 接口名，如 stock_zh_a_hist_em
    :type name: str
    :return: [{"name": 接口名, "title": 标题, "source": 来源, "rate_limit": 访问限制}]
    :rtype: list
    """
    titles = {item["name"]: item["title"] for item in _all_interfaces()}
    return [
        {
            "name": other,
            "title": titles.get(other, ""),
            "source": source_of(other),
            "rate_limit": rate_limit_of(other),
        }
        for other in _registry_info(name).get("alternatives") or []
        if is_interface(other)
    ]


def find_alternatives(name: str) -> List[Dict[str, Optional[str]]]:
    """
    东方财富行情接口被限流时可以改用的同类接口
    即 registered_alternatives 中不请求东方财富 push2 行情服务器的那些：限流按 IP 生效，
    被限流期间其他东方财富行情接口同样无法使用
    :param name: 接口名，如 stock_zh_a_hist_em
    :type name: str
    :return: 同 registered_alternatives；没有登记时为空列表
    :rtype: list
    """
    return [
        item
        for item in registered_alternatives(name)
        if item["rate_limit"] != EASTMONEY_PUSH2
    ]


def similar_names(name: str, limit: int = SIMILAR_LIMIT) -> List[str]:
    """
    接口名不存在时，找出名称最接近的接口，用于提示
    接口更名（如 get_futures_daily 改为 futures_daily）或凭记忆写错名称时很常见。
    按字符相似度比较，而不用 ak.search：后者对任何输入都会按片段给出结果，
    名称完全无关时也会列出几个接口，反而误导
    :param name: 不存在的接口名
    :type name: str
    :param limit: 最多返回几个
    :type limit: int
    :return: 接口名列表，没有足够相近的名称时为空
    :rtype: list
    """
    names = [item["name"] for item in _all_interfaces()]
    return difflib.get_close_matches(name, names, n=limit, cutoff=0.6)


def renamed_info(name: str) -> Optional[Dict[str, str]]:
    """
    旧接口名的去向，取自 AKShare 的改名对照（ak.renamed_info，AKShare 1.20.58 起提供）
    :param name: 接口名
    :type name: str
    :return: 含 status（renamed 或 removed）、version、url，更名时另有 new_name；
        不是已知的旧接口名，或 AKShare 版本过低时返回 None
    :rtype: dict
    """
    lookup = getattr(ak, "renamed_info", None)
    if lookup is None:
        return None
    try:
        return lookup(name)
    except Exception:
        return None


def not_found_message(name: str, channel: str = "http") -> str:
    """
    接口名不存在时的完整报错信息，按调用渠道给出下一步该怎么做
    已更名的接口给出现在的名称，已移除的给出移除的版本与更新日志地址，
    其余情况（多为拼写错误）给出名称相近的接口。改名的接口必须先查对照：
    按名称相似度猜出来的候选常把另一个数据源的接口排在前面，对已移除的接口则完全不相干
    :param name: 不存在的接口名
    :type name: str
    :param channel: http 表示 HTTP 接口，mcp 表示 MCP 工具
    :type channel: str
    :return: 报错信息
    :rtype: str
    """
    prefix = f"未找到接口 {name}。"
    info = renamed_info(name)
    if info and info.get("status") == "renamed":
        new_name = info["new_name"]
        moved = f"{name} 已在 AKShare {info['version']} 更名为 {new_name}，"
        if channel == "mcp":
            return (
                f'{prefix}{moved}请改用 name="{new_name}"；参数与返回的列可能有调整，'
                "调用前先用 describe_interface 查看"
            )
        return (
            f"{prefix}{moved}请改为请求 /api/public/{new_name}；参数与返回的列可能有调整，"
            f"说明见 /api/interfaces/{new_name}"
        )
    if info and info.get("status") == "removed":
        step = (
            "可用 search_interfaces 查找替代接口"
            if channel == "mcp"
            else "可通过 /api/interfaces?q=关键词 查找替代接口"
        )
        return (
            f"{prefix}{name} 已在 AKShare {info['version']} 移除，{step}；"
            f"移除的原因见更新日志 {info['url']}"
        )
    similar = similar_names(name)
    hint = f"名称相近的接口：{'、'.join(similar)}。" if similar else ""
    if channel == "mcp":
        return f"{prefix}{hint}请用 search_interfaces 搜索正确的接口名"
    return (
        f"{prefix}{hint}请通过 /api/interfaces 查找接口名，"
        f"或升级 AKShare 到最新版本：{DOC_URL}"
    )


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
