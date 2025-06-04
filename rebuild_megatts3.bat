@echo off
echo === 重建MegaTTS3容器 ===
echo ⚠️  警告：这将停止并重新创建容器

echo.
set /p confirm="确定要重建容器吗？(y/N): "
if /i not "%confirm%"=="y" (
    echo 取消操作
    pause
    exit /b
)

echo.
echo 1. 停止当前容器...
docker stop megatts3-api

echo.
echo 2. 删除容器...
docker rm megatts3-api

echo.
echo 3. 查找MegaTTS3镜像...
docker images | findstr megatts3

echo.
echo 4. 重新创建容器...
docker run -d --name megatts3-api -p 7929:7929 -p 7930:7930 --gpus all megatts3:latest

echo.
echo 5. 等待容器启动...
timeout /t 15 >nul

echo.
echo 6. 检查容器状态...
docker ps | findstr megatts3-api

echo.
echo 7. 测试服务...
curl -X GET "http://localhost:7929/health"

echo.
echo === 重建完成 ===
pause 