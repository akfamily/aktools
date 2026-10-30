# -*- coding:utf-8 -*-
# !/usr/bin/env python
"""
Date: 2026/10/30 12:00
Desc: 日志：按天轮转的日志文件
日志目录由环境变量 AKTOOLS_LOG_DIR 指定；测试据此把日志写到临时目录，避免在仓库中留下日志文件
"""

import logging
import os
import tempfile
from logging.handlers import TimedRotatingFileHandler


def _create_log_handler(filename: str) -> TimedRotatingFileHandler:
    """
    按天轮转的日志文件，保留最近 7 天
    AI 助手以 stdio 方式启动 aktools-mcp 时，工作目录可能不可写（如 macOS 上的 /），
    此时改写到系统临时目录，避免服务因无法创建日志文件而启动失败
    :param filename: 日志文件路径
    :type filename: str
    :return: 日志处理器
    :rtype: TimedRotatingFileHandler
    """
    options = {"when": "midnight", "interval": 1, "backupCount": 7, "encoding": "utf-8"}
    try:
        return TimedRotatingFileHandler(filename=filename, **options)
    except OSError:
        fallback = os.path.join(tempfile.gettempdir(), os.path.basename(filename))
        return TimedRotatingFileHandler(filename=fallback, **options)


LOG_DIR_ENV = "AKTOOLS_LOG_DIR"
LOG_FILENAME = "aktools_log.log"


def _log_path() -> str:
    """
    日志文件路径：优先使用 AKTOOLS_LOG_DIR 指定的目录；
    Vercel 环境只有 /tmp 可写；其余情况写到当前工作目录
    :return: 日志文件路径
    :rtype: str
    """
    log_dir = os.getenv(LOG_DIR_ENV)
    if log_dir:
        return os.path.join(log_dir, LOG_FILENAME)
    if os.getenv("VERCEL") == "1":
        return os.path.join("/tmp", LOG_FILENAME)
    return LOG_FILENAME


logger = logging.getLogger("AKToolsLog")
logger.setLevel(logging.INFO)
handler = _create_log_handler(_log_path())
handler.setFormatter(
    logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
)
logger.addHandler(handler)
