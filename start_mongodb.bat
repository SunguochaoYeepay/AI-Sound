@echo off
echo [启动] MongoDB 数据库服务...
echo.

cd /d "%~dp0"

echo 检查Docker是否运行...
docker info >nul 2>&1
if errorlevel 1 (
    echo [错误] Docker未运行，请先启动Docker Desktop
    pause
    exit /b 1
)

echo 创建网络（如果不存在）...
docker network create ai-sound-network 2>nul

echo 启动MongoDB服务...
cd services\infrastructure
docker-compose -f docker-compose.mongodb.yml up -d

if errorlevel 1 (
    echo [错误] MongoDB启动失败
    pause
    exit /b 1
)

echo.
echo [成功] MongoDB已启动
echo 数据库地址: localhost:27017
echo 管理员账号: admin / admin123
echo 应用数据库: ai_sound
echo.
echo 检查服务状态...
docker-compose -f docker-compose.mongodb.yml ps

pause 