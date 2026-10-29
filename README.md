# AKTools

<!-- mcp-name: io.github.akfamily/aktools -->

> AKTools exposes [AKShare](https://github.com/akfamily/akshare)'s financial data as an HTTP API and an MCP server, so you can fetch it from any programming language or AI assistant.

[![PyPI](https://img.shields.io/pypi/v/aktools.svg)](https://pypi.org/project/aktools/)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/aktools.svg)](https://pypi.org/project/aktools/)
[![PyPI Downloads](https://static.pepy.tech/personalized-badge/aktools?period=total&units=INTERNATIONAL_SYSTEM&left_color=BLACK&right_color=GREEN&left_text=downloads)](https://pepy.tech/projects/aktools)
[![Documentation Status](https://img.shields.io/readthedocs/aktools/latest)](https://aktools.akfamily.xyz/)
[![Actions Status](https://github.com/akfamily/aktools/actions/workflows/build.yml/badge.svg)](https://github.com/akfamily/aktools/actions/workflows/build.yml)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![Data Science - AKShare](https://img.shields.io/badge/Data%20Science-AKShare-green)](https://github.com/akfamily/akshare)
[![MIT Licence](https://img.shields.io/badge/license-MIT-blue)](https://github.com/akfamily/aktools/blob/main/LICENSE)
[![GitHub stars](https://img.shields.io/github/stars/akfamily/aktools)](https://github.com/akfamily/aktools/stargazers)
[![GitHub forks](https://img.shields.io/github/forks/akfamily/aktools)](https://github.com/akfamily/aktools/network/members)
[![GitHub issues](https://img.shields.io/github/issues/akfamily/aktools)](https://github.com/akfamily/aktools/issues)

[AKTools](https://github.com/akfamily/aktools) 把开源财经数据接口库 [AKShare](https://github.com/akfamily/akshare) 的一千多个接口变成两种开箱即用的服务：

- **HTTP API**：一行命令启动服务，C/C++、Java、Go、Rust、JavaScript、R、MATLAB、Stata、Excel 等任何编程语言或软件都能通过网址获取数据。
- **MCP 服务**：在 Claude、Cursor 等 AI 助手中直接用自然语言提问，助手会自己查找接口、填写参数并取回数据。

两种方式背后是同一套接口目录、缓存和错误处理，按需选用即可。

**[AKTools 中文文档](https://aktools.akfamily.xyz/)** | **[AKShare 数据字典](https://akshare.akfamily.xyz/data/index.html)** | **[版本说明](https://aktools.akfamily.xyz/aktools_version/)**

> **第一次使用？** HTTP API 请从 [快速入门教程](https://aktools.akfamily.xyz/getting-started/) 开始，约 10 分钟即可完成从安装到下载 Excel 的完整流程；AI 助手请直接看下面的 [在 AI 助手中使用](#在-ai-助手中使用)。

## 目录

- [两种使用方式](#两种使用方式)
- [特性](#特性)
- [安装](#安装)
- [快速开始](#快速开始)
- [调用规则](#调用规则)
- [多语言调用示例](#多语言调用示例)
- [部署](#部署)
- [常见问题](#常见问题)
- [参与贡献](#参与贡献)
- [免责声明](#免责声明)
- [许可证](#许可证)

## 两种使用方式

### 通过 HTTP API 获取数据

```shell
pip install aktools
python -m aktools
```

然后在浏览器打开 `http://127.0.0.1:8080/api/public/tool_trade_date_hist_sina`，看到交易日历数据即表示成功。更多用法见下文的[快速开始](#快速开始)与[调用规则](#调用规则)。

### 在 AI 助手中使用

先[安装 uv](https://docs.astral.sh/uv/getting-started/installation/)，再把下面的配置加入 AI 助手的 MCP 配置文件，**不需要事先安装 AKTools，也不需要手动启动服务**：

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

重启助手后，就可以直接提问，例如：

- “帮我查一下贵州茅台 2024 年 10 月 8 日到 11 日的前复权日线行情”
- “AKShare 里有哪些和可转债相关的接口？”
- “stock_zh_a_hist 这个接口有哪些参数，复权方式怎么填？”

助手会通过 AKTools 提供的 3 个工具完成查询：`search_interfaces` 搜索接口、`describe_interface` 查看参数、`get_data` 获取数据。下面是在 Claude Code 中实际提问的过程（根据真实会话记录回放）：

![在 Claude Code 中提问，AI 助手通过 AKTools 的 MCP 工具查询贵州茅台的日线行情](https://aktools.akfamily.xyz/img/mcp-demo.gif)

<details>
<summary>Claude Desktop</summary>

打开设置中的“开发者 → 编辑配置”，把上面的配置加入 `claude_desktop_config.json`，保存后重启 Claude Desktop。

</details>

<details>
<summary>Claude Code</summary>

```shell
claude mcp add aktools -- uvx --from aktools aktools-mcp
```

</details>

<details>
<summary>Cursor</summary>

点击按钮一键添加：

[![Add AKTools MCP server to Cursor](https://cursor.com/deeplink/mcp-install-dark.svg)](https://cursor.com/install-mcp?name=aktools&config=eyJjb21tYW5kIjoidXZ4IiwiYXJncyI6WyItLWZyb20iLCJha3Rvb2xzIiwiYWt0b29scy1tY3AiXX0%3D)

也可以手动把上面的配置加入项目的 `.cursor/mcp.json`，或全局的 `~/.cursor/mcp.json`。

</details>

<details>
<summary>连接已经运行的 AKTools 服务（HTTP 方式）</summary>

已经用 `python -m aktools` 启动了服务，或者想让多台电脑共用一个服务时，可以让助手直接连接 `http://127.0.0.1:8080/mcp`，例如：

```shell
claude mcp add --transport http aktools http://127.0.0.1:8080/mcp
```

</details>

第一次启动时 `uvx` 需要下载 AKShare 等依赖（约 150 MB），可能需要几分钟。配置、局域网访问与排障详见 [AI 助手（MCP）文档](https://aktools.akfamily.xyz/guide/mcp/)。

## 特性

- **两种方式**：同一份数据既可以通过 HTTP API 获取，也可以在 Claude、Cursor 等 AI 助手中用自然语言获取
- **零配置**：`python -m aktools` 一行命令启动服务，无需编写任何代码
- **接口全覆盖**：AKShare 的每个数据接口都可以通过 `/api/public/<接口名>` 直接访问，AKShare 新增接口后升级即可使用
- **跨语言**：返回标准 JSON，任何能发送 HTTP 请求的语言或软件都可以调用
- **接口自查**：`/api/interfaces` 列出全部接口并支持按关键词搜索，每个接口的参数、默认值和说明都能直接查询
- **表格下载**：加上 `_format=csv` 或 `_format=xlsx` 即可把数据下载为 CSV 或 Excel 文件
- **结果缓存**：同一接口、同样参数在 60 秒内直接返回上次的数据，减少对上游网站的重复请求，降低被封 IP 的风险
- **自带文档**：基于 [FastAPI](https://fastapi.tiangolo.com/)，启动后访问 `/docs` 即可在线查看和调试接口
- **便于部署**：提供 Dockerfile，支持 Gunicorn + Uvicorn 多进程部署

## 安装

AKTools 要求 **Python 3.11 及以上（64 位）**，运行环境要求与 [AKShare 安装指导](https://akshare.akfamily.xyz/installation.html) 一致。

```shell
pip install aktools
```

AKShare 的数据接口会随上游网站的变化频繁更新，遇到问题时请先把两者都升级到最新版：

```shell
pip install akshare aktools --upgrade -i https://pypi.org/simple
```

## 快速开始

1. 启动服务：

    ```shell
    python -m aktools
    ```

2. 浏览器打开以下地址：

    | 地址 | 说明 |
    | --- | --- |
    | `http://127.0.0.1:8080/` | 主页，展示简要的使用说明 |
    | `http://127.0.0.1:8080/docs` | 接口导览，可在线调试 |
    | `http://127.0.0.1:8080/version` | 当前与最新的 AKShare、AKTools 版本 |
    | `http://127.0.0.1:8080/api/interfaces?q=历史行情` | 按关键词搜索接口 |
    | `http://127.0.0.1:8080/api/interfaces/stock_zh_a_hist` | 查看接口的参数、默认值和说明 |
    | `http://127.0.0.1:8080/api/public/tool_trade_date_hist_sina` | 连通性测试（新浪交易日历，无需参数且较为稳定） |
    | `http://127.0.0.1:8080/api/public/stock_zh_a_hist?symbol=600000` | 带参数获取数据 |

启动参数：

| 参数 | 简写 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `--host` | `-H` | `127.0.0.1` | 监听地址，需要局域网或其他机器访问时设置为 `0.0.0.0` |
| `--port` | `-P` | `8080` | 监听端口 |
| `--auto` | `-A` | 关闭 | 启动后自动打开浏览器 |
| `--cache-ttl` | — | `60` | 结果缓存的有效期（秒），同一接口、同样参数在有效期内直接返回上次的数据，`0` 为关闭 |
| `--akshare-cache-clear` | — | `3600` | 清空 AKShare 内部缓存的间隔（秒），避免板块名称等数据一直不更新，`0` 为关闭 |
| `--version` | `-v` | — | 查看 AKTools 版本 |

例如：`python -m aktools --port 8888 --auto` 会在 8888 端口启动并自动打开浏览器。需要让局域网内的其他机器访问时，加上 `--host 0.0.0.0`，其他机器通过 `http://<本机 IP>:8888` 访问；`0.0.0.0` 只表示监听所有网卡，不能当作访问地址在浏览器中打开。

## 调用规则

AKTools 本身不加工数据，只负责把 HTTP 请求翻译成对 AKShare 接口的调用：

```text
GET /api/public/{接口名}?{参数1}={值1}&{参数2}={值2}
        ↓
akshare.{接口名}(参数1="值1", 参数2="值2")
```

- **接口名**与 AKShare 的函数名完全一致。可以通过 `/api/interfaces?q=关键词` 搜索接口，通过 `/api/interfaces/{接口名}` 查看参数说明，详细的数据说明请查阅 [AKShare 数据字典](https://akshare.akfamily.xyz/data/index.html)。
- **参数**以查询字符串传递，值不需要加引号，例如 `?symbol=600000&period=weekly`；不传的参数使用 AKShare 接口的默认值。
- **返回值**默认是由 DataFrame 按行转换得到的 JSON 数组，日期时间字段为 ISO 8601 格式，例如 `"2024-01-25T00:00:00.000"`。
- **下载表格**：加上保留参数 `_format=csv` 或 `_format=xlsx`，数据会以 `{接口名}.csv` 或 `{接口名}.xlsx` 文件下载，例如 `/api/public/stock_zh_a_hist?symbol=000001&_format=xlsx`。CSV 为带 BOM 的 UTF-8 编码，可以直接用 Excel 打开。

请求失败时返回 `{"error": "错误信息"}`，状态码含义如下：

| 状态码 | 含义 | 处理建议 |
| --- | --- | --- |
| `200` | 成功 | — |
| `400` | 参数不合法，`_format` 取值不支持，或数据行数超过 Excel 上限 | 对照 `/api/interfaces/{接口名}` 检查参数；`_format` 改用 `json`、`csv` 或 `xlsx`，数据过大时改用 `csv` |
| `404` | 接口名不存在，或接口调用出错 | 升级 AKShare，并对照 `/api/interfaces/{接口名}` 检查接口名和参数 |
| `429` | 上游数据源限制了访问频率 | 稍后重试，或调大 `--cache-ttl` 减少重复请求 |
| `502` | 无法访问上游数据源、上游返回错误，或上游页面改版导致解析失败 | 检查网络和代理设置，见 [常见问题](#常见问题)；解析失败时升级 AKShare |

## 多语言调用示例

以下示例均假设服务运行在 `http://127.0.0.1:8080`，请按实际地址和端口修改。

<details open>
<summary>curl</summary>

```shell
curl "http://127.0.0.1:8080/api/public/stock_zh_a_hist?symbol=000001&period=daily&start_date=20240101&end_date=20240131&adjust=qfq"
```

</details>

<details>
<summary>Python</summary>

```python
import pandas as pd
import requests

url = "http://127.0.0.1:8080/api/public/stock_zh_a_hist"
params = {
    "symbol": "000001",
    "period": "daily",
    "start_date": "20240101",
    "end_date": "20240131",
    "adjust": "qfq",
}
r = requests.get(url, params=params, timeout=30)
r.raise_for_status()
df = pd.DataFrame(r.json())
print(df)
```

</details>

<details>
<summary>R</summary>

```r
library(RCurl)    # 需要先安装该包
library(jsonlite) # 需要先安装该包
options(warn = -1) # 去掉无参数请求时的 warning 信息

temp_df <- getForm(
  uri = "http://127.0.0.1:8080/api/public/stock_zh_a_hist",
  symbol = "000001",
  period = "daily",
  start_date = "20211109",
  end_date = "20211209",
  adjust = "hfq",
  .encoding = "utf-8"
)
inner_df <- fromJSON(temp_df)
inner_df
```

</details>

<details>
<summary>MATLAB</summary>

```matlab
api = 'http://127.0.0.1:8080/api/public/';
url = [api 'stock_zh_a_hist'];
options = weboptions('ContentType', 'json', 'CharacterEncoding', 'utf-8');
data = webread(url, 'symbol', '000001', 'period', 'daily', ...
    'start_date', '20211109', 'end_date', '20211209', 'adjust', 'hfq', options);
data % MATLAB 无法显示中文字段名，可自行改为英文字段
```

</details>

<details>
<summary>Rust</summary>

依赖：`reqwest`（启用 `blocking` 与 `json` 特性）和 `serde_json`。

```rust
use reqwest::blocking;
use serde_json::Value;

const URL: &str = "http://127.0.0.1:8080/api/public";

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let params = [
        ("symbol", "000001"),
        ("period", "daily"),
        ("start_date", "20240125"),
        ("end_date", "20240126"),
        ("adjust", ""),
    ];
    let resp = blocking::Client::new()
        .get(format!("{URL}/stock_zh_a_hist"))
        .query(&params)
        .send()?;

    if resp.status().is_success() {
        let data: Value = resp.json()?;
        println!("{data:#?}");
    } else {
        eprintln!("请求失败，状态码为：{}", resp.status());
    }
    Ok(())
}
```

</details>

更多示例及运行结果，请见 [多语言调用](https://aktools.akfamily.xyz/guide/examples/)。

## 部署

### Docker

使用仓库中的 [Dockerfile](https://github.com/akfamily/aktools/blob/main/Dockerfile) 构建镜像，镜像默认以 Gunicorn 管理多个 Uvicorn worker 运行：

```shell
docker build -t aktools .
docker run -d -p 8080:8080 aktools
```

国内网络环境下可以指定 PyPI 镜像源加速构建：

```shell
docker build --build-arg PIP_INDEX_URL=https://mirrors.aliyun.com/pypi/simple/ -t aktools .
```

镜像升级等更多说明，请见 [部署文档](https://aktools.akfamily.xyz/deploy/#docker)。

### 生产环境

`python -m aktools` 适合本地使用。生产环境建议直接用 Gunicorn 启动 `aktools.main:app`：

```shell
pip install gunicorn uvicorn-worker
AKTOOLS_HOST=0.0.0.0 gunicorn aktools.main:app --bind 0.0.0.0:8080 --workers 4 --worker-class uvicorn_worker.UvicornWorker
```

> AKTools 不带鉴权功能。如果服务需要暴露到公网，请在前面加一层带鉴权的反向代理（如 Nginx）。

## 常见问题

**返回 502，提示“访问上游数据源失败”**

运行 AKTools 的机器无法访问东方财富、新浪财经等上游网站，通常是代理配置导致的。报错中如果出现 `ProxyError` 或 `Unable to connect to proxy`，请检查或清除代理相关的环境变量后重启服务：

```shell
# Linux / macOS
unset HTTP_PROXY HTTPS_PROXY ALL_PROXY
# Windows PowerShell
Remove-Item Env:HTTP_PROXY, Env:HTTPS_PROXY, Env:ALL_PROXY
```

部分接口要求在境内网络环境下访问，详见 AKShare 文档中对应接口的说明。

**返回 404，提示“未找到该接口”或“调用接口出错”**

先升级 AKShare 到最新版，然后用 `/api/interfaces?q=关键词` 搜索正确的接口名，用 `/api/interfaces/{接口名}` 检查参数名和可选值。也可以在 Python 中直接调用同名的 AKShare 接口，确认问题是否出在 AKShare。

**数据没有及时更新**

同一接口、同样参数的请求在 60 秒内会返回缓存的数据，响应头 `X-AKTools-Cache: hit` 表示数据来自缓存，启动时加上 `--cache-ttl 0` 可关闭缓存。板块名称等数据由 AKShare 内部缓存，默认每小时清空一次，可用 `--akshare-cache-clear` 调整。

**数据有误或接口报错，应该去哪里反馈？**

AKTools 只负责转发请求，数据内容由 AKShare 提供。如果在 Python 中直接调用 AKShare 也有同样的问题，请到 [AKShare Issues](https://github.com/akfamily/akshare/issues) 反馈；只有 AKTools 自身的问题（启动、路由、序列化等）才需要到 [AKTools Issues](https://github.com/akfamily/aktools/issues) 反馈。

## 参与贡献

欢迎提交 Issue 和 Pull Request！开发环境的搭建、代码检查与提交规范请见 [贡献指南](https://github.com/akfamily/aktools/blob/main/CONTRIBUTING.md)。参与本项目即表示您同意遵守 [贡献者行为准则](https://github.com/akfamily/aktools/blob/main/CODE_OF_CONDUCT.md)。

## 免责声明

AKTools 与 AKShare 提供的数据仅供学术研究使用，不构成任何投资建议。数据均来自公开的网络数据源，请在使用前自行核实，并遵守相关数据源的使用条款。因使用本项目造成的任何直接或间接损失，项目作者及贡献者不承担任何责任。

## 许可证

本项目基于 [MIT 许可证](https://github.com/akfamily/aktools/blob/main/LICENSE) 开源。
