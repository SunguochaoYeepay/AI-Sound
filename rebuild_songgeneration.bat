@echo off
echo 强制重建SongGeneration容器...

echo 1. 停止容器...
docker container stop ai-sound-songgeneration

echo 2. 删除容器...
docker container rm ai-sound-songgeneration

echo 3. 删除旧镜像...
docker image rm ai-sound-songgeneration

echo 4. 重新构建...
docker-compose build songgeneration

echo 5. 启动新容器...
docker-compose up songgeneration -d

echo 完成！检查状态：
docker-compose ps songgeneration

pause 