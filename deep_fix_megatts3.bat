@echo off
echo === 深度修复MegaTTS3服务 ===

echo.
echo 1. 检查Python环境...
docker exec megatts3-api python --version
docker exec megatts3-api which python

echo.
echo 2. 检查应用文件...
docker exec megatts3-api ls -la /app/
docker exec megatts3-api ls -la /app/api_server.py

echo.
echo 3. 检查工作目录...
docker exec megatts3-api pwd
docker exec megatts3-api ls -la

echo.
echo 4. 尝试手动启动Flask应用（查看错误）...
echo 如果有错误会在这里显示：
docker exec megatts3-api python /app/api_server.py &
timeout /t 5 >nul

echo.
echo 5. 再次检查进程...
docker exec megatts3-api ps aux | findstr python

echo.
echo 6. 测试端口绑定...
docker exec megatts3-api netstat -tulpn | findstr 7929

echo.
echo 7. 最终测试...
curl -X GET "http://localhost:7929/health"

echo.
echo === 深度修复完成 ===
pause 