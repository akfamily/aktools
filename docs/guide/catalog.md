# 接口目录

不知道接口名或参数怎么填时，可以直接向 AKTools 查询，不需要去翻 AKShare 文档。这些信息来自 AKShare 接口的函数签名和说明，查询时不会访问上游数据源，因此不联网也能使用。

## 搜索接口 {#search}

按关键词搜索，关键词同时匹配接口名和中文标题，不区分大小写：

```text
http://127.0.0.1:8080/api/interfaces?q=交易日历
```

```json
[
  {"name": "futures_rule", "title": "国泰君安期货-交易日历数据表"},
  {"name": "tool_trade_date_hist_sina", "title": "新浪财经-交易日历-历史数据"}
]
```

不带 `q` 时返回全部接口。

!!! tip "搜索技巧"

    中文标题通常写成“数据来源-市场-数据类型”，例如“新浪财经-A 股-个股的历史行情数据”。用“历史行情”“分红”“资金流”等数据类型搜索最有效；结果太多时，换一个更具体的关键词，或加上市场名称，如“个股的历史行情”“港股”。也可以用接口名的一部分搜索，例如 `stock_zh_a`。

## 查看参数说明 {#detail}

在 `/api/interfaces/` 后面加上接口名：

```text
http://127.0.0.1:8080/api/interfaces/stock_zh_a_hist
```

```json
{
  "name": "stock_zh_a_hist",
  "title": "东方财富网-行情首页-沪深京 A 股-每日行情",
  "source": "东方财富·行情（频繁访问易限流）",
  "source_url": "https://quote.eastmoney.com/concept/sh603777.html?from=classic",
  "rate_limit": "eastmoney_push2",
  "alternatives": [
    {"name": "stock_zh_a_daily", "title": "新浪财经-A 股-个股的历史行情数据，大量抓取容易封 IP", "source": "新浪财经"},
    {"name": "stock_zh_a_hist_tx", "title": "腾讯证券-日频-股票历史数据", "source": "腾讯"}
  ],
  "url": "/api/public/stock_zh_a_hist",
  "params": [
    {"name": "symbol", "default": "000001", "required": false, "type": "str", "description": "股票代码"},
    {"name": "period", "default": "daily", "required": false, "type": "str", "description": "choice of {'daily', 'weekly', 'monthly'}"}
  ],
  "doc": "AKShare 接口的完整说明文字……"
}
```

示例中的 `params` 只列出了前两个参数。各字段的含义：

| 字段 | 含义 |
| --- | --- |
| `name` | 接口名，即 `/api/public/` 后面要写的名称 |
| `title` | 中文标题，说明数据来源和内容 |
| `source` | 数据来源的中文名称，如“新浪财经”“同花顺”“东方财富”；东方财富行情服务器的接口标为“东方财富·行情（频繁访问易限流）”，见[东方财富行情接口的限流](#rate-limit) |
| `source_url` | 数据来源网页，可以打开对照数据含义 |
| `rate_limit` | 访问限制，取自 AKShare 的接口注册表：`eastmoney_push2` 表示频繁访问会被东方财富临时限流，其他接口为 `null` |
| `alternatives` | 来自其他数据源的同类接口，每项包含 `name`、`title`、`source`，取自 AKShare 人工维护的对照表（AKShare 1.20.39 起），没有登记时为空；它们的参数与返回列可能不同 |
| `url` | 获取数据的地址 |
| `params` | 参数列表，见下表 |
| `outputs` | 返回的列，每列包含 `name`、`type`、`desc`，取自 AKShare 的接口注册表，未登记时为空 |
| `limit_desc` | 单次调用返回的数据范围说明 |
| `example` | Python 调用示例 |
| `doc` | 接口的完整说明，参数说明不全时可以参考它 |

`params` 中每个参数的字段：

| 字段 | 含义 |
| --- | --- |
| `name` | 参数名 |
| `default` | 默认值，不传该参数时使用 |
| `required` | 为 `true` 时必须传入 |
| `type` | AKShare 声明的参数类型，如 `str`、`float`。通过网址传入的参数值都是文本，AKTools 会原样传给 AKShare |
| `description` | 参数说明，`choice of {...}` 表示可选值 |

接口名不存在时返回 `404`，并在错误信息中列出名称相近的接口。

!!! note "说明来自 AKShare"

    参数说明直接取自 AKShare 源码中的注释，个别接口的说明可能不完整。需要了解数据字段的含义时，请查阅 [AKShare 数据字典](https://akshare.akfamily.xyz/data/index.html)。

## 东方财富行情接口的限流 {#rate-limit}

东方财富的行情类接口（实时行情、历史 K 线、板块、资金流等，约 100 个）使用的服务器在短时间内请求较多时，会临时封禁来源 IP，首次一般约 5 分钟后恢复，期间所有东方财富行情接口都会返回 `429`。这类接口的 `source` 为“东方财富·行情（频繁访问易限流）”，`rate_limit` 为 `eastmoney_push2`。东方财富的宏观、财务报表、龙虎榜等接口使用其他服务器，不受影响。

需要批量获取行情数据时，可以先搜索同一类数据的其他来源，例如 A 股日线除了东方财富的 `stock_zh_a_hist`，还有新浪财经的 `stock_zh_a_daily` 和腾讯的 `stock_zh_a_hist_tx`。接口说明中的 `alternatives` 列出了 AKShare 登记的同类接口；被限流时，返回的错误信息也会列出其中可以改用的接口。它们的参数可能不同，调用前请先查看参数说明。
