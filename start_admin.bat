@echo off
echo [启动] Admin 前端管理界面...
echo.

cd /d "%~dp0"

echo 检查Docker是否运行...
docker info >nul 2>&1
if errorlevel 1 (
    echo [错误] Docker未运行，请先启动Docker Desktop
    pause
    exit /b 1
)

echo 检查API服务是否运行...
docker ps --filter "name=services-api" --filter "status=running" -q | findstr . >nul
if errorlevel 1 (
    echo [警告] API服务未运行，建议先启动: start_api.bat
    echo 继续启动Admin界面...
    echo.
)

echo 确保网络存在...
docker network create ai-sound-network 2>nul

echo 构建并启动Admin界面...
cd services
docker-compose -f docker-compose.core.yml up --build -d web-admin

if errorlevel 1 (
    echo [错误] Admin界面启动失败
    pause
    exit /b 1
)

echo.
echo [成功] Admin管理界面已启动
echo 访问地址: http://localhost:8080
echo API连接: http://localhost:9930
echo.
echo 检查服务状态...
docker-compose -f docker-compose.core.yml ps web-admin

echo.
echo 查看服务日志（按Ctrl+C退出）...
timeout /t 3 >nul
docker-compose -f docker-compose.core.yml logs -f web-admin 