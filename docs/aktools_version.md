# 版本说明

本页记录 [AKTools](https://github.com/akfamily/aktools) 每个版本的主要变更，最新版本在最前。升级到最新版：

```shell
pip install aktools --upgrade -i https://pypi.org/simple
```

AKTools 只负责把 HTTP 请求转发给 AKShare，数据接口的新增与变更请查看 [AKShare 版本更新说明](https://akshare.akfamily.xyz/changelog.html)。

## 更新记录

0.1.6: feat: curated alternatives, better search and clearer errors for MCP

1. 东方财富行情接口被限流时，建议的同类接口改为取自 AKShare 人工维护的对照表，不再按接口名称猜测；0.1.5 的猜测有不少配错，如把 ST 股票列表配给日线。describe_interface 与 /api/interfaces/{接口名} 新增 alternatives，取数前就能看到其他来源的同类接口。没有登记的接口不再给出候选
2. 搜索更准：随 AKShare 1.20.39 支持常用同义词，“港股 日线”“期货 日线”这类说法能直接找到日线行情接口；MCP 的 search_interfaces 没有匹配时返回提示，说明关键词应描述数据类型而不是证券名称
3. 接口名写错或使用已更名的旧接口名（如 get_futures_daily）时，报错中列出名称相近的接口，MCP 与 HTTP API 相同
4. 大连商品交易所接口被对方网站拒绝访问时，不再提示“请稍后重试”，改为说明重试无效并保留 AKShare 给出的替代接口
5. 更多数据来源显示中文名称，如集思录、上海黄金交易所、财联社
6. MCP 的 search_interfaces 工具描述中写明优先选用其他来源的规则，不依赖客户端是否向模型传递服务说明
7. AKShare 的最低版本要求提高到 1.20.39

0.1.5: feat: label data sources and suggest alternatives on Eastmoney rate limits

1. MCP 的 search_interfaces、describe_interface 与 /api/interfaces/{接口名} 新增 source，用中文标明数据来源，如“新浪财经”“同花顺”“东方财富”；describe 另有 rate_limit。东方财富行情类接口（实时行情、历史 K 线、板块、资金流等）标为“东方财富·行情（频繁访问易限流）”，与不限流的东方财富数据中心区分。限流标记需要 AKShare 1.20.37 及以上版本，旧版本只显示“东方财富”
2. 修复东方财富行情接口被限流时返回 502 并提示检查代理的问题，现在返回 429
3. 东方财富行情接口被限流时，报错说明需要等待的时间，并在有把握时列出其他来源的同类接口，如 stock_zh_a_hist 被限流时建议 stock_zh_a_hist_tx（腾讯）、stock_zh_a_daily（新浪财经）；MCP 与 HTTP API 相同
4. MCP 发给助手的使用说明要求：批量获取行情数据时优先选用其他来源，被限流时不要立即重试，回答时说明数据来源
5. 文档新增 WorkBuddy 与 Codex 的 MCP 配置方法，以及与 AKQuant 联用、由 AI 自动回测的说明

0.1.4: feat: better MCP search, paging and interface details

1. MCP 的 get_data 新增 offset：用于翻页，负数表示从末尾倒数，如 -20 取最后 20 行；此前只能取表头，按日期升序的数据最新的行取不到
2. MCP 的 search_interfaces 改为按相关度检索，支持“A股 日线”“期货持仓”等多个关键词，结果附带类目
3. describe_interface 与 /api/interfaces/{接口名} 补充返回列、数据范围说明与调用示例
4. MCP 的三个工具标注为只读
5. 文档站发布 llms.txt，向 AI 助手说明 AKTools 的接入方式

0.1.3: fix: clear errors for unknown parameters

1. 参数名写错时返回 400，并列出该接口的全部可用参数，不再返回 404 并提示升级 AKShare，也不会白白请求一次上游网站；MCP 的 get_data 同样适用
2. 最低依赖提升到 AKShare 1.20.13：页码等数字参数可以直接以文本传入，--timeout 对所有接口生效
3. AKShare 1.20.13 起各接口不再提供 timeout 参数，旧网址中的 timeout 会返回 400 并提示改用 --timeout

0.1.2: feat: optional access token

1. 新增可选的访问令牌（--token，环境变量 AKTOOLS_TOKEN）：设置后，数据接口与 /mcp 需要携带令牌，支持请求头 Authorization: Bearer <令牌> 或网址参数 _token=<令牌>，多个令牌用逗号分隔；主页、/version 与 /docs 保持公开；未设置时行为不变
2. 修复主页上的地址写死为 http:// 的问题：经反向代理以 HTTPS 访问时，主页显示的接口与 /mcp 地址改为与实际访问的协议、域名一致

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
