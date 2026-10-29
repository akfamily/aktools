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

## 生产环境 {#production}

`python -m aktools` 启动的是单进程的 Uvicorn，适合个人使用。需要同时服务多人或多个程序时，建议用 Gunicorn 管理多个 Uvicorn worker 进程，提高并发处理能力（Gunicorn 不支持 Windows，请在 Linux 或 macOS 上使用）：

```shell
pip install gunicorn uvicorn-worker
AKTOOLS_HOST=0.0.0.0 gunicorn aktools.main:app --bind 0.0.0.0:8080 --workers 4 --worker-class uvicorn_worker.UvicornWorker
```

`AKTOOLS_HOST` 告诉 AKTools 实际的监听地址，[MCP 服务](guide/mcp.md#lan)据此决定是否允许局域网访问；不使用 MCP 时可以省略。`--workers` 通常设为 CPU 核数的 2～4 倍，更多配置请参考 [Gunicorn 文档](https://gunicorn.org/)。

!!! warning "安全提示"

    AKTools 不带鉴权和限流功能，任何能访问到服务的人都可以调用全部接口。如果服务需要暴露到公网，请在前面加一层带鉴权的反向代理（如 Nginx），或者只在内网中使用。

## Docker {#docker}

### 构建镜像

仓库中提供了 [Dockerfile](https://github.com/akfamily/aktools/blob/main/Dockerfile)，构建时会安装 PyPI 上最新的 AKShare 和 AKTools。下载该文件后，在其所在目录执行：

```shell
docker build -t aktools .
```

国内网络环境下，可以指定 PyPI 镜像源加速构建：

```shell
docker build --build-arg PIP_INDEX_URL=https://mirrors.aliyun.com/pypi/simple/ -t aktools .
```

### 启动容器

```shell
docker run -d -p 8080:8080 --name aktools aktools
```

镜像默认以 Gunicorn + Uvicorn worker 的方式运行，与[生产环境](#production)的部署方式一致。如需改用普通模式启动：

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
