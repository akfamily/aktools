# AKTools：AKShare 的 HTTP API 服务镜像
# 构建：docker build -t aktools .
# 运行：docker run -d -p 8080:8080 aktools，然后访问 http://127.0.0.1:8080/docs
# 国内构建可指定镜像源：docker build --build-arg PIP_INDEX_URL=https://mirrors.aliyun.com/pypi/simple/ -t aktools .
FROM python:3.14-slim-trixie

ARG PIP_INDEX_URL=https://pypi.org/simple
# AKTOOLS_HOST：容器内监听 0.0.0.0，MCP 据此允许经端口映射或局域网地址访问 /mcp
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    TZ=Asia/Shanghai \
    AKTOOLS_HOST=0.0.0.0

RUN pip install --index-url "$PIP_INDEX_URL" --upgrade akshare "aktools[mcp]" gunicorn uvicorn-worker

# 以非 root 用户运行；AKTools 启动时会在工作目录写入 aktools_log.log，工作目录需可写，
# 因此使用该用户自己的家目录
RUN useradd --create-home --uid 1000 aktools
USER aktools
WORKDIR /home/aktools

EXPOSE 8080

# aktools.main:app 按包路径加载，不依赖 site-packages 的具体位置，升级 Python 版本无需修改
CMD ["gunicorn", "aktools.main:app", "--bind", "0.0.0.0:8080", "--worker-class", "uvicorn_worker.UvicornWorker"]
