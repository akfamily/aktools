# AI 助手（MCP）

AKTools 内置了 [MCP](https://modelcontextprotocol.io/)（Model Context Protocol，模型上下文协议）服务。接入后，可以直接在 WorkBuddy、Codex、Cursor、Claude 等 AI 助手中用自然语言获取数据，例如“帮我查一下贵州茅台 2024 年 10 月 8 日到 11 日的日线行情”，助手会自己查找接口、填写参数并取回数据。

AKTools 已上架 [MCP 官方注册表](https://registry.modelcontextprotocol.io/v0.1/servers?search=io.github.akfamily/aktools)，名称为 `io.github.akfamily/aktools`，支持从注册表安装的客户端可以直接搜索添加。

安装 AKTools 时已经包含 MCP 服务，不需要额外安装。第一次配置可以先按[快速入门](../getting-started.md#mcp)的 3 个步骤操作。

## 可以问什么 {#examples}

下面是在 Claude Code 中实际提问的过程（根据真实会话记录回放）：

![在 Claude Code 中提问，AI 助手通过 AKTools 的 MCP 工具查询贵州茅台的日线行情](../img/mcp-demo.gif)

更多示例：

- “帮我查一下贵州茅台 2024 年 10 月 8 日到 11 日的前复权日线行情”
- “AKShare 里有哪些和可转债相关的接口？”
- “stock_zh_a_hist_em 这个接口有哪些参数，复权方式怎么填？”

助手每次最多取回 1000 行数据（默认 100 行），适合查看具体某段时间、某只证券的数据。需要完整的大表格时，请让助手给出 CSV 下载地址（HTTP 方式），或改用 [HTTP API](usage.md#download) 下载。

想让 AI 接着用这些数据写策略、跑回测，请看[与 AKQuant 联用](#akquant)。

## 两种接入方式 {#modes}

| 方式 | 怎么用 | 适合 |
| --- | --- | --- |
| stdio（推荐） | 由 AI 助手自动启动 `aktools-mcp` 命令，不需要先运行服务 | 个人在自己电脑上使用 |
| HTTP | 先运行 `python -m aktools`，助手连接 `http://127.0.0.1:8080/mcp` | 多人或多台电脑共用一个服务 |

两种方式提供的工具完全相同。

## stdio 方式 {#stdio}

推荐用 [uv](https://docs.astral.sh/uv/) 的 `uvx` 启动：它会自动下载并在独立环境中运行 AKTools，不需要事先用 pip 安装。请先[安装 uv](https://docs.astral.sh/uv/getting-started/installation/)。

=== "WorkBuddy"

    最简单的方法是直接对 WorkBuddy 说“安装 AKShare 的官方 MCP”，它会自己完成配置。

    也可以手动添加：在 WorkBuddy 的连接器（MCP）设置中粘贴下面的配置，或者直接编辑用户级配置文件 `~/.workbuddy/mcp.json`（Windows 上是 `C:\Users\<用户名>\.workbuddy\mcp.json`）：

    ```json
    {
      "mcpServers": {
        "aktools": {
          "command": "uvx",
          "args": ["--from", "aktools", "aktools-mcp"],
          "env": {"UV_INDEX_URL": "https://mirrors.aliyun.com/pypi/simple/"}
        }
      }
    }
    ```

    `env` 中的镜像源用来加快国内下载，在国外可以去掉。连接器显示绿色圆点即表示已连接。只想在某个项目中使用时，把配置写到项目目录下的 `.workbuddy/mcp.json`。

=== "Codex"

    在命令行中运行：

    ```shell
    codex mcp add aktools -- uvx --from aktools aktools-mcp
    ```

    也可以手动编辑 `~/.codex/config.toml`。第一次启动要下载依赖，建议把启动等待时间调长：

    ```toml
    [mcp_servers.aktools]
    command = "uvx"
    args = ["--from", "aktools", "aktools-mcp"]
    startup_timeout_sec = 120
    ```

    国内网络可以再加一行 `env = { UV_INDEX_URL = "https://mirrors.aliyun.com/pypi/simple/" }`。

=== "Cursor"

    点击按钮一键添加：

    [![Add AKTools MCP server to Cursor](https://cursor.com/deeplink/mcp-install-dark.svg)](https://cursor.com/install-mcp?name=aktools&config=eyJjb21tYW5kIjoidXZ4IiwiYXJncyI6WyItLWZyb20iLCJha3Rvb2xzIiwiYWt0b29scy1tY3AiXX0%3D)

    也可以在项目的 `.cursor/mcp.json`（或全局的 `~/.cursor/mcp.json`）中手动添加：

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

=== "Claude Code"

    在命令行中运行：

    ```shell
    claude mcp add aktools -- uvx --from aktools aktools-mcp
    ```

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

!!! tip "首次启动较慢"

    第一次启动时，`uvx` 需要下载 AKShare 等依赖（约 150 MB），可能需要几分钟，客户端可能提示连接超时。下载完成后重启客户端即可。国内网络可以在配置中加上镜像源，例如在 `aktools` 下添加 `"env": {"UV_INDEX_URL": "https://mirrors.aliyun.com/pypi/simple/"}`。需要代理或调整超时时，同样在 `env` 中加上 `AKTOOLS_PROXY`、`AKTOOLS_TIMEOUT`，详见[代理与超时](../deploy.md#network)。刚发版后镜像可能还没有同步新版本，详见[常见问题](../faq.md#faq-mirror)。

`aktools mcp` 与 `aktools-mcp` 两个命令作用相同，MCP 官方注册表中登记的启动方式是 `uvx aktools mcp`。已经用 pip 安装了 AKTools 时，也可以把 `command` 设为 `aktools-mcp`、去掉 `args`。这要求客户端能在 PATH 中找到该命令；找不到时，请改用命令的完整路径（Windows 上可用 `where aktools-mcp` 查看，macOS 和 Linux 上用 `which aktools-mcp`）。

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

服务设置了[访问令牌](../deploy.md#token)时，需要在客户端配置中加上请求头，例如 Claude Code：

```shell
claude mcp add --transport http aktools http://127.0.0.1:8080/mcp --header "Authorization: Bearer <令牌>"
```

Cursor 则在 `mcp.json` 的 `aktools` 下加上 `"headers": {"Authorization": "Bearer <令牌>"}`。`get_data` 返回的 CSV 下载地址不含令牌，下载时需要自行加上 `_token=<令牌>`。

## 提供的工具 {#tools}

AKShare 有一千多个接口，如果逐个注册成工具，会占满助手的上下文。因此 AKTools 只提供 3 个通用工具，由助手分步使用：

| 工具 | 作用 |
| --- | --- |
| `search_interfaces` | 按关键词搜索接口，可用空格分隔多个关键词（如“A股 日线”），结果按相关度排序，返回接口名、中文标题与类目，最多 50 个 |
| `describe_interface` | 查看接口的参数、默认值和说明，以及 AKShare 登记的返回列、数据范围说明与调用示例 |
| `get_data` | 传入接口名和参数获取数据，默认最多返回 100 行，可用 `max_rows` 调整，最多 1000 行；用 `offset` 翻页，负数表示从末尾倒数 |

按日期升序排列的数据，最新的行在末尾。问“最近”的数据时，助手可以用 `offset=-20` 这样的负数直接取最后 20 行，不必从头翻页。

三个工具都标注为只读（`readOnlyHint`），不会修改任何数据，支持的客户端可以据此减少确认提示。

### 数据来源与限流 {#source}

同一类数据常有多个来源，例如 A 股日线既有东方财富的 `stock_zh_a_hist_em`，也有新浪财经的 `stock_zh_a_daily_sina` 和腾讯的 `stock_zh_a_hist_tx`。`search_interfaces` 与 `describe_interface` 的结果都带有 `source` 字段，标明数据来源。

东方财富的行情类接口（实时行情、历史 K 线、板块、资金流等，约 100 个）使用的服务器在短时间内请求较多时，会临时封禁来源 IP，所有东方财富行情接口约 5 分钟以上无法使用。这类接口的来源标为“东方财富·行情（频繁访问易限流）”。东方财富的宏观、财务报表、龙虎榜等接口使用其他服务器，不受影响，来源只标“东方财富”。

AKTools 在发给助手的使用说明中要求：需要连续获取多只证券或大量行情数据时，优先选用其他来源的同类接口；遇到限流时不要立即重试。被限流时，`get_data` 的报错会说明需要等待多久，并列出 AKShare 登记的其他来源的同类接口供助手改用。

同类接口取自 AKShare 人工维护的对照表，`describe_interface` 的 `alternatives` 字段也会列出，因此助手在取数之前就能选择其他来源。对照表目前覆盖 A 股、指数、ETF、港股、美股、板块与期货的日线和实时行情等常用接口；没有登记的接口不会给出候选，AKTools 不自行猜测。同类接口的参数写法和返回列可能不同，例如新浪财经的 `stock_zh_a_daily_sina` 要把 `symbol` 写成 `sh600519`，助手会先用 `describe_interface` 查看再调用。

数据来源、限流标记与同类接口都取自 AKShare 的接口注册表：限流标记需要 AKShare 1.20.37，同类接口需要 1.20.39。AKTools 0.1.8 起要求 AKShare 不低于 1.20.48，接口名以该版本为准。

### 搜索接口的技巧 {#search-tips}

`search_interfaces` 的关键词应描述数据类型，例如“港股 日线”“期货 分钟”“可转债 实时行情”，不要写具体证券的名称或代码。AKShare 1.20.39 起搜索认得常用的同义说法，“日线”可以匹配到描述写作“日频率”“历史行情”的接口。没有匹配的结果时，返回内容会带一条提示，说明该怎么换关键词。

接口名写错，或者用了已经更名的旧接口名（如 `get_futures_daily`，现为 `futures_daily`）时，报错中会列出名称相近的接口。

数据超过返回行数时，`get_data` 会给出总行数。HTTP 方式下还会给出完整数据的 CSV 下载地址，例如 `/api/public/stock_zh_a_daily_sina?symbol=sh600519&_format=csv`，在地址前加上服务地址即可下载；stdio 方式没有 HTTP 服务，因此不提供下载地址。

`get_data` 与 `/api/public` 使用同一套逻辑，同样经过[数据缓存](usage.md#cache)，出错时的说明也相同。

## 与 AKQuant 联用：AI 自动回测 {#akquant}

[AKQuant](https://akquant.akfamily.xyz/) 是 AKFamily 的量化回测框架，也有自己的官方 MCP 服务，同样已上架 [MCP 官方注册表](https://registry.modelcontextprotocol.io/v0.1/servers?search=io.github.akfamily/akquant)，名称为 `io.github.akfamily/akquant`。两个服务一起接入后，AI 助手可以完成从数据到回测报告的全过程：

| 服务 | 负责 |
| --- | --- |
| AKTools（AKShare 官方 MCP） | 查找 AKShare 的接口、查看参数、取回数据 |
| AKQuant | 查询 AKQuant 的 API、编写并检查策略、准备行情数据、运行回测、读取成交与权益明细 |

### 一句话体验

在 WorkBuddy 中输入：

> 安装 AKShare 和 AKQuant 各自的官方 MCP，运行一个示例策略并报告结果

助手会自己完成安装，然后下载数据、编写策略、运行回测，解读收益、回撤等结果，并给出改进策略的建议。在 Codex、Cursor、Claude Code 等助手中也可以这样提问。

想让结果更具体，可以写明标的、时间和策略，例如：

- “用平安银行（000001）近三年的日线，跑一个 5 日与 20 日均线交叉的策略，报告收益、最大回撤和交易次数”
- “先查一下 AKShare 里沪深 300 指数的日线接口，再用它回测一个简单的趋势策略”
- “把刚才的策略改成只在均线向上时开仓，再跑一次，和上一次的结果对比”

### 手动配置

助手没能自动安装时，可以手动把两个服务加入配置文件。WorkBuddy、Cursor、Claude Desktop 等使用 JSON 配置的客户端：

```json
{
  "mcpServers": {
    "aktools": {
      "command": "uvx",
      "args": ["--from", "aktools", "aktools-mcp"],
      "env": {"UV_INDEX_URL": "https://mirrors.aliyun.com/pypi/simple/"}
    },
    "akquant": {
      "command": "uvx",
      "args": ["--from", "akquant[mcp]", "akquant-mcp", "--root", "D:/akquant-demo"],
      "env": {"UV_INDEX_URL": "https://mirrors.aliyun.com/pypi/simple/"}
    }
  }
}
```

Codex 与 Claude Code 在命令行中运行（把 `codex` 换成 `claude` 即为 Claude Code 的写法）：

```shell
codex mcp add aktools -- uvx --from aktools aktools-mcp
codex mcp add akquant -- uvx --from "akquant[mcp]" akquant-mcp --root D:/akquant-demo
```

`--root` 是 AKQuant 的项目目录，请先建好这个文件夹，并换成你自己的路径（macOS 上类似 `/Users/<用户名>/akquant-demo`）。Windows 路径写进 JSON 时，请用正斜杠 `/`，或把 `\` 写成 `\\`。策略文件和数据文件都必须放在这个目录中，回测结果保存在其中的 `.akquant-mcp` 文件夹里。AKQuant 的工具和参数详见 [AKQuant 的 MCP 文档](https://akquant.akfamily.xyz/guide/mcp/)。

!!! warning "注意事项"

    - AKQuant 会在本机直接运行策略代码，**没有沙箱隔离**，与自己运行 `python strategy.py` 相同。请只运行自己或助手刚写好、看过内容的策略，不要运行来源不明的策略文件。
    - 第一次启动时两个服务都要下载依赖，可能需要几分钟，详见[常见问题](../faq.md#faq-mcp-timeout)。
    - 回测结果与改进建议由 AI 生成，仅供学习和研究，不构成投资建议。

## 局域网访问 {#lan}

为了防止恶意网页通过浏览器访问本机服务（DNS 重绑定攻击），HTTP 方式下服务只监听本机时，MCP 只接受发往 `127.0.0.1`、`localhost` 的请求。需要让其他电脑上的 AI 助手访问时，按[让其他机器访问](../deploy.md#lan)的方法启动：

```shell
python -m aktools --host 0.0.0.0
```

其他电脑使用 `http://<本机 IP>:8080/mcp` 连接。

用 Gunicorn 部署时，请通过环境变量 `AKTOOLS_HOST` 告诉 AKTools 实际的监听地址，详见[部署](../deploy.md#production)；Docker 镜像中已设置为 `0.0.0.0`。

!!! warning "安全提示"

    未设置[访问令牌](../deploy.md#token)时，能访问到 `/mcp` 的人都可以通过它获取数据。多人共用或经公网访问时，请设置访问令牌。
