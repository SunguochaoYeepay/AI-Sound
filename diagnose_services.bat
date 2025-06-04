@echo off
echo === 诊断服务状态 ===

echo.
echo 1. 检查Docker容器状态...
docker ps -a | findstr megatts3
echo Docker容器检查完成

echo.
echo 2. 检查端口占用情况...
netstat -ano | findstr :7929
echo 7929端口检查完成

netstat -ano | findstr :8000
echo 8000端口检查完成

echo.
echo 3. 尝试重启MegaTTS3容器...
docker restart megatts3-api
if %errorlevel% neq 0 (
    echo ❌ 容器重启失败
) else (
    echo ✅ 容器重启成功，等待服务启动...
    timeout /t 10 >nul
)

echo.
echo 4. 测试MegaTTS3服务...
curl -X GET "http://localhost:7929/health" 2>nul
if %errorlevel% neq 0 (
    echo ❌ MegaTTS3服务仍未响应
) else (
    echo ✅ MegaTTS3服务已恢复
)

echo.
echo === 诊断完成 ===
pause 