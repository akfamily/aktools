## AKTools

AKTools is a package of HTTP API for AKShare! It depends on AKShare, FastAPI and Typer.

[AKTools](https://github.com/akfamily/aktools) 是一款用于快速搭建 [AKShare](https://github.com/akfamily/akshare) HTTP API 的工具，
通过 [AKTools](https://github.com/akfamily/aktools) 可以利用一行命令来启动 HTTP 服务，
从而让原本专属服务于 Python 用户的开源财经数据接口库 [AKShare](https://github.com/akfamily/akshare) 的使用突破编程语言的限制。
无论您使用的是 C/C++、Java、Go、Rust、Ruby、PHP、JavaScript、R、Matlab、Stata 等编程语言或软件都可以快速、
轻松获取财经数据，助力您更好地展开研究和开发工作。

## 安装

<div class="termy">

```console
$ pip install aktools
---> 100%
Successfully installed aktools
```

</div>

## 升级

<div class="termy">

```console
$ pip install aktools --upgrade -i https://pypi.org/simple
---> 100%
Successfully upgraded aktools
```

</div>

## 相关项目

- [AKShare 文档](https://akshare.akfamily.xyz/)
- [FastAPI 文档](https://fastapi.tiangolo.com/)
- [Typer 文档](https://typer.tiangolo.com/)

## 快速开始

1. 在命令行运行 `python -m aktools` 启动服务
2. 浏览器打开 `http://127.0.0.1:8080/` 查看主页与说明信息
3. 连通性测试：浏览器打开 `http://127.0.0.1:8080/api/public/tool_trade_date_hist_sina`（新浪交易日历，无需参数且稳定）
4. 获取数据并带参数：`http://127.0.0.1:8080/api/public/stock_zh_a_hist?symbol=600000`

更详细的安装说明、启动参数、R / MATLAB 等多语言调用案例与 Docker 部署方式，请见 [详细文档](aktools.md)。
