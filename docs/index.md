# AKTools

> AKTools exposes AKShare's financial data interfaces as an HTTP API, so you can fetch data from any programming language.

[AKTools](https://github.com/akfamily/aktools) 是一款用于快速搭建 [AKShare](https://github.com/akfamily/akshare) HTTP API 的工具。只需一行命令即可启动 HTTP 服务，让原本只服务于 Python 用户的开源财经数据接口库 AKShare 突破编程语言的限制：无论您使用的是 C/C++、Java、Go、Rust、Ruby、PHP、JavaScript、R、MATLAB、Stata 等编程语言或软件，都可以快速、轻松地获取财经数据，助力您更好地展开研究和开发工作。

## 特性

- **零配置**：`python -m aktools` 一行命令启动服务，无需编写任何代码
- **接口全覆盖**：AKShare 的每个数据接口都可以通过 `/api/public/<接口名>` 直接访问，AKShare 新增接口后升级即可使用
- **跨语言**：返回标准 JSON，任何能发送 HTTP 请求的语言或软件都可以调用
- **自带文档**：基于 FastAPI，启动后访问 `/docs` 即可在线查看和调试接口
- **便于部署**：提供 Dockerfile，支持 Gunicorn + Uvicorn 多进程部署

## 安装

AKTools 要求 Python 3.11 及以上（64 位）。

<div class="termy">

```console
$ pip install aktools
---> 100%
Successfully installed aktools
```

</div>

## 升级

AKShare 的数据接口会随上游网站的变化频繁更新，遇到问题时请先把两者都升级到最新版：

<div class="termy">

```console
$ pip install akshare aktools --upgrade -i https://pypi.org/simple
---> 100%
Successfully installed akshare aktools
```

</div>

## 快速开始

1. 在命令行运行 `python -m aktools` 启动服务
2. 浏览器打开 `http://127.0.0.1:8080/` 查看主页，打开 `http://127.0.0.1:8080/docs` 在线调试接口
3. 连通性测试：打开 `http://127.0.0.1:8080/api/public/tool_trade_date_hist_sina`（新浪交易日历，无需参数且较为稳定）
4. 带参数获取数据：`http://127.0.0.1:8080/api/public/stock_zh_a_hist?symbol=600000`

接口名与 AKShare 的函数名完全一致，参数以查询字符串传递。接口列表和参数说明请查阅 [AKShare 数据字典](https://akshare.akfamily.xyz/data/index.html)。

## 下一步

- [启动参数与服务地址](aktools.md#start)
- [调用规则与状态码](aktools.md#usage)
- [Python、JavaScript、R、MATLAB、Rust 等调用示例](aktools.md#examples)
- [生产环境与 Docker 部署](aktools.md#deploy)
- [常见问题](aktools.md#faq)

## 相关链接

- [AKTools GitHub 仓库](https://github.com/akfamily/aktools)：提交 Issue 或 Pull Request 前请阅读[贡献指南](https://github.com/akfamily/aktools/blob/main/CONTRIBUTING.md)
- [AKShare 文档](https://akshare.akfamily.xyz/)
- [FastAPI 文档](https://fastapi.tiangolo.com/)
