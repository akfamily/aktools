---
name: AKTools 问题报告
about: 反馈 AKTools 的 HTTP API 相关问题
title: AKTools 问题报告
labels: bug
assignees: ''

---

> 本 issue 只接受 AKTools 自身的问题。如果是某个数据接口返回的数据有误或接口报错，
> 请先确认该接口在 AKShare 中直接调用是否正常；若 AKShare 侧即有问题，请到
> AKShare 仓库反馈：https://github.com/akfamily/akshare/issues

## 重要前提

遇到问题请先将本地的 AKShare 与 AKTools 都升级到**最新版**：

```bash
pip install akshare aktools --upgrade  # Python 版本需要大于等于 3.11
```

## 如何提交问题

请提交以下信息，以便更精准地定位问题。**不符合提交规范的 issue 会被关闭！**

1. 操作系统及版本（目前只支持 64 位主流操作系统）
2. Python 版本（目前只支持 3.11 及以上）
3. AKShare 与 AKTools 的版本，可访问 `http://127.0.0.1:8080/version` 获取
4. 启动 AKTools 的命令，以及访问的完整 URL（接口名与参数）
5. 完整的报错信息或异常堆栈（请粘贴文本，不要仅截图）
6. 如与特定依赖版本有关，请附上 `pip list` 中 fastapi、uvicorn、starlette 的版本
