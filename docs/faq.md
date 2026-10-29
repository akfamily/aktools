# 常见问题

遇到问题时，先看返回的状态码：`404` 多为接口名或参数问题，`502` 多为网络问题，状态码的完整说明见[调用规则](guide/usage.md#status-codes)。

## 接口返回 502 且提示“访问上游数据源失败” {#faq-502}

AKTools 本身只是把请求转发给 AKShare，数据由东方财富、新浪财经等上游网站提供。当返回如下错误时：

```text
{"error": "访问上游数据源失败，请检查网络或代理设置（如 HTTP_PROXY/HTTPS_PROXY 环境变量）：..."}
```

通常是运行 AKTools 的机器**无法访问上游数据源**，而不是 AKTools 或接口本身的问题。常见原因与排查方法：

1. 本机配置了 HTTP 代理，但代理不可用。报错中若出现 `ProxyError`、`Unable to connect to proxy` 即属此类。请检查并按需清除代理环境变量，然后重启服务：

    ```shell
    # Linux / macOS
    unset HTTP_PROXY HTTPS_PROXY ALL_PROXY
    # Windows PowerShell
    Remove-Item Env:HTTP_PROXY, Env:HTTPS_PROXY, Env:ALL_PROXY
    ```

    若必须经代理访问外网，可通过 `NO_PROXY` 排除内网地址，或确认代理本身可用。

2. 网络不通或上游网站临时不可达：可先用 `tool_trade_date_hist_sina` 这类轻量接口测试连通性，或稍后重试。

3. 部分接口对网络环境（如需境内网络）有要求，请参考 [AKShare 文档](https://akshare.akfamily.xyz/) 中对应接口的说明。

## 接口返回 404 {#faq-404}

按错误信息分别处理：

- **未找到该接口**：接口名拼写错误，或当前安装的 AKShare 版本还没有这个接口。请升级 AKShare，并用[接口目录](guide/catalog.md#search)搜索正确的接口名。
- **调用接口出错**：通常是参数名或参数值不正确。请用[接口参数说明](guide/catalog.md#detail)检查参数名和可选值，也可以在 Python 中直接调用同名接口，确认问题是否出在 AKShare。
- **该接口返回数据为空**：参数组合没有对应的数据，例如日期范围内没有交易日。

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

## PyScript 数据展示页一直显示“数据加载中” {#faq-pyscript}

`/api/show` 与 `/api/show-temp/{接口名}` 页面在浏览器中运行 Python，首次打开需要从 jsDelivr 下载约数十 MB 的 Pyodide 与 pandas，通常需要十几到几十秒。长时间没有反应时，请检查浏览器能否访问 `fastly.jsdelivr.net`。只需要数据时，直接访问 `/api/public/{接口名}` 即可，不依赖这个页面。

## 日志文件在哪里 {#faq-log}

AKTools 在**启动服务时所在的工作目录**下写入 `aktools_log.log`，每天零点轮转一次，保留最近 7 天。部署到 Vercel 时写入 `/tmp/aktools_log.log`。

## 数据有误或接口报错，应该去哪里反馈 {#faq-feedback}

先在 Python 中直接调用同名的 AKShare 接口：

- 直接调用 AKShare 也有同样的问题：请到 [AKShare Issues](https://github.com/akfamily/akshare/issues) 反馈。
- 只有通过 AKTools 访问时才出问题：请到 [AKTools Issues](https://github.com/akfamily/aktools/issues) 反馈，并按 Issue 模板提供版本、启动命令、请求 URL 与完整报错。
