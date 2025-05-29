@echo off
echo ========================================
echo    AI-Sound 开发模式启动脚本
echo ========================================
echo.

echo [INFO] 启动开发模式服务...
echo [INFO] 特性: 代码热重载、实时调试
echo.

REM 启动开发模式
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up --build

echo.
echo [INFO] 开发模式已启动
echo [INFO] API服务: http://localhost:9930
echo [INFO] 前端服务: http://localhost:5173
echo [INFO] 修改代码后会自动重载，无需重新构建
echo.
pause 