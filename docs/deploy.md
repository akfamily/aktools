# 部署

本页介绍启动参数、如何让其他机器访问，以及生产环境与 Docker 部署。只在自己电脑上使用时，按[快速入门](getting-started.md)运行 `python -m aktools` 即可，不需要阅读本页。

## 启动参数 {#options}

| 参数 | 简写 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `--host` | `-H` | `127.0.0.1` | 监听地址 |
| `--port` | `-P` | `8080` | 监听端口 |
| `--auto` | `-A` | 关闭 | 启动后自动打开浏览器 |
| `--cache-ttl` | — | `60` | 结果缓存的有效期（秒），`0` 为关闭，详见[缓存设置](#cache) |
| `--akshare-cache-clear` | — | `3600` | 清空 AKShare 内部缓存的间隔（秒），`0` 为关闭，详见[缓存设置](#cache) |
| `--proxy` | — | 不设置 | 访问上游数据源使用的代理，详见[代理与超时](#network) |
| `--timeout` | — | `60` | 访问上游数据源的读取超时（秒），详见[代理与超时](#network) |
| `--token` | — | 不设置 | 访问令牌，详见[访问令牌](#token) |
| `--version` | `-v` | — | 查看 AKTools 版本 |
| `--help` | — | — | 查看帮助 |

例如，在 8888 端口启动并自动打开浏览器：

```shell
python -m aktools --port 8888 --auto
```

8080 端口已被其他程序占用时，也可以用 `--port` 换一个端口。

## 让其他机器访问 {#lan}

默认的 `127.0.0.1` 只允许本机访问。需要让局域网内的其他电脑或程序访问时，把监听地址设为 `0.0.0.0`：

```shell
python -m aktools --host 0.0.0.0 --port 8888
```

其他机器通过 `http://<本机 IP>:8888` 访问。本机 IP 可以在 Windows 上用 `ipconfig`、在 macOS 和 Linux 上用 `ifconfig` 或 `ip addr` 查看，通常形如 `192.168.x.x`。

!!! note "0.0.0.0 不是访问地址"

    `0.0.0.0` 只是“监听所有网卡”的意思，不能在浏览器中打开。监听 `0.0.0.0` 时，命令行打印的链接和 `--auto` 打开的页面会自动使用 `127.0.0.1`。

其他机器仍然无法访问时，请参考[常见问题](faq.md#faq-remote)。

## 缓存设置 {#cache}

AKTools 有两种缓存，都可以在启动时调整：

| 缓存 | 作用 | 命令行参数 | 环境变量 | 默认值 |
| --- | --- | --- | --- | --- |
| 结果缓存 | 同一接口、同样参数在有效期内直接返回上次的数据 | `--cache-ttl` | `AKTOOLS_CACHE_TTL` | 60 秒 |
| AKShare 内部缓存清理 | AKShare 的部分接口会把板块名称、代码对照表等数据缓存在内存中，服务长期运行时会一直不更新，因此定期清空 | `--akshare-cache-clear` | `AKTOOLS_AKSHARE_CACHE_CLEAR` | 3600 秒 |

例如，关闭结果缓存，并每 10 分钟清空一次 AKShare 内部缓存：

```shell
python -m aktools --cache-ttl 0 --akshare-cache-clear 600
```

用 Gunicorn 或 Docker 部署时，通过环境变量设置：

```shell
AKTOOLS_CACHE_TTL=300 gunicorn aktools.main:app --bind 0.0.0.0:8080 --workers 4 --worker-class uvicorn_worker.UvicornWorker
docker run -d -p 8080:8080 -e AKTOOLS_CACHE_TTL=300 --name aktools aktools
```

缓存保存在进程内存中，服务重启后清空。Gunicorn 启动多个 worker 进程时，每个进程各有一份缓存，因此同样的请求可能分别由不同进程各访问一次上游网站。

## 代理与超时 {#network}

AKTools 通过 AKShare 访问东方财富、新浪财经等上游网站，可以为这些请求指定代理和超时：

| 设置 | 命令行参数 | 环境变量 | 默认值 |
| --- | --- | --- | --- |
| 代理 | `--proxy` | `AKTOOLS_PROXY` | 不设置，沿用 `HTTP_PROXY`、`HTTPS_PROXY` 等环境变量 |
| 读取超时 | `--timeout` | `AKTOOLS_TIMEOUT` | 60 秒（AKShare 的默认值） |

例如，经本机 7890 端口的代理访问，并把读取超时调大到 120 秒：

```shell
python -m aktools --proxy http://127.0.0.1:7890 --timeout 120
```

- 代理同时用于 http 与 https 请求，只影响 AKTools 访问上游网站，不影响本机其他程序。
- 读取超时指两次收到数据之间的最长等待时间，不是整个请求的总时长；连接超时固定为 10 秒。数据量大、上游响应慢的接口经常超时时再调大。
- 两项都在服务启动时设置一次，对所有请求生效，不能按请求单独指定。
- 用 Gunicorn、Docker 部署时设置环境变量，例如 `docker run -e AKTOOLS_PROXY=http://代理地址:端口 ...`；以 stdio 方式运行 MCP 时，在客户端配置的 `env` 中设置，详见[AI 助手（MCP）](guide/mcp.md#stdio)。
- 少数直接调用底层库的 AKShare 接口可能不受这两项设置影响，以 AKShare 文档为准。

## 访问令牌 {#token}

多人或多台电脑共用一个服务时，可以设置访问令牌，只让持有令牌的人使用：

```shell
python -m aktools --host 0.0.0.0 --token 一串足够长的随机字符
```

也可以用环境变量 `AKTOOLS_TOKEN` 设置，Gunicorn、Docker 部署时同样适用，例如 `docker run -e AKTOOLS_TOKEN=... aktools`。随机令牌可以用 `python -c "import secrets; print(secrets.token_urlsafe(32))"` 生成。

设置后，数据接口（`/api/` 开头的地址）与 `/mcp` 需要携带令牌，否则返回 `401`；主页、`/version` 与 `/docs` 只展示版本和使用说明，仍然公开。携带令牌有两种方式：

| 方式 | 写法 | 适合 |
| --- | --- | --- |
| 请求头 | `Authorization: Bearer <令牌>` | 程序、MCP 客户端 |
| 查询参数 | 在网址末尾加上 `_token=<令牌>`，如 `/api/public/stock_zh_a_hist?symbol=000001&_token=<令牌>` | Excel、Stata、浏览器等不便设置请求头的场景 |

- 多个令牌用逗号分隔，如 `--token alice令牌,bob令牌`，任意一个均可访问。每人一个令牌时，删掉某个令牌即可单独撤销此人的权限，修改后需要重启服务。
- 写在网址中的令牌会出现在浏览器历史、服务的访问日志和反向代理的日志里，请尽量用请求头方式；经公网访问时请配合 HTTPS 使用，否则令牌会以明文传输。
- 以 stdio 方式运行的 MCP（`aktools-mcp`）不经过网络，不需要令牌。HTTP 方式的 MCP 客户端需要配置请求头，详见[AI 助手（MCP）](guide/mcp.md#http)。

!!! note "为什么不提供用户登录"

    令牌是一把共享的“钥匙”，适合团队内部共用。AKTools 不保存用户信息，因此不提供注册、登录和按人分配权限。需要对接企业账号或按人管理权限时，请在前面加一层现成的认证网关，如 OAuth2 Proxy、Cloudflare Access。

## 生产环境 {#production}

`python -m aktools` 启动的是单进程的 Uvicorn，适合个人使用。需要同时服务多人或多个程序时，建议用 Gunicorn 管理多个 Uvicorn worker 进程，提高并发处理能力（Gunicorn 不支持 Windows，请在 Linux 或 macOS 上使用）：

```shell
pip install gunicorn uvicorn-worker
AKTOOLS_HOST=0.0.0.0 gunicorn aktools.main:app --bind 0.0.0.0:8080 --workers 4 --worker-class uvicorn_worker.UvicornWorker
```

`AKTOOLS_HOST` 告诉 AKTools 实际的监听地址，[MCP 服务](guide/mcp.md#lan)据此决定是否允许局域网访问；不使用 MCP 时可以省略。`--workers` 通常设为 CPU 核数的 2～4 倍，更多配置请参考 [Gunicorn 文档](https://gunicorn.org/)。

!!! warning "安全提示"

    未设置[访问令牌](#token)时，任何能访问到服务的人都可以调用全部接口。AKTools 不带限流功能，所有请求都从服务器的同一个 IP 访问上游网站，不建议开放给不特定的人使用；确需对外提供时，请设置访问令牌并配合 HTTPS。

使用 Nginx 等反向代理时，请转发 `Host` 与 `X-Forwarded-Proto` 请求头（如 `proxy_set_header Host $host;`、`proxy_set_header X-Forwarded-Proto $scheme;`），主页上显示的地址才会是用户实际访问的域名与协议。服务默认只信任本机反向代理传来的这些请求头；反向代理在其他机器上时，Gunicorn 需加上 `--forwarded-allow-ips <反向代理的 IP>`。

## Docker {#docker}

### 构建镜像

仓库中提供了 [Dockerfile](https://github.com/akfamily/aktools/blob/main/Dockerfile)，构建时会从 PyPI 安装最新的 AKShare 和 AKTools，不需要仓库中的其他文件。下载该文件后，在其所在目录执行：

```shell
docker build -t aktools .
```

国内网络通常无法访问 Docker Hub 与官方 PyPI，可以分别用 `BASE_IMAGE` 指定基础镜像的镜像站、用 `PIP_INDEX_URL` 指定 PyPI 镜像源：

```shell
docker build --build-arg BASE_IMAGE=docker.m.daocloud.io/library/python:3.14-slim-trixie --build-arg PIP_INDEX_URL=https://mirrors.aliyun.com/pypi/simple/ -t aktools .
```

`docker.m.daocloud.io` 是 DaoCloud 提供的 Docker Hub 镜像站，也可以换成其他可用的镜像站。刚发版后 PyPI 镜像源可能还没有同步新版本，详见[常见问题](faq.md#faq-mirror)。

### 启动容器

```shell
docker run -d -p 8080:8080 --name aktools aktools
```

镜像默认以 Gunicorn + Uvicorn worker 的方式运行，默认只启动 1 个 worker 进程。需要更高的并发能力时，用 `WEB_CONCURRENCY` 指定 worker 数量，参考[生产环境](#production)中的说明：

```shell
docker run -d -p 8080:8080 -e WEB_CONCURRENCY=4 --name aktools aktools
```

如需改用普通模式启动：

```shell
docker run -d -p 8080:8080 --name aktools aktools python -m aktools --host 0.0.0.0 --port 8080
```

启动后访问 `http://127.0.0.1:8080/api/public/tool_trade_date_hist_sina`，能获取到数据即表示部署成功。

### 升级镜像

镜像中的 AKShare 版本在构建时固定。需要升级时，加上 `--no-cache` 重新构建，再用新镜像重建容器即可：

```shell
docker build --no-cache -t aktools .
docker rm -f aktools
docker run -d -p 8080:8080 --name aktools aktools
```
