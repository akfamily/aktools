---
name: mcp-tool-change
description: Use when changing AKTools' MCP server (aktools/mcp_server.py) — adding or changing a tool, its parameters or return fields, the row limits, the client config snippet, or stdio/HTTP transport behaviour — e.g. "改 MCP 工具", "get_data 加参数", "MCP 配置", "llms.txt", "同步 akshare 的 mcp 文档".
---

# 修改 MCP 服务（AKTools）

## 核心原则

MCP 工具的说明除了代码，还写在**本仓库 3 处文档和 AKShare 仓库 2 个文件**里。AI 助手读的是这些说明，漏改一处，助手就会按旧的参数去调用。stdio 方式下 stdout 只能输出协议消息，写错一行就会让客户端断开连接。

## 代码约束（细节见 CLAUDE.md 的 `aktools/mcp_server.py` 一节）

- 只保留 `search_interfaces`、`describe_interface`、`get_data` 三个通用工具，不要为每个接口单独注册工具。
- 取数一律经过 `aktools.core.fetch.fetch_dataframe`，与 `/api/public` 共用缓存、参数名检查和错误分类。
- 错误只能抛 `ToolError`。SDK 会隐藏其他异常的文字，助手只能看到一句笼统的出错提示。
- 新工具加上 `annotations=READ_ONLY`。
- 参数用 `Annotated[..., Field(description=...)]` 写中文说明，这些说明会作为工具的输入说明（schema）发给助手。
- stdio 方式下没有 HTTP 服务，返回结果里的 `csv_url` 必须为 `None`。

## 落点清单

| # | 落点 | 改什么 |
|---|---|---|
| 1 | `aktools/mcp_server.py` | 工具本身，以及 `INSTRUCTIONS` 中的使用步骤 |
| 2 | `tests/test_mcp.py` | 先写测试再改代码，确认测试在改动前失败 |
| 3 | `docs/guide/mcp.md` →「提供的工具」 | 工具表格与表格下方的说明 |
| 4 | `docs/llms.txt` | 英文的工具签名、返回字段与限制 |
| 5 | 客户端配置片段（只在改动配置时） | 5 处一起改：`README.md`、`docs/index.md`、`docs/getting-started.md#mcp`、`docs/guide/mcp.md`、`docs/llms.txt` |
| 6 | `CLAUDE.md` | 新增约束或容易踩的坑时补充 |

## 收尾验证

```bash
uv run pytest -q tests/test_mcp.py        # 连续跑 3 次：stdio 测试依赖子进程，偶发失败要当真
uv run pytest -q
uv run --group docs zensical build --strict
```

再用真实客户端走一遍 stdio：先 `uv build -o /tmp/dist`，然后用 `mcp.client.Client` 加 `StdioServerParameters(command="uvx", args=["--no-config", "--default-index", "https://pypi.org/simple", "--from", "<wheel 路径>", "aktools-mcp"])` 跑一遍“搜索 → 查看参数 → 取数”。输出写到文件再读。本机 HTTP 代理不可用时，在 `env` 中把 `HTTP_PROXY`、`HTTPS_PROXY` 设为空。

## 同步 AKShare

AKShare 的 `docs/mcp.md`（https://akshare.akfamily.xyz/mcp.html）改写自 `docs/guide/mcp.md`，它的 `llms.txt` 也有 MCP 一节。清单第 3、4、5 项有改动时，两边要一起更新，而且要等 **AKTools 发版之后**，否则 AKShare 的文档会描述用户还用不上的功能。

1. 在 AKShare 仓库基于最新的 `origin/main` 新建分支，如 `docs/aktools-mcp-<主题>`，只改 `docs/mcp.md` 与 `llms.txt`。
2. 使用该仓库自己配置的 git 身份。提交前要通过 AKShare 的 pre-commit 检查，包括中文标点检查与 Conventional Commits 格式检查。
3. 推送分支并提交 PR。AKShare 的 `main` 有规则集，要求通过状态检查，**不要直接推送 `main`**。只有维护者明确要求时，才由你合并（只允许 squash 合并）并发版。
4. AKShare 发版要按它自己 `CLAUDE.md` 中的 “Release checklist” 进行：改 `akshare/_version.py` 与 `docs/changelog.md`，标签为 `vX.Y.Z`。如果 `main` 上已有改过版本号但还没发布的版本，就把这次改动并进去一起发，不要跳号。

## 常见错误

- 用 `print` 或日志写到 stdout：在 stdio 方式下会混进协议通道。`main()` 已经把 stdout 换成无缓冲流，不要再改回去。
- 把 `/mcp` 用 `app.mount` 挂载：`/mcp` 会被 307 重定向到 `/mcp/`，部分客户端不会跟随。用 `TestClient` 测试时要加 `follow_redirects=False`，否则测不出这个问题。
- 只改了 `docs/guide/mcp.md`，漏了 `docs/llms.txt` 或 AKShare 那两个文件。
- 断言写得太松，比如只检查报错里含参数名，而报错原文本身就带这个词，修改前测试也能通过。改完后要确认测试在改动前确实会失败。
