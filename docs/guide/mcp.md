# AI 助手（MCP）

AKTools 内置了 [MCP](https://modelcontextprotocol.io/)（Model Context Protocol，模型上下文协议）服务。接入后，可以直接在 Claude、Cursor 等 AI 助手中用自然语言获取数据，例如“帮我查一下贵州茅台 2024 年 10 月 8 日到 11 日的日线行情”，助手会自己查找接口、填写参数并取回数据。

安装 AKTools 时已经包含 MCP 服务，不需要额外安装。

## 两种接入方式 {#modes}

| 方式 | 怎么用 | 适合 |
| --- | --- | --- |
| stdio（推荐） | 由 AI 助手自动启动 `aktools-mcp` 命令，不需要先运行服务 | 个人在自己电脑上使用 |
| HTTP | 先运行 `python -m aktools`，助手连接 `http://127.0.0.1:8080/mcp` | 多人或多台电脑共用一个服务 |

两种方式提供的工具完全相同。

## stdio 方式 {#stdio}

推荐用 [uv](https://docs.astral.sh/uv/) 的 `uvx` 启动：它会自动下载并在独立环境中运行 AKTools，不需要事先用 pip 安装。请先[安装 uv](https://docs.astral.sh/uv/getting-started/installation/)。

=== "Claude Desktop"

    打开设置中的“开发者 → 编辑配置”，在 `claude_desktop_config.json` 中添加：

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

    保存后重启 Claude Desktop。

=== "Claude Code"

    在命令行中运行：

    ```shell
    claude mcp add aktools -- uvx --from aktools aktools-mcp
    ```

=== "Cursor"

    在项目的 `.cursor/mcp.json`（或全局的 `~/.cursor/mcp.json`）中添加：

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

!!! tip "首次启动较慢"

    第一次启动时，`uvx` 需要下载 AKShare 等依赖（约 150 MB），可能需要几分钟，客户端可能提示连接超时。下载完成后重启客户端即可。国内网络可以在配置中加上镜像源，例如在 `aktools` 下添加 `"env": {"UV_INDEX_URL": "https://mirrors.aliyun.com/pypi/simple/"}`。

已经用 pip 安装了 AKTools 时，也可以把 `command` 设为 `aktools-mcp`、去掉 `args`。这要求客户端能在 PATH 中找到该命令；找不到时，请改用命令的完整路径（Windows 上可用 `where aktools-mcp` 查看，macOS 和 Linux 上用 `which aktools-mcp`）。

## HTTP 方式 {#http}

先启动服务：

```shell
python -m aktools
```

然后在支持 Streamable HTTP 的客户端中填写 `http://127.0.0.1:8080/mcp`，例如 Claude Code：

```shell
claude mcp add --transport http aktools http://127.0.0.1:8080/mcp
```

Cursor 则在 `mcp.json` 中使用 `"url": "http://127.0.0.1:8080/mcp"` 代替 `command` 与 `args`。使用过程中服务需要保持运行。

## 提供的工具 {#tools}

AKShare 有一千多个接口，如果逐个注册成工具，会占满助手的上下文。因此 AKTools 只提供 3 个通用工具，由助手分步使用：

| 工具 | 作用 |
| --- | --- |
| `search_interfaces` | 按关键词搜索接口，返回接口名与中文标题，最多 50 个 |
| `describe_interface` | 查看接口的参数、默认值和说明 |
| `get_data` | 传入接口名和参数获取数据，默认最多返回 100 行，可用 `max_rows` 调整，最多 1000 行 |

数据超过返回行数时，`get_data` 会给出总行数。HTTP 方式下还会给出完整数据的 CSV 下载地址，例如 `/api/public/stock_zh_a_daily?symbol=sh600519&_format=csv`，在地址前加上服务地址即可下载；stdio 方式没有 HTTP 服务，因此不提供下载地址。

`get_data` 与 `/api/public` 使用同一套逻辑，同样经过[数据缓存](usage.md#cache)，出错时的说明也相同。

## 局域网访问 {#lan}

为了防止恶意网页通过浏览器访问本机服务（DNS 重绑定攻击），HTTP 方式下服务只监听本机时，MCP 只接受发往 `127.0.0.1`、`localhost` 的请求。需要让其他电脑上的 AI 助手访问时，按[让其他机器访问](../deploy.md#lan)的方法启动：

```shell
python -m aktools --host 0.0.0.0
```

其他电脑使用 `http://<本机 IP>:8080/mcp` 连接。

用 Gunicorn 部署时，请通过环境变量 `AKTOOLS_HOST` 告诉 AKTools 实际的监听地址，详见[部署](../deploy.md#production)；Docker 镜像中已设置为 `0.0.0.0`。

!!! warning "安全提示"

    MCP 与 `/api/public` 一样不带鉴权，能访问到 `/mcp` 的人都可以通过它获取数据。请只在本机或内网中使用。
