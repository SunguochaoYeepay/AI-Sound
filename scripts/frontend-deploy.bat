@echo off
chcp 65001 >nul
setlocal

:: 检查参数
set MODE=%1
if "%MODE%"=="" set MODE=prod

echo ===========================================
echo   🚀 AI-Sound 前端自动构建部署脚本
echo   📦 模式: %MODE%
echo ===========================================
echo.

:: 检查当前目录
if not exist "docker-compose.yml" (
    echo ❌ 请在项目根目录运行此脚本！
    pause
    exit /b 1
)

echo [1/5] 🏗️  开始构建前端代码...
cd platform\frontend

:: 根据模式选择构建命令
if "%MODE%"=="dev" (
    echo 🔧 开发模式构建...
    call npm run build
) else (
    echo 🚀 生产模式构建...
    call npm run build
)

if %errorlevel% neq 0 (
    echo ❌ 前端构建失败！
    pause
    exit /b 1
)
echo ✅ 前端构建完成
echo.

echo [2/5] 🧹 清理nginx目录...
cd ..\..
if exist "nginx-dist\*" (
    powershell -Command "Remove-Item nginx-dist\* -Recurse -Force -ErrorAction SilentlyContinue"
)
if not exist "nginx-dist" mkdir nginx-dist
echo ✅ nginx目录清理完成
echo.

echo [3/5] 📂 拷贝构建文件到nginx目录...
powershell -Command "Copy-Item -Path platform\frontend\dist\* -Destination nginx-dist\ -Recurse -ErrorAction Stop"
if %errorlevel% neq 0 (
    echo ❌ 文件拷贝失败！
    pause
    exit /b 1
)
echo ✅ 文件拷贝完成
echo.

echo [4/5] 🔄 重启nginx容器...
docker-compose restart nginx
if %errorlevel% neq 0 (
    echo ❌ nginx重启失败！
    echo 💡 提示: 请检查Docker是否运行正常
    pause
    exit /b 1
)
echo ✅ nginx重启完成
echo.

echo [5/5] 🔍 等待nginx启动...
timeout /t 3 /nobreak >nul
echo ✅ nginx启动完成
echo.

echo ===========================================
echo   🎉 前端部署完成！
echo   📱 访问地址: http://localhost:3001
echo   💻 开发模式: %MODE%
echo ===========================================
echo.

echo 📊 容器状态检查:
docker-compose ps

echo.
echo 💡 使用方法:
echo   frontend-deploy.bat           ^(生产模式^)
echo   frontend-deploy.bat dev       ^(开发模式^)
echo   frontend-deploy.bat prod      ^(生产模式^)
echo.
pause 