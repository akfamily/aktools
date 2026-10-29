# 调用规则

本页说明 AKTools 的网址怎么写、参数怎么传、返回什么格式，以及出错时如何判断原因。还没有运行过 AKTools 的话，建议先完成[快速入门](../getting-started.md)。

## 服务地址 {#endpoints}

以下地址都以服务地址开头，默认为 `http://127.0.0.1:8080`：

| 地址 | 说明 |
| --- | --- |
| `/` | 主页，展示服务地址、版本信息和简要的使用说明 |
| `/docs` | 接口导览（Swagger UI），可在线调试接口 |
| `/version` | 当前与最新的 AKShare、AKTools 版本 |
| `/api/public/{接口名}` | 获取数据，详见下文 |
| `/api/interfaces` | 接口目录，可用 `?q=关键词` 搜索，详见[接口目录](catalog.md) |
| `/api/interfaces/{接口名}` | 接口的标题、数据源地址与各参数的默认值、类型和说明 |
| `/api/show-temp/{接口名}` | 用 [PyScript](https://pyscript.net/) 在浏览器中获取并展示该接口的数据，并提供 JSON 下载 |
| `/api/show` | 上述 PyScript 数据展示页的演示，展示 `tool_trade_date_hist_sina` 接口的数据 |

PyScript 数据展示页在浏览器中运行 Python：首次打开时，浏览器需要从 jsDelivr 的 fastly 节点下载 Pyodide 与 pandas（数十 MB），国内网络一般可以访问，加载通常需要十几到几十秒，之后会使用浏览器缓存。

## 获取数据 {#usage}

AKTools 把 HTTP 请求一一对应地翻译成 AKShare 接口调用：

```text
GET /api/public/{接口名}?{参数1}={值1}&{参数2}={值2}
        ↓
akshare.{接口名}(参数1="值1", 参数2="值2")
```

- **接口名**与 AKShare 的函数名完全一致，例如 `stock_zh_a_hist`。不知道接口名时，请用[接口目录](catalog.md)搜索。
- **参数**以查询字符串传递，写在 `?` 之后，每个参数写成“参数名=值”，多个参数之间用 `&` 连接。
- **参数值不加引号**，例如写 `symbol=600000`，不要写 `symbol="600000"`。
- 不传的参数使用 AKShare 接口的默认值。

### 无参数接口

例如 `ak.tool_trade_date_hist_sina()` 用于获取新浪财经的交易日历，直接访问即可：

```text
http://127.0.0.1:8080/api/public/tool_trade_date_hist_sina
```

### 带参数接口

例如 `ak.stock_zh_a_hist()` 用于获取 A 股历史行情。获取 `symbol="600000"` 的数据：

```text
http://127.0.0.1:8080/api/public/stock_zh_a_hist?symbol=600000
```

同时指定多个参数：

```text
http://127.0.0.1:8080/api/public/stock_zh_a_hist?symbol=600000&period=weekly&start_date=20240101&end_date=20241231&adjust=qfq
```

!!! note "参数值中含中文或特殊字符"

    在浏览器地址栏中可以直接输入中文，浏览器会自动编码。在程序中拼接网址时，请使用所用语言的参数编码功能，例如 Python `requests` 的 `params`、JavaScript 的 `URLSearchParams`，不要手动拼接含 `&`、`=`、空格的参数值。

## 返回格式 {#response}

成功时返回由 DataFrame 按行转换得到的 JSON 数组，每一行是一个对象，字段名与 AKShare 返回的列名一致；日期时间字段为 ISO 8601 格式：

```json
[
  {"trade_date": "1990-12-19T00:00:00.000"},
  {"trade_date": "1990-12-20T00:00:00.000"},
  {"trade_date": "1990-12-21T00:00:00.000"}
]
```

## 数据缓存 {#cache}

为了减少对上游网站的重复请求，AKTools 会缓存接口返回的数据：

- 同一接口、同样参数的请求，在 **60 秒**内直接返回上次的数据，不再访问上游网站。`_format` 不影响缓存，同样参数的 JSON、CSV、Excel 请求共用一份数据。
- 响应头 `X-AKTools-Cache` 标明数据来源：`hit` 表示来自缓存，`miss` 表示刚从上游获取。
- 出错的请求和空数据不会被缓存。

需要更实时的数据，或想延长缓存时间，请在启动时设置，详见[缓存设置](../deploy.md#cache)。

## 下载 CSV 与 Excel {#download}

加上保留参数 `_format`，可以把数据直接下载为表格文件，方便在 Excel、Stata、MATLAB 等软件中使用：

| `_format` | 返回内容 |
| --- | --- |
| `json` | 默认值，返回 JSON 数组 |
| `csv` | 下载 `{接口名}.csv`，UTF-8 编码并带 BOM，Excel 直接打开中文不会乱码 |
| `xlsx` | 下载 `{接口名}.xlsx` Excel 文件 |

例如：

```text
http://127.0.0.1:8080/api/public/stock_zh_a_hist?symbol=000001&start_date=20240101&end_date=20241231&_format=xlsx
```

`_format` 由 AKTools 处理，不会传给 AKShare 接口。Excel 单个工作表最多约 104 万行，数据超出时请改用 `csv`。

## 错误与状态码 {#status-codes}

失败时返回 `{"error": "错误信息"}`，可以根据状态码判断是用法问题还是网络问题：

| 状态码 | 含义 | 处理建议 |
| --- | --- | --- |
| `200` | 成功 | — |
| `400` | `_format` 取值不支持，或数据行数超过 Excel 上限 | 改用 `json`、`csv` 或 `xlsx`；数据过大时改用 `csv` |
| `404` | 接口名不存在、接口调用出错（如参数错误）或接口返回空数据 | 升级 AKShare，并对照[接口参数说明](catalog.md#detail)检查接口名和参数，详见[常见问题](../faq.md#faq-404) |
| `502` | 无法访问上游数据源 | 检查网络和代理设置，详见[常见问题](../faq.md#faq-502) |
