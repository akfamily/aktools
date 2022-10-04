# -*- coding:utf-8 -*-
# !/usr/bin/env python
"""
Date: 2022/9/8 15:20
Desc: 数据库配置
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from msscore.config import get_local_settings

local_settings = get_local_settings()

MYSQL_DB = local_settings.mysql_db  # MySQL 数据库名称
MYSQL_USER = local_settings.mysql_user  # MySQL 数据库登录帐号
MYSQL_PASSWD = local_settings.mysql_passwd  # MySQL 数据库登陆密码，由于格式化路径的问题，请勿使用 `@` 符号
MYSQL_HOST = local_settings.mysql_host  # MySQL 数据库地址，此处需要替换为服务器的地址
MYSQL_PORT = local_settings.mysql_port  # MySQL 端口
SQLALCHEMY_DATABASE_URL = f"mysql://{MYSQL_USER}:{MYSQL_PASSWD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DB}?charset=utf8mb4"
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
