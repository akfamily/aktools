# AKTools

> AKTools exposes AKShare's financial data interfaces as an HTTP API, so you can fetch data from any programming language.

[AKTools](https://github.com/akfamily/aktools) 是一款用于快速搭建 [AKShare](https://github.com/akfamily/akshare) HTTP API 的工具。只需一行命令即可启动 HTTP 服务，让原本只服务于 Python 用户的开源财经数据接口库 AKShare 突破编程语言的限制：无论您使用的是 C/C++、Java、Go、Rust、Ruby、PHP、JavaScript、R、MATLAB、Stata 等编程语言或软件，都可以快速、轻松地获取财经数据，助力您更好地展开研究和开发工作。

!!! tip "第一次使用？"

    请从[快速入门](getting-started.md)开始。教程会带您从安装开始，一步步完成启动服务、查找接口、获取数据和下载 Excel，大约需要 10 分钟。

## 适合谁用

- 使用 R、MATLAB、Stata、Excel 等软件，想直接获取 AKShare 财经数据的研究人员
- 使用 Java、Go、JavaScript 等语言开发应用，需要一个财经数据服务的开发者
- 希望把数据获取集中在一台服务器上，供团队成员共同使用的团队

## 什么情况下不必用 AKTools {#when-not}

AKTools 是 AKShare 外面的一层 HTTP 转发，并不改变 AKShare 本身的特点。以下情况可以考虑其他方式：

- **个人在 R、Stata 中使用**：R 的 [reticulate](https://rstudio.github.io/reticulate/)、Stata 16 及以上的 `python` 代码块都能直接调用 AKShare，不需要额外运行一个服务。AKTools 同样需要安装 Python，它省去的是编写 Python 代码，而不是安装 Python。
- **生产或商业用途**：AKShare 的数据来自公开网页，网站改版时接口可能失效，数据仅供学术研究使用。对稳定性和授权有要求时，请使用有授权的商业数据源。
- **需要长期、可复现的历史数据**：每次请求都会实时访问上游网站。做研究时，更稳妥的做法是定期把数据保存到本地文件或数据库，研究时读取本地数据。
- **部署到公网供不特定的人使用**：AKTools 不带鉴权，所有请求都从服务器的同一个 IP 访问上游网站，请求量大时容易被封 IP，转发数据也可能违反数据源的使用条款。

## 特性

- **零配置**：`python -m aktools` 一行命令启动服务，无需编写任何代码
- **接口全覆盖**：AKShare 的每个数据接口都可以通过 `/api/public/<接口名>` 直接访问，AKShare 新增接口后升级即可使用
- **跨语言**：返回标准 JSON，任何能发送 HTTP 请求的语言或软件都可以调用
- **接口自查**：通过 `/api/interfaces` 按关键词搜索接口，直接查看每个参数的默认值和说明，详见[接口目录](guide/catalog.md)
- **表格下载**：加上 `_format=csv` 或 `_format=xlsx`，即可把数据下载为 CSV 或 Excel 文件，详见[下载 CSV 与 Excel](guide/usage.md#download)
- **结果缓存**：同一接口、同样参数在 60 秒内直接返回上次的数据，减少对上游网站的重复请求，详见[数据缓存](guide/usage.md#cache)
- **AI 助手**：内置 MCP 服务，在 Claude、Cursor 等 AI 助手中用自然语言获取数据，详见[AI 助手（MCP）](guide/mcp.md)
- **自带文档**：基于 FastAPI，启动后访问 `/docs` 即可在线查看和调试接口
- **便于部署**：提供 Dockerfile，支持 Gunicorn + Uvicorn 多进程部署，详见[部署](deploy.md)

## 工作原理

AKTools 把每个 HTTP 请求翻译成一次同名的 AKShare 接口调用，再把返回的表格数据转成 JSON：

```text
浏览器或程序发出请求：GET /api/public/stock_zh_a_daily?symbol=sh600519
        ↓
AKTools 调用同名接口：akshare.stock_zh_a_daily(symbol="sh600519")
        ↓
AKShare 从新浪财经等网站获取数据，AKTools 以 JSON、CSV 或 Excel 格式返回
```

因此**接口有哪些、参数怎么填、数据是什么含义，都以 AKShare 为准**。您可以通过 AKTools 的[接口目录](guide/catalog.md)查询，也可以查阅 [AKShare 数据字典](https://akshare.akfamily.xyz/data/index.html)。

## 3 步快速体验

已经安装了 Python 3.11 及以上版本？只需 3 步：

<div class="termy">

```console
$ pip install aktools
---> 100%
Successfully installed aktools
```

</div>

1. 在命令行运行 `python -m aktools` 启动服务
2. 浏览器打开 `http://127.0.0.1:8080/api/public/tool_trade_date_hist_sina`，看到交易日历数据即表示成功
3. 浏览器打开 `http://127.0.0.1:8080/api/interfaces?q=历史行情`，搜索您需要的接口

## 文档导航

| 页面 | 内容 |
| --- | --- |
| [快速入门](getting-started.md) | 从安装到下载 Excel 的完整教程，新手请从这里开始 |
| [调用规则](guide/usage.md) | 网址怎么写、参数怎么传、返回什么格式、出错了怎么看 |
| [接口目录](guide/catalog.md) | 搜索接口、查看参数说明 |
| [多语言调用](guide/examples.md) | curl、Python、JavaScript、R、MATLAB、Rust 示例代码 |
| [AI 助手（MCP）](guide/mcp.md) | 在 Claude、Cursor 等 AI 助手中用自然语言获取数据 |
| [部署](deploy.md) | 启动参数、局域网访问、生产环境与 Docker 部署 |
| [常见问题](faq.md) | 502、404、无法访问、版本升级等问题的排查方法 |
| [版本说明](aktools_version.md) | 每个版本的更新内容 |

## 相关链接

- [AKTools GitHub 仓库](https://github.com/akfamily/aktools)：提交 Issue 或 Pull Request 前请阅读[贡献指南](https://github.com/akfamily/aktools/blob/main/CONTRIBUTING.md)
- [AKShare 文档](https://akshare.akfamily.xyz/)
- [FastAPI 文档](https://fastapi.tiangolo.com/)
