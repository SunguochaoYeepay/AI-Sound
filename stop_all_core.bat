@echo off
echo ========================================
echo    AI-Sound 核心服务停止
echo ========================================
echo.

cd /d "%~dp0"

echo [1/2] 停止API和Admin服务...
echo ----------------------------------------
cd services
docker-compose -f docker-compose.core.yml down
echo [✓] API和Admin服务已停止

echo.
echo [2/2] 停止MongoDB数据库...
echo ----------------------------------------
cd infrastructure
docker-compose -f docker-compose.mongodb.yml down
echo [✓] MongoDB数据库已停止

echo.
echo ========================================
echo         所有服务已停止
echo ========================================
echo.
echo 注意: 数据已保留，下次启动会恢复
echo.
pause 