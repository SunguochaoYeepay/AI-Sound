@echo off
echo === 修复MegaTTS3容器内服务 ===

echo.
echo 1. 检查容器内进程...
docker exec megatts3-api ps aux

echo.
echo 2. 检查Flask应用日志...
docker exec megatts3-api ls -la /app/logs/

echo.
echo 3. 重启Flask应用...
docker exec megatts3-api pkill -f api_server.py
timeout /t 2 >nul
docker exec -d megatts3-api python /app/api_server.py

echo.
echo 4. 等待服务启动...
timeout /t 10 >nul

echo.
echo 5. 测试服务响应...
curl -X GET "http://localhost:7929/health"

echo.
echo === 修复完成 ===
pause 