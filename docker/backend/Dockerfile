# AI-Sound 后端服务 (终极版本 - 彻底解决构建问题)
FROM python:3.10-slim

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 复制requirements文件并安装Python依赖
COPY platform/backend/requirements.txt ./requirements.txt
RUN pip config set global.index-url https://mirrors.aliyun.com/pypi/simple/ && \
    pip config set global.trusted-host mirrors.aliyun.com && \
    pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 复制应用代码 (确保获取最新代码)
COPY platform/backend/app/ ./app/

# 修正路径问题
RUN find ./app -name "*.py" -exec sed -i "s|'../data/|'/app/data/|g" {} \; && \
    find ./app -name "*.py" -exec sed -i 's|"../data/|"/app/data/|g' {} \;

# 创建必要的目录
RUN mkdir -p /app/data/audio \
             /app/data/uploads \
             /app/data/voice_profiles \
             /app/data/projects \
             /app/data/database \
             /app/data/logs \
             /app/data/config \
             /app/data/backups

# 暴露端口
EXPOSE 8000

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# 启动应用 - 保持工作目录在 /app
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]