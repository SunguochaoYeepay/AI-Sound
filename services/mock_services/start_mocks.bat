@echo off
REM 启动模拟服务

echo 创建网络（如果不存在）
docker network create ai-sound-network || echo 网络已存在

echo 构建并启动模拟服务...
docker-compose build
docker-compose up -d

echo 模拟服务已启动：
echo MegaTTS3: http://localhost:9931
echo ESPnet: http://localhost:9932

pause