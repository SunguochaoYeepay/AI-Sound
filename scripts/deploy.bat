@echo off
REM AI-Sound Windows 自动化部署脚本
REM 用途：一键部署生产环境

setlocal enabledelayedexpansion

echo ==================================
echo 🎵 AI-Sound 自动化部署脚本
echo ==================================
echo.

REM 颜色定义 (Windows限制，使用简单标识)
set "INFO=[INFO]"
set "SUCCESS=[SUCCESS]"
set "WARNING=[WARNING]"
set "ERROR=[ERROR]"

REM 检查必要的命令
echo %INFO% 检查系统要求...

REM 检查Docker
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo %ERROR% Docker 未安装，请先安装Docker Desktop
    pause
    exit /b 1
)

REM 检查Docker Compose
docker-compose --version >nul 2>&1
if %errorlevel% neq 0 (
    echo %ERROR% Docker Compose 未安装，请先安装Docker Compose
    pause
    exit /b 1
)

REM 检查Node.js
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo %ERROR% Node.js 未安装，请先安装Node.js 18+
    pause
    exit /b 1
)

echo %SUCCESS% 系统要求检查通过

REM 创建必要的目录
echo %INFO% 创建数据目录...
if not exist "data" mkdir data
if not exist "data\audio" mkdir data\audio
if not exist "data\database" mkdir data\database
if not exist "data\logs" mkdir data\logs
if not exist "data\logs\nginx" mkdir data\logs\nginx
if not exist "data\logs\backend" mkdir data\logs\backend
if not exist "data\uploads" mkdir data\uploads
if not exist "data\voice_profiles" mkdir data\voice_profiles
if not exist "data\cache" mkdir data\cache
if not exist "data\config" mkdir data\config
if not exist "data\backups" mkdir data\backups
if not exist "data\temp" mkdir data\temp
if not exist "nginx-dist" mkdir nginx-dist

echo %SUCCESS% 目录创建完成

REM 构建前端
echo %INFO% 构建前端应用...
cd platform\frontend

REM 安装依赖
if not exist "node_modules" (
    echo %INFO% 安装前端依赖...
    call npm install
    if %errorlevel% neq 0 (
        echo %ERROR% 前端依赖安装失败
        pause
        exit /b 1
    )
)

REM 构建应用
echo %INFO% 构建前端资源...
call npm run build
if %errorlevel% neq 0 (
    echo %ERROR% 前端构建失败
    pause
    exit /b 1
)

REM 复制构建结果
echo %INFO% 复制构建结果...
xcopy /E /Y dist\* ..\..\nginx-dist\
cd ..\..

echo %SUCCESS% 前端构建完成

REM 启动服务
echo %INFO% 启动Docker服务...

REM 停止现有服务
docker-compose down >nul 2>&1

REM 启动新服务
docker-compose up -d
if %errorlevel% neq 0 (
    echo %ERROR% 服务启动失败
    pause
    exit /b 1
)

echo %SUCCESS% 服务启动完成

REM 健康检查
echo %INFO% 执行健康检查...

REM 等待服务启动
echo %INFO% 等待服务启动...
timeout /t 30 /nobreak >nul

REM 检查容器状态
echo %INFO% 检查容器状态...
docker-compose ps

REM 检查API健康状态
echo %INFO% 检查API服务...
set max_attempts=10
set attempt=1

:health_check_loop
curl -f http://localhost:3001/health >nul 2>&1
if %errorlevel% equ 0 (
    echo %SUCCESS% API服务健康检查通过
    goto health_check_success
)

echo %WARNING% API服务尚未就绪，等待中... (!attempt!/!max_attempts!)
timeout /t 10 /nobreak >nul

set /a attempt+=1
if !attempt! leq !max_attempts! goto health_check_loop

echo %ERROR% API服务健康检查失败
docker-compose logs --tail=50 backend
pause
exit /b 1

:health_check_success
echo %SUCCESS% 所有服务运行正常

REM 显示访问信息
echo.
echo %INFO% 部署完成！访问信息：
echo.
echo 🌐 前端界面:    http://localhost:3001
echo 📡 API接口:     http://localhost:3001/api
echo 📚 API文档:     http://localhost:3001/docs
echo 💊 健康检查:    http://localhost:3001/health
echo.
echo 📋 管理命令:
echo   查看日志:     docker-compose logs -f
echo   重启服务:     docker-compose restart
echo   停止服务:     docker-compose down
echo.

echo %SUCCESS% 部署成功完成！
pause 