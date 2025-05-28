@echo off
REM 创建Docker网络，用于所有服务之间的通信
REM 如果网络已存在，则不会重新创建

echo 正在创建AI-Sound服务网络...
docker network create ai-sound-network || echo 网络已存在，无需创建

echo 网络创建完成。现在您可以启动各个服务了。
echo 启动顺序建议：
echo 1. 启动MegaTTS3服务：cd ..\MegaTTS3 ^&^& docker-compose up -d
echo 2. 启动ESPnet服务：cd ..\espnet ^&^& docker-compose up -d
echo 3. 启动API和Web服务：docker-compose up -d

pause