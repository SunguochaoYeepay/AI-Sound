# 使用轻量级Python基础镜像
FROM python:3.11-slim

# 构建参数
ARG PYTHON_MIRROR=https://pypi.tuna.tsinghua.edu.cn/simple
ARG APT_MIRROR=mirrors.tuna.tsinghua.edu.cn

# 设置环境变量
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH="/app:/app/src" \
    PIP_INDEX_URL=${PYTHON_MIRROR} \
    PIP_TRUSTED_HOST=pypi.tuna.tsinghua.edu.cn

# 设置工作目录
WORKDIR /app

# 创建必要的目录
RUN mkdir -p /app/src /app/data /app/output

# 配置APT镜像源（可选）
RUN if [ -n "${APT_MIRROR}" ]; then \
        sed -i "s/deb.debian.org/${APT_MIRROR}/g" /etc/apt/sources.list.d/debian.sources || \
        sed -i "s/deb.debian.org/${APT_MIRROR}/g" /etc/apt/sources.list; \
    fi

# 安装系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libsndfile1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 复制并安装Python依赖
COPY services/api/requirements.txt /app/
RUN pip3 install --no-cache-dir --timeout=60 --retries=3 -r requirements.txt

# 复制源代码
COPY services/api/src/ /app/src/

# 创建非root用户
RUN useradd --create-home --shell /bin/bash app && \
    chown -R app:app /app
USER app

# 暴露API端口
EXPOSE 9930

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:9930/health || exit 1

# 运行API服务
CMD ["python3", "-m", "src.main", "--host", "0.0.0.0", "--port", "9930"]