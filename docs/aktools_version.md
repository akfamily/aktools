## [AKTools](https://github.com/akfamily/aktools) 版本说明

## 开发目标

1. 提供 AKShare 的 HTTP API 核心功能
2. 提供多线程访问功能
3. 增加接口状态码支持
4. 增加接口用户认证
5. 增加用户自定义数据接口功能
6. 增加主页及增强命令行支持
7. 增加测试支持
8. 增加 SQLite 数据库支持

## 开发进度

0.0.86: add: add log function

0.0.85: fix: update python version

0.0.84: fix: fix homepage url

0.0.83: fix: fix Dockerfile

0.0.82: fix: fix connection.py

0.0.81: add: add support for Python 3.11

0.0.80: fix: fix uvicorn run command

0.0.79: fix: fix typos in homepage.html

0.0.78: add: add test_cli.py

    1. 增加测试文件，增加项目的稳健型

0.0.77: add: add cli.py file

0.0.76: fix: fix rename master to main

0.0.75: add: add version interface

0.0.74: add: add typer for CLI

0.0.73: fix: fix tips

0.0.72: add: add type hint for CLI

0.0.71: add: add more info to homepage

0.0.70: add: add homepage

    1. 增加首页，提供更多帮助信息

0.0.69: fix: fix file path in datasets.py

0.0.68: fix: fix cookie in parameter

0.0.67: fix: fix parameter with blank character

0.0.66: fix: fix setup.py

0.0.65: fix: fix favicon.ico path

0.0.64: fix: fix favicon.ico path

0.0.63: fix: fix favicon.ico path

0.0.62: add: add favicon.ico

0.0.61: fix: fix remove dependency from akscript.html

    1. 从 akscript.html 中移除 numpy 和 matplotlib 依赖

0.0.60: add: add css and html to akscript.py

0.0.59: add: add templates

0.0.58: add: add jinja2 to setup.py

0.0.57: fix: fix setup.py

0.0.56: add: add init.py

0.0.55: add: add datasets.py

0.0.54: fix: fix PyScript demo url

0.0.53: fix: fix PyScript demo url

    1. 修复 PyScript demo url 

0.0.52: add: add pyscript support
    
    1. 新增 PyScript Demo 演示

0.0.51: add: add CORS support

    1. 新增跨域的支持

0.0.50: add: add interface docs

    1. 给接口增加描述和简要说明
    2. 修正部分函数的签名

0.0.49: add: add FastAPI docs introduction

    1. 提供文档的标题、描述及版本
    2. 文档的版本与 AKShare 的版本对应，方便查询相关接口

0.0.48: fix: fix docs

    1. 修正 URL 连接
    2. 修正部分表述错误

0.0.47: add: add tips
    
    1. 移除路径输出
    2. 在终端窗口输出：`http://127.0.0.1:8080/docs` 类似的链接，用户可以一键直达接口文档

0.0.46: fix: fix setup.py

    1. 在 setup.py 中增加 `python-multipart` 的依赖

0.0.45: add: add module format support
    
    1. 把核心 API 模块和登录模块拆分开
    2. 把项目结构化，有利于后续开发
    3. 增加 run.py 文件作为项目的主入口

0.0.44: add: add support response status code

    1. 增加用户认证模块，但是该程序目前并没有采用数据库，还是在测试中
    2. 目前用户可以通过 username 为 `akshare` 和 password 为 `akfamily` 来获取 token
    3. 通过在请求头中设置 token 参数来访问接口

0.0.43: add: add support response status code
    
    1. 增加返回状态码，用户可以通过状态码来判断是否获取到数据
    2. 修正一些表述错处