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
  "source_url": "https://quote.eastmoney.com/concept/sh603777.html?from=classic",
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
| `source_url` | 数据来源网页，可以打开对照数据含义 |
| `url` | 获取数据的地址 |
| `params` | 参数列表，见下表 |
| `doc` | 接口的完整说明，参数说明不全时可以参考它 |

`params` 中每个参数的字段：

| 字段 | 含义 |
| --- | --- |
| `name` | 参数名 |
| `default` | 默认值，不传该参数时使用 |
| `required` | 为 `true` 时必须传入 |
| `type` | AKShare 声明的参数类型，如 `str`、`float`。通过网址传入的参数值都是文本，AKTools 会原样传给 AKShare |
| `description` | 参数说明，`choice of {...}` 表示可选值 |

接口名不存在时返回 `404`。

!!! note "说明来自 AKShare"

    参数说明直接取自 AKShare 源码中的注释，个别接口的说明可能不完整。需要了解数据字段的含义时，请查阅 [AKShare 数据字典](https://akshare.akfamily.xyz/data/index.html)。
