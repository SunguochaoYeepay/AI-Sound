@echo off
echo ========================================
echo    AI-Sound 核心服务一键启动
echo ========================================
echo.

cd /d "%~dp0"

echo 检查Docker是否运行...
docker info >nul 2>&1
if errorlevel 1 (
    echo [错误] Docker未运行，请先启动Docker Desktop
    pause
    exit /b 1
)

echo.
echo [1/3] 启动MongoDB数据库...
echo ----------------------------------------
docker network create ai-sound-network 2>nul
cd services\infrastructure
docker-compose -f docker-compose.mongodb.yml up -d
if errorlevel 1 (
    echo [错误] MongoDB启动失败
    pause
    exit /b 1
)
echo [✓] MongoDB已启动 (localhost:27017)

echo.
echo [2/3] 启动API后端服务...
echo ----------------------------------------
cd ..\..
cd services
docker-compose -f docker-compose.core.yml up --build -d api
if errorlevel 1 (
    echo [错误] API服务启动失败
    pause
    exit /b 1
)
echo [✓] API服务已启动 (localhost:9930)

echo.
echo [3/3] 启动Admin管理界面...
echo ----------------------------------------
docker-compose -f docker-compose.core.yml up --build -d web-admin
if errorlevel 1 (
    echo [错误] Admin界面启动失败
    pause
    exit /b 1
)
echo [✓] Admin界面已启动 (localhost:8080)

echo.
echo ========================================
echo           启动完成！
echo ========================================
echo MongoDB:  http://localhost:27017
echo API:      http://localhost:9930
echo Admin:    http://localhost:8080
echo ========================================
echo.

echo 检查所有服务状态...
echo.
echo === MongoDB ===
cd infrastructure
docker-compose -f docker-compose.mongodb.yml ps
echo.
echo === API & Admin ===
cd ..
docker-compose -f docker-compose.core.yml ps

echo.
echo 按任意键退出...
pause >nul 