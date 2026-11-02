---
name: release-aktools
description: Use when releasing a new AKTools version to PyPI — e.g. "发版", "发布", "发 0.1.x", "打 tag", bumping the version, or when the release workflow (release_and_deploy.yml) fails, PyPI lacks a version, or the MCP Registry still shows the old version.
---

# 发布 AKTools 新版本

## 核心原则

PyPI 的版本号一经占用就不能重用，所以**先把仓库里的版本信息对齐、CI 通过，再打标签**。打标签后流程会自动发布到 PyPI、GitHub Release 和 MCP 官方注册表，三处都核对过才算发布完成。

## 版本号

只升最后一位，如 0.1.4 → 0.1.5，**即使有不兼容的改动**也一样。不兼容的改动在版本说明开头用加粗写明，并说明替代做法。

## 落点清单（4 处必须一致，`scripts/check_release.py` 会校验）

| # | 落点 | 做法 |
|---|---|---|
| 1 | `aktools/_version.py` | `__version__ = "X.Y.Z"` |
| 2 | `docs/aktools_version.md` | 在 `## 更新记录` 下最前面加一条：`X.Y.Z: <type>: <英文短句>`，下面空一行接**不缩进**的中文编号列表；缩进 4 格会被渲染成代码块 |
| 3 | `server.json` | 服务的 `version` 与 `packages[0].version` 两处都改 |
| 4 | git 标签 | `vX.Y.Z`，在 CI 通过后再打 |

## 步骤

1. 确认工作区干净，`git fetch` 后与 `origin/main` 无差异，且 `curl -s -o /dev/null -w "%{http_code}" https://pypi.org/pypi/aktools/X.Y.Z/json` 返回 404（版本号未被占用）。
2. 改上面前 3 处，运行收尾验证。
3. 只提交这 3 个文件：`chore: 版本号更新为 X.Y.Z`，推送到 `main`。
4. 等这次提交的 CI 通过：`gh run list -R akfamily/aktools --workflow build --commit <完整提交号>`。**必须用完整的 40 位提交号**，短提交号会查不到结果，导致一直空等。
5. 打带注释的标签并推送：`git tag -a vX.Y.Z -m "release vX.Y.Z" <提交号> && git push origin vX.Y.Z`。
6. 等 `release_and_deploy.yml` 跑完，它有两个任务：`deploy`（PyPI 与 GitHub Release）和 `publish-mcp-registry`。按标签名查运行记录：`gh run list --workflow release_and_deploy.yml --json headBranch` 中 `headBranch == "vX.Y.Z"`。

## 收尾验证

发版前：

```bash
python -I scripts/check_release.py vX.Y.Z
uv run pytest -q
uv run --group docs zensical build --strict
uv build -o /tmp/dist && uvx twine check /tmp/dist/*
```

有 `mcp-publisher` 时，再运行 `mcp-publisher validate server.json`。版本与 `release_and_deploy.yml` 中的 `MCP_PUBLISHER_VERSION` 保持一致。

发布后，以下几项都要核对：

- `https://pypi.org/pypi/aktools/X.Y.Z/json` 返回 200
- `gh release view vX.Y.Z -R akfamily/aktools` 不是草稿
- `https://registry.modelcontextprotocol.io/v0.1/servers?search=io.github.akfamily/aktools` 中 X.Y.Z 的 `isLatest` 为 true
- 从官方 PyPI 实际启动：`uvx --no-config --default-index https://pypi.org/simple --refresh aktools@X.Y.Z mcp`，发送 initialize 后，握手响应中的版本为 X.Y.Z。**先把输出写到文件再读**，直接用管道传给解析脚本，偶尔会读到空结果

## 常见错误

- **`deploy` 在 “Publish package to PyPI” 失败，日志是 `RekorClientError ... HTTP 502`**：sigstore 签名服务临时故障，失败发生在上传之前，版本号没有被占用。等 3 分钟左右运行 `gh run rerun <id> --failed`，可能需要重跑两次。**不要**为了绕过它关闭 `attestations`，那会去掉来源证明，需要维护者同意。
- **只有 `publish-mcp-registry` 失败**：PyPI 已经发布成功，只重跑这个任务即可，不要重新发版。
- **本机装不到新版本**：本机 uv 配置了清华镜像，镜像同步需要几个小时。验证时加 `--no-config --default-index https://pypi.org/simple`，单靠 `UV_INDEX_URL` 覆盖不了配置文件。
- **README 中的 `<!-- mcp-name: io.github.akfamily/aktools -->` 被删掉**：注册表靠它确认 PyPI 包的归属，删掉后登记会失败（有测试保护）。
- 用 `git add -A` 把日志等无关文件带进了版本提交；只按文件名暂存。

## 同步 AKShare

本次改动涉及 MCP 工具、配置片段或行数限制时，发版后按 **REQUIRED SUB-SKILL: mcp-tool-change** 的“同步 AKShare”一节处理。
