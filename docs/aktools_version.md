## [AKTools](https://github.com/akfamily/aktools) 版本说明

### 开发目标

1. 提供 AKShare 的 HTTP API
2. 提供多线程访问功能
3. 增加接口状态码支持
4. 增加接口用户认证
5. 增加用户自定义数据接口功能

### 开发进展

0.0.43: add: add support response status code

    1. 增加用户认证模块，但是该程序目前并没有采用数据库，还是在测试中
    2. 目前用户可以通过 username 为 `akshare` 和 password 为 `akfamily` 来获取 token
    3. 通过在请求头中设置 token 参数来访问接口
