# 基于CUDA的Python镜像
FROM nvidia/cuda:11.8-devel-ubuntu20.04

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONPATH=/app:/app/MegaTTS3
ENV PYTHONIOENCODING=utf-8

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-dev \
    git \
    curl \
    ffmpeg \
    libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

# 升级pip
RUN python3 -m pip install --upgrade pip

# 复制MegaTTS3的requirements.txt
COPY MegaTTS/MegaTTS3/requirements.txt /tmp/requirements.txt

# 安装Python依赖
RUN pip3 install -r /tmp/requirements.txt

# 安装额外的微服务依赖
RUN pip3 install \
    flask==2.3.3 \
    flask-cors==4.0.0 \
    gradio \
    requests

# 创建必要的目录
RUN mkdir -p /app/src/api /app/src/webui /app/logs /app/storage /app/models /app/config

# 设置权限
RUN chmod 755 /app

# 暴露端口
EXPOSE 8001 8002

# 默认命令
CMD ["/bin/bash"] 