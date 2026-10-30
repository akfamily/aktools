# 常见问题

遇到问题时，先看返回的状态码：`404` 多为接口名或参数问题，`502` 多为网络问题，状态码的完整说明见[调用规则](guide/usage.md#status-codes)。

## 接口返回 502 且提示“访问上游数据源失败” {#faq-502}

AKTools 本身只是把请求转发给 AKShare，数据由东方财富、新浪财经等上游网站提供。当返回如下错误时：

```text
{"error": "访问上游数据源失败，请检查网络或代理设置（HTTP_PROXY/HTTPS_PROXY 环境变量，或启动参数 --proxy）：..."}
```

通常是运行 AKTools 的机器**无法访问上游数据源**，而不是 AKTools 或接口本身的问题。常见原因与排查方法：

1. 本机配置了 HTTP 代理，但代理不可用。报错中若出现 `ProxyError`、`Unable to connect to proxy` 即属此类。请检查并按需清除代理环境变量，然后重启服务：

    ```shell
    # Linux / macOS
    unset HTTP_PROXY HTTPS_PROXY ALL_PROXY
    # Windows PowerShell
    Remove-Item Env:HTTP_PROXY, Env:HTTPS_PROXY, Env:ALL_PROXY
    ```

    若必须经代理访问外网，请确认代理本身可用，或用 `--proxy` 只为 AKTools 指定代理，详见[代理与超时](deploy.md#network)。

2. 网络不通、上游网站临时不可达或响应过慢：可先用 `tool_trade_date_hist_sina` 这类轻量接口测试连通性，或稍后重试。数据量大的接口超时时，可以用 `--timeout` 调大读取超时。

3. 部分接口对网络环境（如需境内网络）有要求，请参考 [AKShare 文档](https://akshare.akfamily.xyz/) 中对应接口的说明。

4. 报错中出现“上游数据源返回错误”或“解析上游数据失败”：前者多为上游网站临时故障，稍后重试即可；后者多为上游页面改版，请升级 AKShare。

## 接口返回 429 {#faq-429}

上游网站限制了访问频率，通常是短时间内请求过多。请稍后重试；多人或多个程序共用服务时，可以调大 `--cache-ttl`，让同样的请求直接使用缓存，详见[缓存设置](deploy.md#cache)。

## 接口返回 404 {#faq-404}

按错误信息分别处理：

- **未找到该接口**：接口名拼写错误，或当前安装的 AKShare 版本还没有这个接口。请升级 AKShare，并用[接口目录](guide/catalog.md#search)搜索正确的接口名。
- **调用接口出错**：通常是参数名或参数值不正确。请用[接口参数说明](guide/catalog.md#detail)检查参数名和可选值，也可以在 Python 中直接调用同名接口，确认问题是否出在 AKShare。
- **该接口返回数据为空**：参数组合没有对应的数据，例如日期范围内没有交易日。

## 接口返回 400，提示“不支持参数” {#faq-400}

网址中带了该接口没有的参数，通常是参数名拼写错误。错误信息会列出该接口的全部可用参数，也可以访问 `/api/interfaces/{接口名}` 查看说明。

AKShare 1.20.13 起，各接口不再提供 `timeout` 参数。旧网址中的 `timeout=…` 请删掉，超时改在启动 AKTools 时用 `--timeout` 设置，详见[代理与超时](deploy.md#network)。

## 数据没有及时更新 {#faq-stale}

AKTools 有两种缓存，可能让数据看起来没有更新：

1. **结果缓存**：同一接口、同样参数的请求在 60 秒内会返回缓存的数据。响应头 `X-AKTools-Cache: hit` 表示数据来自缓存。需要实时数据时，启动时加上 `--cache-ttl 0` 关闭结果缓存。
2. **AKShare 内部缓存**：板块名称、代码对照表等数据会被 AKShare 缓存，AKTools 默认每小时清空一次。需要更快更新时，调小 `--akshare-cache-clear`，例如设为 `600`（10 分钟）。

两者的详细说明见[缓存设置](deploy.md#cache)。

## 其他机器无法访问服务 {#faq-remote}

1. 启动时需要指定 `--host 0.0.0.0`，默认的 `127.0.0.1` 只允许本机访问，详见[让其他机器访问](deploy.md#lan)。
2. 检查防火墙或云服务器的安全组是否放行了对应端口。
3. 使用 Docker 时，确认 `docker run` 带上了 `-p 8080:8080` 端口映射。

## 如何查看和升级版本 {#faq-version}

服务启动后访问 `http://127.0.0.1:8080/version`，可以同时看到当前安装的和 PyPI 上最新的 AKShare、AKTools 版本：

```json
{"ak_current_version":"1.20.0","ak_latest_version":"1.20.2","at_current_version":"0.0.96","at_latest_version":"0.0.96"}
```

也可以在命令行中运行 `python -m aktools --version` 查看 AKTools 版本。

AKShare 的数据接口会随上游网站的变化频繁更新，遇到问题时请先把两者都升级到最新版，然后重启服务：

```shell
pip install akshare aktools --upgrade -i https://pypi.org/simple
```

## 刚发布的新版本安装不到 {#faq-mirror}

清华、阿里云等国内 PyPI 镜像同步 PyPI 上的新版本通常需要几个小时。在此期间，用镜像源执行 `pip install aktools --upgrade` 或 `uvx --from aktools` 仍会装到旧版本；指定新版本号时还会报错，例如 pip 提示 `No matching distribution found`，uv 提示 `there is no version of aktools==…`。

可以等镜像同步完成，或者临时改从官方 PyPI 安装：

```shell
pip install aktools --upgrade -i https://pypi.org/simple
uvx --default-index https://pypi.org/simple --from aktools aktools-mcp
```

在 MCP 客户端配置中，把这两个参数加到 `args` 最前面即可，例如 `["--default-index", "https://pypi.org/simple", "--from", "aktools", "aktools-mcp"]`。命令行中的 `--default-index` 会覆盖 uv 配置文件里设置的镜像源。

## AI 助手提示 MCP 连接超时或启动失败 {#faq-mcp-timeout}

使用 `uvx --from aktools aktools-mcp` 时，第一次启动需要下载 AKShare 等依赖（约 150 MB），可能超过客户端的等待时间。可以先在命令行中运行一次，等它下载完成并停在等待输入的状态后按 ++ctrl+c++ 退出，再重启 AI 助手：

```shell
uvx --from aktools aktools-mcp
```

国内网络下载较慢时，可以在 MCP 配置的 `aktools` 下加上 `"env": {"UV_INDEX_URL": "https://mirrors.aliyun.com/pypi/simple/"}` 使用镜像源。

## AI 助手提示找不到 uvx 命令 {#faq-mcp-uvx}

Claude Desktop、Cursor 等桌面应用不一定能读到命令行中的 PATH 设置，即使命令行中能运行 `uvx`，应用也可能报 `spawn uvx ENOENT` 之类的错误。请把配置中的 `"command": "uvx"` 改为 `uvx` 的完整路径：Windows 上用 `where uvx` 查看，macOS 和 Linux 上用 `which uvx` 查看。

## 接口返回 401 {#faq-401}

服务启用了[访问令牌](deploy.md#token)，请求没有携带令牌或令牌不正确。请向服务管理员获取令牌，在请求头加上 `Authorization: Bearer <令牌>`，或在网址中加上 `_token=<令牌>`。HTTP 方式的 MCP 客户端返回 401 时，请在客户端配置中加上该请求头，详见[AI 助手（MCP）](guide/mcp.md#http)。

## 连接 /mcp 时返回 421 {#faq-mcp-421}

HTTP 方式下，服务只监听本机（默认的 `127.0.0.1`）时，为了防止 DNS 重绑定攻击，`/mcp` 只接受发往 `127.0.0.1`、`localhost` 的请求，用局域网 IP 或域名访问会返回 `421`。

- 需要局域网访问时，用 `python -m aktools --host 0.0.0.0` 启动，详见[局域网访问](guide/mcp.md#lan)。
- 通过 Nginx 等反向代理、以域名访问时，请设置环境变量 `AKTOOLS_HOST=0.0.0.0` 后再启动服务，并注意 `/mcp` 不带鉴权。

## 日志文件在哪里 {#faq-log}

AKTools 默认在**启动服务时所在的工作目录**下写入 `aktools_log.log`，每天零点轮转一次（旧日志改名为 `aktools_log.log.YYYY-MM-DD`），保留最近 7 天。部署到 Vercel 时写入 `/tmp/aktools_log.log`；工作目录不可写时写入系统临时目录。

需要指定日志目录时，设置环境变量 `AKTOOLS_LOG_DIR`，例如：

```shell
# Linux / macOS
AKTOOLS_LOG_DIR=/var/log/aktools python -m aktools
# Windows PowerShell
$env:AKTOOLS_LOG_DIR = "D:\logs\aktools"; python -m aktools
```

该目录需要事先创建好。

## 数据有误或接口报错，应该去哪里反馈 {#faq-feedback}

先在 Python 中直接调用同名的 AKShare 接口：

- 直接调用 AKShare 也有同样的问题：请到 [AKShare Issues](https://github.com/akfamily/akshare/issues) 反馈。
- 只有通过 AKTools 访问时才出问题：请到 [AKTools Issues](https://github.com/akfamily/aktools/issues) 反馈，并按 Issue 模板提供版本、启动命令、请求 URL 与完整报错。
