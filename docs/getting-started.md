# 快速入门

本教程带您从零开始完成一次完整的取数流程：安装 AKTools，启动服务，在浏览器里看到第一份数据，找到需要的接口，查看参数，获取贵州茅台的历史行情，最后下载为 Excel 文件。整个过程不需要编写代码，大约需要 10 分钟。

!!! tip "只想在 AI 助手中使用？"

    不需要完成下面的 10 个步骤，直接跳到[在 AI 助手中使用](#mcp)，约 3 分钟即可完成配置。

## 第 1 步：准备 Python 环境 {#python}

AKTools 需要 **Python 3.11 及以上版本（64 位）**。打开命令行，检查 Python 版本：

=== "Windows"

    按 ++win+r++，输入 `cmd` 后回车，打开命令提示符，然后输入：

    ```shell
    python --version
    ```

=== "macOS / Linux"

    打开“终端”，输入：

    ```shell
    python3 --version
    ```

    macOS 和 Linux 上的命令通常是 `python3`，下文的 `python` 请相应替换为 `python3`。

显示 `Python 3.11.x` 或更高的版本号即可。如果提示“不是内部或外部命令”或版本过低，请先到 [Python 官网](https://www.python.org/downloads/) 下载安装新版本。Windows 用户安装时请勾选 **Add python.exe to PATH**。

## 第 2 步：安装 AKTools {#install}

在命令行中输入：

```shell
pip install aktools
```

安装 AKTools 时会自动安装 AKShare。国内网络下载较慢时，可以使用镜像源：

```shell
pip install aktools -i https://mirrors.aliyun.com/pypi/simple/
```

## 第 3 步：启动服务 {#start}

```shell
python -m aktools
```

看到类似下面的输出，就表示服务已经启动：

```text
请访问：http://127.0.0.1:8080/version 来获取最新的库版本信息，确保使用最新版本的 AKShare 和 AKTools
当前的 AKTools 版本为：0.0.96，AKShare 版本为：1.20.0
点击打开 HTTP API 主页：http://127.0.0.1:8080/
点击打开接口导览：http://127.0.0.1:8080/docs
INFO:     Uvicorn running on http://127.0.0.1:8080 (Press CTRL+C to quit)
```

!!! warning "不要关闭这个命令行窗口"

    服务运行在这个窗口里，关闭窗口服务就停止了。下面的步骤都在浏览器中完成。

## 第 4 步：获取第一份数据 {#first-request}

在浏览器地址栏输入以下地址并回车：

```text
http://127.0.0.1:8080/api/public/tool_trade_date_hist_sina
```

这个地址调用的是 AKShare 的 `tool_trade_date_hist_sina` 接口，获取新浪财经的 A 股交易日历。浏览器中会显示类似下面的内容：

```json
[{"trade_date":"1990-12-19T00:00:00.000"},{"trade_date":"1990-12-20T00:00:00.000"},{"trade_date":"1990-12-21T00:00:00.000"}, ...]
```

能看到数据，说明 AKTools 已经可以正常工作。如果看到 `502` 错误，通常是网络或代理问题，请参考[常见问题](faq.md#faq-502)。

## 第 5 步：找到需要的接口 {#find}

AKShare 有一千多个数据接口，每个接口都有一个英文名称。不知道名称时，可以用中文关键词搜索。例如搜索“个股的历史行情”：

```text
http://127.0.0.1:8080/api/interfaces?q=个股的历史行情
```

返回 4 个接口，每个接口包含名称 `name` 和中文标题 `title`：

```json
[
  {"name": "stock_hk_daily", "title": "新浪财经-港股-个股的历史行情数据"},
  {"name": "stock_zh_a_cdr_daily", "title": "新浪财经-A股-CDR个股的历史行情数据，大量抓取容易封 IP"},
  {"name": "stock_zh_a_daily", "title": "新浪财经-A 股-个股的历史行情数据，大量抓取容易封 IP"},
  {"name": "stock_zh_b_daily", "title": "新浪财经-B 股-个股的历史行情数据，大量抓取容易封 IP"}
]
```

我们要找的是 A 股个股的历史行情，对应的接口是 `stock_zh_a_daily`。

!!! tip "搜索技巧"

    关键词会同时匹配接口名称和中文标题。中文标题通常写成“数据来源-市场-数据类型”，用“历史行情”“分红”“资金流”等词搜索最有效。结果太多时，换一个更具体的关键词，比如把“历史行情”换成“个股的历史行情”。

## 第 6 步：查看接口的参数 {#params}

在 `/api/interfaces/` 后面加上接口名，即可查看它有哪些参数：

```text
http://127.0.0.1:8080/api/interfaces/stock_zh_a_daily
```

返回内容中的 `params` 就是参数列表，整理如下：

| 参数 | 默认值 | 说明 |
| --- | --- | --- |
| `symbol` | `sh603843` | 股票代码，格式如 `sh600000`：沪市加 `sh`，深市加 `sz` |
| `start_date` | `19900101` | 开始日期，格式如 `20201103` |
| `end_date` | `21000118` | 结束日期，格式如 `20201103` |
| `adjust` | 空 | 复权方式：空为不复权，`qfq` 为前复权，`hfq` 为后复权 |

所有参数都有默认值，不传也能调用；需要特定股票和日期范围时，再把对应参数加到地址里。

## 第 7 步：带参数获取数据 {#with-params}

获取贵州茅台（沪市代码 600519）2024 年 10 月 8 日至 11 日的前复权日线数据：

```text
http://127.0.0.1:8080/api/public/stock_zh_a_daily?symbol=sh600519&start_date=20241008&end_date=20241011&adjust=qfq
```

这个地址由三部分组成：

| 部分 | 含义 |
| --- | --- |
| `/api/public/stock_zh_a_daily` | 调用 `stock_zh_a_daily` 接口 |
| `?` | 问号后面是参数 |
| `symbol=sh600519&start_date=...` | 每个参数写成“参数名=值”，多个参数之间用 `&` 连接，值不加引号 |

返回 4 个交易日的数据，每一天是一个对象：

```json
[
  {"date":"2024-10-08T00:00:00.000","open":1771.63,"high":1771.63,"low":1558.46,"close":1598.18,"volume":19470947.0, ...},
  {"date":"2024-10-09T00:00:00.000","open":1576.85,"high":1576.85,"low":1474.81,"close":1479.59,"volume":12019684.0, ...},
  {"date":"2024-10-10T00:00:00.000","open":1504.74,"high":1547.24,"low":1475.74,"close":1521.19,"volume":7460342.0, ...},
  {"date":"2024-10-11T00:00:00.000","open":1498.37,"high":1521.16,"low":1474.81,"close":1488.72,"volume":4191471.0, ...}
]
```

## 第 8 步：下载为 Excel 文件 {#download}

在上一步的地址末尾加上 `&_format=xlsx`：

```text
http://127.0.0.1:8080/api/public/stock_zh_a_daily?symbol=sh600519&start_date=20241008&end_date=20241011&adjust=qfq&_format=xlsx
```

浏览器会下载一个名为 `stock_zh_a_daily.xlsx` 的文件，用 Excel 或 WPS 打开即可。把 `xlsx` 换成 `csv` 则下载 CSV 文件，适合导入 Stata、MATLAB 等软件。

## 第 9 步：在程序中调用 {#code}

在浏览器里能打开的地址，在任何编程语言里都能请求。以 Python 为例：

```python
import pandas as pd
import requests

url = "http://127.0.0.1:8080/api/public/stock_zh_a_daily"
params = {
    "symbol": "sh600519",
    "start_date": "20241008",
    "end_date": "20241011",
    "adjust": "qfq",
}
r = requests.get(url, params=params, timeout=30)
r.raise_for_status()
df = pd.DataFrame(r.json())
print(df)
```

其他语言的写法请见[多语言调用](guide/examples.md)。

## 第 10 步：停止服务 {#stop}

回到运行服务的命令行窗口，按 ++ctrl+c++ 即可停止服务。下次使用时，重新运行 `python -m aktools`。

## 在 AI 助手中使用 {#mcp}

AKTools 也可以作为 MCP 服务，让 Claude、Cursor 等 AI 助手直接获取数据。这种方式**不需要安装 Python 和 AKTools，也不需要手动启动服务**，AI 助手会自己启动它。

### 第 1 步：安装 uv

[uv](https://docs.astral.sh/uv/) 会自动下载 Python 和 AKTools，并在独立环境中运行。按[官方安装说明](https://docs.astral.sh/uv/getting-started/installation/)安装后，在命令行中运行 `uvx --version`，能显示版本号即可。

### 第 2 步：添加到 AI 助手

=== "Claude Desktop"

    打开设置中的“开发者 → 编辑配置”，在 `claude_desktop_config.json` 中加入以下内容，保存后重启 Claude Desktop：

    ```json
    {
      "mcpServers": {
        "aktools": {
          "command": "uvx",
          "args": ["--from", "aktools", "aktools-mcp"]
        }
      }
    }
    ```

=== "Claude Code"

    在命令行中运行：

    ```shell
    claude mcp add aktools -- uvx --from aktools aktools-mcp
    ```

=== "Cursor"

    在项目的 `.cursor/mcp.json`（或全局的 `~/.cursor/mcp.json`）中加入以下内容：

    ```json
    {
      "mcpServers": {
        "aktools": {
          "command": "uvx",
          "args": ["--from", "aktools", "aktools-mcp"]
        }
      }
    }
    ```

第一次启动时需要下载 AKShare 等依赖（约 150 MB），可能需要几分钟；客户端提示超时的话，等下载完成后重启客户端即可。

### 第 3 步：提问

直接用自然语言提问，例如：

- “帮我查一下贵州茅台 2024 年 10 月 8 日到 11 日的前复权日线行情”
- “AKShare 里有哪些和可转债相关的接口？”
- “stock_zh_a_hist 这个接口有哪些参数，复权方式怎么填？”

助手会依次调用 `search_interfaces` 搜索接口、`describe_interface` 查看参数、`get_data` 获取数据。遇到问题请参考[常见问题](faq.md#faq-mcp-timeout)，更多说明见[AI 助手（MCP）](guide/mcp.md)。

## 下一步 {#next}

恭喜您完成了快速入门！接下来可以：

- 阅读[调用规则](guide/usage.md)，了解返回格式和错误状态码
- 阅读[接口目录](guide/catalog.md)，了解接口说明中各字段的含义
- 想在 Claude、Cursor 等 AI 助手中使用？请见[在 AI 助手中使用](#mcp)
- 想让同事或其他程序访问这个服务？请见[部署](deploy.md)
- 遇到问题？请先查看[常见问题](faq.md)
