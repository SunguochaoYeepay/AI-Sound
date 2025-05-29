@echo off
echo 🔨 标准API构建脚本
echo ==========================================

echo 1️⃣ 构建API服务...
set DOCKER_BUILDKIT=1
docker-compose build api --no-cache

if %errorlevel% neq 0 (
    echo ❌ 构建失败！尝试使用国内镜像源...
    docker-compose build api --no-cache --build-arg PYTHON_MIRROR=https://pypi.tuna.tsinghua.edu.cn/simple
)

if %errorlevel% neq 0 (
    echo ❌ 仍然失败！尝试阿里云镜像源...
    docker-compose build api --no-cache --build-arg PYTHON_MIRROR=https://mirrors.aliyun.com/pypi/simple/
)

echo 2️⃣ 启动API服务...
docker-compose up -d api

echo 3️⃣ 等待服务启动...
timeout /t 15

echo 4️⃣ 检查服务状态...
docker-compose ps api

echo 5️⃣ 测试API健康检查...
python test_health_simple.py

echo ==========================================
echo ✅ API构建和测试完成！
pause 