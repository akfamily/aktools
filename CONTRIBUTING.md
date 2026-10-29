<!-- omit in toc -->
# 参与贡献 AKTools

首先，感谢您愿意花时间参与贡献！❤️

我们欢迎并重视各种形式的贡献：报告问题、提出建议、改进文档、提交代码都非常有帮助。参与之前请先阅读下面的相关章节，这能让维护者更快地处理您的贡献，也让整个过程更顺畅。

> 如果您喜欢这个项目但暂时没有时间参与，也可以通过以下方式支持我们：
> - 给项目点一个 Star
> - 在您的项目 README 中引用 AKTools
> - 向朋友或同事推荐 AKTools

<!-- omit in toc -->
## 目录

- [行为准则](#行为准则)
- [先确认问题属于哪个项目](#先确认问题属于哪个项目)
- [提问](#提问)
- [报告 Bug](#报告-bug)
- [提出改进建议](#提出改进建议)
- [贡献代码](#贡献代码)
- [改进文档](#改进文档)
- [提交信息规范](#提交信息规范)
- [发布流程（维护者）](#发布流程维护者)
- [法律声明](#法律声明)

## 行为准则

本项目及所有参与者均须遵守 [AKTools 贡献者行为准则](https://github.com/akfamily/aktools/blob/main/CODE_OF_CONDUCT.md)。参与本项目即表示您同意遵守该准则。如发现不可接受的行为，请发送邮件至 <albertandking@gmail.com> 报告。

## 先确认问题属于哪个项目

AKTools 只是 [AKShare](https://github.com/akfamily/akshare) 外面的一层 HTTP 封装：请求 `/api/public/<接口名>` 时，AKTools 调用同名的 AKShare 接口，再把返回的 DataFrame 转成 JSON。因此**绝大多数数据问题其实是 AKShare 的问题**。

提交 Issue 前，请先在 Python 中直接调用同名接口：

```python
import akshare as ak

df = ak.stock_zh_a_hist(symbol="000001")  # 换成您出问题的接口和参数
print(df)
```

- 直接调用 AKShare **也有问题**（报错、数据有误、接口缺失）：请到 [AKShare Issues](https://github.com/akfamily/akshare/issues) 反馈。
- 直接调用 AKShare **正常**，只有通过 AKTools 访问时才出问题（启动失败、路由、参数解析、JSON 序列化、主页等）：请到 [AKTools Issues](https://github.com/akfamily/aktools/issues) 反馈。
- 返回 `502` 且提示“访问上游数据源失败”：通常是网络或代理问题，请先按 [README 常见问题](https://github.com/akfamily/aktools#常见问题) 排查。

## 提问

提问前，请先阅读 [AKTools 文档](https://aktools.akfamily.xyz/) 和 [AKShare 文档](https://akshare.akfamily.xyz/)，并搜索已有的 [Issues](https://github.com/akfamily/aktools/issues)。如果已有相关 Issue 但仍需要进一步说明，请直接在该 Issue 下追问。

如果仍然需要提问，请[新建 Issue](https://github.com/akfamily/aktools/issues/new)，并尽可能提供以下信息：

- 您想做什么，遇到了什么情况
- 操作系统、Python、AKShare 与 AKTools 的版本（版本可以通过 `http://127.0.0.1:8080/version` 获取）

## 报告 Bug

<!-- omit in toc -->
### 提交之前

好的 Bug 报告不需要维护者反复追问细节。提交之前请：

- 把 AKShare 与 AKTools 都升级到最新版：`pip install akshare aktools --upgrade`，确认问题仍然存在。
- 按[先确认问题属于哪个项目](#先确认问题属于哪个项目)排除 AKShare 本身的问题。
- 在[已有的 Bug 报告](https://github.com/akfamily/aktools/issues?q=label%3Abug)中搜索是否有人反馈过同样的问题。

<!-- omit in toc -->
### 如何提交

请使用 [AKTools 问题报告](https://github.com/akfamily/aktools/issues/new?template=aktools_report.md) 模板新建 Issue，并提供：

1. 操作系统及版本（目前只支持 64 位主流操作系统）
2. Python、AKShare 与 AKTools 的版本
3. 启动 AKTools 的命令，以及访问的完整 URL（接口名与参数）
4. 期望的结果与实际的结果
5. 完整的报错信息或异常堆栈（请粘贴文本，不要只发截图）

提交之后，维护者会尝试复现问题，并打上 `bug`、`question` 等标签。如果无法复现，维护者会请您补充信息。

> **安全问题请勿公开提交。** 涉及安全漏洞或包含敏感信息的问题，请不要发到 Issue 或其他公开渠道，而是发送邮件至 <albertandking@gmail.com>。

## 提出改进建议

改进建议包括全新的功能，也包括对现有功能的小改进。提交之前，请先：

- 确认您使用的是最新版本，并阅读文档，确认该功能尚未提供。
- [搜索已有的 Issues](https://github.com/akfamily/aktools/issues?q=label%3Aenhancement)，如果已经有人提过，请在原 Issue 下补充您的意见，不要重复新建。
- 想一想这个功能是否符合项目定位。AKTools 的定位是**轻量的转发层**，本身几乎不包含业务逻辑。新增数据接口、修改数据内容等需求，请到 AKShare 提出。

新建 Issue 时请：

- 使用**清晰、具体的标题**
- **描述当前的行为**，以及**您期望的行为**和理由
- 尽可能给出具体的使用场景，或其他项目中值得参考的做法

## 贡献代码

<!-- omit in toc -->
### 搭建开发环境

AKTools 使用 [uv](https://docs.astral.sh/uv/) 管理开发环境，要求 Python 3.11 及以上。`uv.lock` 已提交到仓库，每个人安装的依赖版本都和 CI 一致。

```bash
git clone https://github.com/<您的用户名>/aktools.git  # 先 Fork 本仓库
cd aktools
uv sync                     # 安装 AKTools 以及 dev 依赖组（pytest、ruff、pre-commit 等）
uv run pre-commit install   # 安装 pre-commit 与 commit-msg 两个钩子
```

本地启动服务：

```bash
uv run python -m aktools --host 127.0.0.1 --port 8080   # 然后打开 http://127.0.0.1:8080/docs
```

<!-- omit in toc -->
### 项目结构

| 路径 | 说明 |
| --- | --- |
| `aktools/main.py` | 创建 FastAPI 应用，提供主页、`/version`，并把核心路由挂载到 `/api` 下 |
| `aktools/core/api.py` | 核心逻辑：`/api/public/{接口名}` 调用同名 AKShare 接口并返回 JSON |
| `aktools/cli.py` | `python -m aktools` 的命令行入口（Typer） |
| `aktools/datasets.py` | 读取随包发布的 HTML 模板、图标等资源 |
| `aktools/_version.py` | 版本号的唯一来源 |
| `tests/` | 单元测试 |
| `docs/`、`mkdocs.yml` | 文档源文件与站点配置，由 Zensical 构建并发布到 Read the Docs |

<!-- omit in toc -->
### 测试与代码检查

提交 Pull Request 前，请确认以下命令在本地全部通过，它们与 CI 执行的检查完全一致：

```bash
uv run pytest                  # 运行单元测试
uv run ruff format --check .   # 代码格式检查
uv run ruff check .            # 静态检查
```

可以用 `uv run ruff format . && uv run ruff check . --fix` 自动修复格式问题。

编写测试时请注意：

- 单元测试**不能依赖网络**。需要调用 AKShare 接口或访问 PyPI 的地方（如渲染主页时调用的 `get_latest_version()`）请用 mock 替换。
- 修复 Bug 时，请尽量补充一个能复现该 Bug 的测试。

<!-- omit in toc -->
### 修改依赖

修改 `pyproject.toml` 中的依赖后，请运行 `uv lock` 并一起提交更新后的 `uv.lock`；锁文件过期时 CI 会失败。

`uv.lock` 必须基于官方 PyPI 解析。`pyproject.toml` 已经声明了官方源，即使您本地配置了国内镜像，生成的锁文件也会指向官方源；如果在 diff 中看到镜像域名，请重新运行 `uv lock`。

<!-- omit in toc -->
### 提交 Pull Request

1. 从 `main` 新建一个分支，例如 `fix/xxx` 或 `feat/xxx`。
2. 每个 Pull Request 只做一件事，避免把无关的改动混在一起。
3. Pull Request 请提交到 `main` 分支，并在描述中说明改动内容和原因；如果关联了 Issue，请写上 `Closes #编号`。
4. 等待 CI 通过和维护者审查。如果需要修改，直接在原分支上追加提交即可。

## 改进文档

文档分为两部分：

- `README.md`：GitHub 首页和 PyPI 项目页的说明。PyPI 不支持相对链接，因此文中指向仓库文件的链接请使用完整的 GitHub 地址。
- `docs/`：[AKTools 中文文档](https://aktools.akfamily.xyz/) 的源文件，由 [Zensical](https://zensical.org/)（Material for MkDocs 的继任者）读取 `mkdocs.yml` 构建，合并到 `main` 后由 Read the Docs 自动发布。构建工具的版本由 `pyproject.toml` 的 `docs` 依赖组和 `uv.lock` 锁定。

本地预览与构建文档：

```bash
uv run --group docs zensical serve            # 实时预览，然后打开 http://localhost:8000
uv run --group docs zensical build --strict   # 与 Read the Docs 相同的构建命令，有警告即失败
```

编写文档时请注意：

- 段落中不要为了排版手动换行。中文之间的换行会被渲染成空格，一个段落请写在同一行。
- 会被其他页面或 README 引用的标题，请用 `{#英文锚点}` 显式指定锚点，例如 `## 接口返回 404 {#faq-404}`，不要依赖自动生成的 `#_14` 这类锚点。
- 页面按新手的学习顺序组织：首页 → 快速入门（`getting-started.md`）→ 使用指南（`guide/`）→ 部署 → 常见问题。新内容请放进对应的页面，不要重新堆到一个长页面里。

错别字、过时的说明、失效的链接、缺少的示例，都欢迎直接提交 Pull Request 修正。

## 提交信息规范

提交信息遵循 [Conventional Commits](https://www.conventionalcommits.org/zh-hans/) 规范，格式为 `<类型>: <描述>`，描述可以使用中文。`pre-commit install` 安装的 `commit-msg` 钩子会自动检查格式。

| 类型 | 用途 | 示例 |
| --- | --- | --- |
| `feat` | 新功能 | `feat: 区分上游数据源不可达错误` |
| `fix` | 修复 Bug | `fix: 修复主页模板渲染错误` |
| `docs` | 只改动文档 | `docs: 更新 Docker 部署说明` |
| `refactor` | 不改变行为的代码重构 | `refactor: 优化内置 HTML 页面` |
| `test` | 新增或修改测试 | `test: 补充 CLI 参数测试` |
| `chore` | 构建、依赖、版本号等杂项 | `chore: 版本号更新为 0.0.95` |
| `ci` | CI 配置 | `ci: 升级 setup-uv` |

## 发布流程（维护者）

发布时以下三处的版本号必须一致，发布工作流中的 `scripts/check_release.py` 会自动校验：

1. Git 标签 `vX.Y.Z`
2. `aktools/_version.py` 中的 `__version__`
3. `docs/aktools_version.md` 中的 `X.Y.Z: ...` 条目

推送 `vX.Y.Z` 标签后，`release_and_deploy.yml` 会依次完成校验、构建、检查构建产物、上传 PyPI 并创建 GitHub Release。

## 法律声明

向本项目提交贡献，即表示您确认所提交的内容由您本人创作，您拥有提交这些内容所需的权利，并同意这些内容以本项目的 [MIT 许可证](https://github.com/akfamily/aktools/blob/main/LICENSE) 发布。

<!-- omit in toc -->
## 致谢

本指南的结构参考了 [contributing-gen](https://github.com/bttger/contributing-gen)。
