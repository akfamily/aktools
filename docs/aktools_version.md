## [AKTools](https://github.com/akfamily/aktools) 版本说明

### 开发目标

1. 提供 AKShare 的 HTTP API
2. 提供多线程访问功能
3. 增加接口状态码支持
4. 增加接口用户认证
5. 增加用户自定义数据接口功能

### 开发进度

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