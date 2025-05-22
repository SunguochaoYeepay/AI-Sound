FROM nvidia/cuda:12.1.0-cudnn8-runtime-ubuntu22.04

# 设置环境变量
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH="/app:/app/MegaTTS3:/app/src"

# 设置工作目录
WORKDIR /app

# 创建必要的目录
RUN mkdir -p /app/src /app/checkpoints /app/output /app/data

# 复制并安装依赖（这一层很少变化，利于缓存）
COPY services/api/requirements.txt /app/
RUN sed -i 's|http://archive.ubuntu.com/ubuntu/|https://mirrors.aliyun.com/ubuntu/|g' /etc/apt/sources.list && \
    sed -i 's|http://security.ubuntu.com/ubuntu/|https://mirrors.aliyun.com/ubuntu/|g' /etc/apt/sources.list && \
    apt-get update && apt-get install -y --no-install-recommends \
    python3 python3-pip python3-dev \
    ffmpeg libsndfile1 \
    portaudio19-dev \
    wget git \
    && rm -rf /var/lib/apt/lists/* \
    && pip3 install --no-cache-dir -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt

# 复制源代码 - 使用调整后的路径
COPY services/api/src/ /app/src/

# MegaTTS3目录将通过卷挂载方式提供，无需复制
# COPY MegaTTS3/ /app/MegaTTS3/

# 创建软链接，确保模块可以被正确导入
RUN ln -sf /app/MegaTTS3/tts /usr/local/lib/python3.*/dist-packages/ || true

# 暴露API端口
EXPOSE 9930

# 运行API服务
CMD ["python3", "-m", "src.main", "--host", "0.0.0.0", "--port", "9930"]