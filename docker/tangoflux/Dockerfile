# TangoFlux 独立环境音生成服务
FROM python:3.10-slim

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    DEBIAN_FRONTEND=noninteractive

# 配置清华大学镜像源并安装依赖
RUN echo "deb http://mirrors.tuna.tsinghua.edu.cn/debian/ bookworm main contrib non-free" > /etc/apt/sources.list && \
    echo "deb http://mirrors.tuna.tsinghua.edu.cn/debian/ bookworm-updates main contrib non-free" >> /etc/apt/sources.list && \
    echo "deb http://mirrors.tuna.tsinghua.edu.cn/debian-security bookworm-security main contrib non-free" >> /etc/apt/sources.list && \
    apt-get update && \
    apt-get install -y --no-install-recommends \
    curl \
    git \
    build-essential \
    ca-certificates \
    && apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# 复制TangoFlux源码
COPY MegaTTS/TangoFlux/ ./

# 创建模型目录并复制本地模型
RUN mkdir -p /app/models/tangoflux /app/models/text_encoders
COPY MegaTTS/TangoFlux/models/tangoflux/ /app/models/tangoflux/

# 安装TangoFlux依赖
RUN pip config set global.index-url https://mirrors.aliyun.com/pypi/simple/ && \
    pip config set global.trusted-host mirrors.aliyun.com && \
    pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -e . && \
    pip install --no-cache-dir flask flask-cors

# 创建数据目录
RUN mkdir -p /app/data/environment_sounds

# 暴露端口
EXPOSE 7930

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:7930/health || exit 1

# 启动TangoFlux API服务
CMD ["python", "tangoflux_api_server.py", "--host", "0.0.0.0", "--port", "7930"] 