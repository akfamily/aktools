# 版本说明

本页记录 [AKTools](https://github.com/akfamily/aktools) 每个版本的主要变更，最新版本在最前。升级到最新版：

```shell
pip install aktools --upgrade -i https://pypi.org/simple
```

AKTools 只负责把 HTTP 请求转发给 AKShare，数据接口的新增与变更请查看 [AKShare 版本更新说明](https://akshare.akfamily.xyz/changelog.html)。

## 更新记录

0.1.1: fix: homepage no longer blocks the server

**不兼容的改动：已移除 PyScript 数据展示页 `/api/show` 与 `/api/show-temp/{接口名}`。** 取数请使用 `/api/public/{接口名}`，表格可加 `_format=csv` 或 `_format=xlsx` 下载。

1. 修复主页与 /version 查询 PyPI 最新版本时阻塞整个服务的问题：内网或无法访问 PyPI 的环境中，此前每打开一次主页，其他请求（取数据、/mcp）都会卡住约 10 秒；最新版本的查询结果改为缓存 1 小时
2. Dockerfile 新增构建参数 BASE_IMAGE，国内网络可改用镜像站拉取基础镜像；文档说明可用 WEB_CONCURRENCY 调整 worker 数量
3. 常见问题补充国内 PyPI 镜像同步延迟时如何安装新版本
4. 内部重构：拆分 aktools/core/api.py；只改文档时 CI 不再运行测试

0.1.0: feat: proxy and timeout settings, clearer upstream errors

AKTools 已具备 HTTP API 与 MCP 两种完整的使用方式，自本版本起进入 0.1.x。

1. 新增 --proxy 与 --timeout（环境变量 AKTOOLS_PROXY、AKTOOLS_TIMEOUT），设置访问上游数据源的代理与读取超时，需要 AKShare 1.20.4 及以上版本
2. AKShare 自定义的异常返回对应的状态码：网络问题 502、上游限流 429、参数不合法 400、上游报错与页面改版 502，不再一律返回 404 并提示升级 AKShare；MCP 工具同样适用
3. 新增环境变量 AKTOOLS_LOG_DIR 指定日志目录
4. 修复跑测试时日志写进仓库目录的问题

0.0.99: feat: publish to the official mcp registry

1. 登记到 MCP 官方注册表（io.github.akfamily/aktools），各 MCP 客户端的市场可以搜到 AKTools；发布流程在 PyPI 发布后自动登记
2. 新增 aktools 命令（同 python -m aktools）与 aktools mcp 子命令（同 aktools-mcp）
3. README 与文档改为 HTTP API 与 MCP 两种使用方式并列，加入 Claude Code 实际使用演示、Cursor 一键安装按钮与 MCP 排障说明
4. 启动提示与内置主页显示 /mcp 地址；PyPI 简介与关键词补充 MCP

0.0.98: feat: add mcp server and result cache

1. 新增 MCP 服务，供 Claude、Cursor 等 AI 助手获取数据：随 HTTP 服务提供 /mcp，或在助手中配置 uvx --from aktools aktools-mcp 以 stdio 方式运行
2. 新增结果缓存：同一接口、同样参数在 60 秒内直接返回上次的数据，可用 --cache-ttl 调整，响应头 X-AKTools-Cache 标明是否命中
3. 定期清空 AKShare 内部缓存（默认每小时），修复服务长期运行后板块名称等数据不更新的问题，可用 --akshare-cache-clear 调整
4. 数据无法转换为所选格式时返回说明；日志目录不可写时改写到系统临时目录
5. 文档新增“什么情况下不必用 AKTools”、缓存设置与 AI 助手（MCP）的说明

0.0.97: docs: reorganize docs for beginners

1. 文档按新手学习顺序重组：首页、快速入门、使用指南（调用规则、接口目录、多语言调用）、部署、常见问题
2. 新增快速入门教程，从安装到查找接口、查看参数、获取数据并下载 Excel，示例均为实际运行结果
3. 首页与 README 补充接口目录、CSV/Excel 下载等新功能的说明，原“详细文档”页面已拆分
4. README 的文档状态徽章改用 shields.io，修复在 GitHub 上无法显示的问题

0.0.96: feat: add interface catalog and csv/xlsx export

1. 新增接口目录：/api/interfaces 列出全部接口并支持按接口名或中文标题搜索，/api/interfaces/{接口名} 返回各参数的默认值、类型和说明
2. /api/public 新增 _format 参数，可将数据下载为 CSV（带 BOM，Excel 直接打开不乱码）或 Excel 文件
3. 修复 /api/show 返回未渲染模板、无法加载数据的问题
4. PyScript 数据展示页升级到 2026.7.3，并改用国内可访问的 Pyodide 节点
5. 以 --host 0.0.0.0 启动时，命令行提示与 --auto 打开的地址改用 127.0.0.1，可直接在浏览器中打开
6. 文档站迁移到 Zensical，重写使用文档、贡献指南与行为准则，更新 PyPI 项目信息

0.0.95: feat: distinguish upstream network errors

1. 上游数据源不可达（网络/代理错误）时返回 502 并提示排查，不再误导为升级 AKShare
2. 文档与主页的连通性测试链接改用更稳定的新浪接口
3. 文档新增常见问题：502/404 的区别与代理问题排查

0.0.94: refactor: optimize built-in HTML pages

1. 内置主页优化：语言标记、移动端适配、样式整理与深浅色配色
2. PyScript 数据展示页由已废弃的 alpha 版升级到当前稳定版
3. 同步文档描述，参照 AKShare 重写 .gitignore

0.0.93: refactor: remove demo user login

1. 删除演示性的用户登录模块（aktools/login）与 /api/private 私人接口
2. 移除 POST /auth/token 端点；数据获取统一使用 GET /api/public/{接口}

0.0.92: fix: fix template response and cli startup

1. 修复新版 Starlette 下主页与模板页面返回 500 的问题（#239）
2. 修复安装路径含空格时 aktools 启动闪退的问题（#238）
3. Python 版本要求提升到 3.11 及以上，与 AKShare 保持一致
4. 更新 Dockerfile，打包配置由 setup.py 迁移到 pyproject.toml
5. 删除未使用的数据库相关代码
