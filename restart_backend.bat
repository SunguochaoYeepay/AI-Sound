@echo off
echo 正在重启backend容器以应用7929端口修复...
echo.

echo 1. 停止backend容器...
docker stop ai-sound-backend

echo 2. 删除旧容器...
docker rm ai-sound-backend

echo 3. 重新构建并启动backend...
docker compose -f docker-compose.prod.yml up -d --build backend

echo 4. 等待容器启动...
timeout /t 10

echo 5. 检查容器状态...
docker ps | findstr ai-sound-backend

echo.
echo 重启完成！现在测试语音合成功能。
pause 