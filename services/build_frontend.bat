@echo off
echo 正在构建前端服务...
docker-compose build web-admin --no-cache
echo 构建完成，正在启动服务...
docker-compose up -d web-admin
echo 前端服务已启动，请等待15秒后刷新页面
pause 