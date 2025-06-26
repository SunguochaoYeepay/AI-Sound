@echo off
echo [DEV-MODE] 启动AI-Sound开发环境...

REM 检查Docker是否运行
docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Docker未运行，请先启动Docker Desktop
    pause
    exit /b 1
)

REM 使用开发配置启动服务
echo [DEV-MODE] 使用开发配置启动服务...
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d

REM 等待服务启动
echo [DEV-MODE] 等待服务启动...
timeout /t 10 /nobreak >nul

REM 检查服务状态
echo [DEV-MODE] 检查服务状态...
docker-compose ps

echo [DEV-MODE] 服务启动完成！
echo [INFO] 前端地址: http://localhost:3001
echo [INFO] 后端API: http://localhost:3001/api
echo [INFO] 后端健康检查: http://localhost:3001/health
echo [INFO] 查看后端日志: docker logs ai-sound-backend -f
pause 