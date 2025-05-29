@echo off
echo [启动] API 后端服务...
echo.

cd /d "%~dp0"

echo 检查Docker是否运行...
docker info >nul 2>&1
if errorlevel 1 (
    echo [错误] Docker未运行，请先启动Docker Desktop
    pause
    exit /b 1
)

echo 检查MongoDB是否运行...
docker ps --filter "name=ai-sound-mongodb" --filter "status=running" -q | findstr . >nul
if errorlevel 1 (
    echo [警告] MongoDB未运行，建议先启动: start_mongodb.bat
    echo 继续启动API服务...
    echo.
)

echo 确保网络存在...
docker network create ai-sound-network 2>nul

echo 构建并启动API服务...
cd services
docker-compose -f docker-compose.core.yml up --build -d api

if errorlevel 1 (
    echo [错误] API服务启动失败
    pause
    exit /b 1
)

echo.
echo [成功] API服务已启动
echo 服务地址: http://localhost:9930
echo 健康检查: http://localhost:9930/health
echo.
echo 检查服务状态...
docker-compose -f docker-compose.core.yml ps api

echo.
echo 查看服务日志（按Ctrl+C退出）...
timeout /t 3 >nul
docker-compose -f docker-compose.core.yml logs -f api 