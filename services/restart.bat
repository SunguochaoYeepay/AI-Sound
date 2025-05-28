@echo off
echo 重启API服务以应用新的ESPnet配置...

echo 停止API容器...
docker stop services-api-1

echo 等待3秒...
timeout /t 3 /nobreak > nul

echo 启动API容器...
docker start services-api-1

echo 等待10秒让服务启动...
timeout /t 10 /nobreak > nul

echo 测试API服务状态...
curl -s http://localhost:9930/health

echo.
echo 重启完成！ 