FROM python:3.10-slim-buster

RUN pip install --upgrade pip
RUN pip install --no-cache-dir akshare fastapi uvicorn -i http://mirrors.aliyun.com/pypi/simple/ --trusted-host=mirrors.aliyun.com  --upgrade
RUN pip install --no-cache-dir aktools -i https://pypi.org/simple --upgrade
