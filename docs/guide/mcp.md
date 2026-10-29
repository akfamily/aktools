# AI 助手（MCP）

AKTools 内置了 [MCP](https://modelcontextprotocol.io/)（Model Context Protocol，模型上下文协议）服务。接入后，可以直接在 Claude、Cursor 等 AI 助手中用自然语言获取数据，例如“帮我查一下贵州茅台 2024 年 10 月 8 日到 11 日的日线行情”，助手会自己查找接口、填写参数并取回数据。

## 安装 {#install}

MCP 是可选功能，需要安装额外的依赖：

```shell
pip install "aktools[mcp]"
```

安装后正常启动服务即可，MCP 服务的地址为：

```text
http://127.0.0.1:8080/mcp
```

没有安装时，服务的其他功能照常可用，只是没有 `/mcp` 地址。使用仓库中的 [Dockerfile](https://github.com/akfamily/aktools/blob/main/Dockerfile) 构建的镜像已包含 MCP 依赖。

## 在 AI 助手中添加 {#clients}

AKTools 使用 MCP 的 Streamable HTTP 方式提供服务，支持这种方式的客户端填写上面的地址即可。

=== "Claude Code"

    在命令行中运行：

    ```shell
    claude mcp add --transport http aktools http://127.0.0.1:8080/mcp
    ```

=== "Cursor"

    在项目的 `.cursor/mcp.json`（或全局的 `~/.cursor/mcp.json`）中添加：

    ```json
    {
      "mcpServers": {
        "aktools": {
          "url": "http://127.0.0.1:8080/mcp"
        }
      }
    }
    ```

添加后，在助手中提问即可。使用过程中 AKTools 服务需要保持运行。

## 提供的工具 {#tools}

AKShare 有一千多个接口，如果逐个注册成工具，会占满助手的上下文。因此 AKTools 只提供 3 个通用工具，由助手分步使用：

| 工具 | 作用 |
| --- | --- |
| `search_interfaces` | 按关键词搜索接口，返回接口名与中文标题，最多 50 个 |
| `describe_interface` | 查看接口的参数、默认值和说明 |
| `get_data` | 传入接口名和参数获取数据，默认最多返回 100 行，可用 `max_rows` 调整，最多 1000 行 |

数据超过返回行数时，`get_data` 会给出总行数和完整数据的 CSV 下载地址，例如 `/api/public/stock_zh_a_daily?symbol=sh600519&_format=csv`，在地址前加上服务地址即可下载。

`get_data` 与 `/api/public` 使用同一套逻辑，同样经过[数据缓存](usage.md#cache)，出错时的说明也相同。

## 局域网访问 {#lan}

为了防止恶意网页通过浏览器访问本机服务（DNS 重绑定攻击），服务只监听本机时，MCP 只接受发往 `127.0.0.1`、`localhost` 的请求。需要让其他电脑上的 AI 助手访问时，按[让其他机器访问](../deploy.md#lan)的方法启动：

```shell
python -m aktools --host 0.0.0.0
```

其他电脑使用 `http://<本机 IP>:8080/mcp` 连接。

用 Gunicorn 部署时，请通过环境变量 `AKTOOLS_HOST` 告诉 AKTools 实际的监听地址，详见[部署](../deploy.md#production)；Docker 镜像中已设置为 `0.0.0.0`。

!!! warning "安全提示"

    MCP 与 `/api/public` 一样不带鉴权，能访问到 `/mcp` 的人都可以通过它获取数据。请只在本机或内网中使用。
