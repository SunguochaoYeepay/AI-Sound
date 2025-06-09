@echo off
chcp 65001 >nul
echo 🚀 AI-Sound Backend 虚拟环境管理器
echo =========================================

if "%1"=="" set ACTION=create
if not "%1"=="" set ACTION=%1

if "%ACTION%"=="create" goto CREATE
if "%ACTION%"=="install" goto INSTALL  
if "%ACTION%"=="run" goto RUN
if "%ACTION%"=="clean" goto CLEAN
goto HELP

:CREATE
echo 🎯 创建虚拟环境...
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python未找到，请先安装Python 3.9-3.11
    echo 💡 下载地址: https://www.python.org/downloads/
    goto END
)

if exist venv (
    echo 🧹 清理现有虚拟环境...
    rmdir /s /q venv
)

echo 📦 创建虚拟环境...
python -m venv venv
if errorlevel 1 (
    echo ❌ 虚拟环境创建失败
    goto END
)

echo ✅ 虚拟环境创建成功
echo.
echo 📋 下一步: setup-venv.bat install
echo 💡 手动激活命令: venv\Scripts\activate.bat
goto END

:INSTALL
echo 🎯 安装依赖包...
if not exist venv\Scripts\activate.bat (
    echo ❌ 虚拟环境不存在，请先运行: setup-venv.bat create
    goto END
)

call venv\Scripts\activate.bat
echo 📦 升级pip...
python -m pip install --upgrade pip

echo 📦 安装基础依赖...
pip install wheel setuptools

echo 📦 安装后端开发依赖...
pip install -r requirements-dev.txt

if errorlevel 1 (
    echo ❌ 依赖安装失败
    goto END
)

echo ✅ 依赖安装完成
echo.
echo 📋 下一步: setup-venv.bat run
goto END

:RUN
echo 🎯 启动后端服务...
if not exist venv\Scripts\activate.bat (
    echo ❌ 虚拟环境不存在，请先运行完整设置
    goto END
)

call venv\Scripts\activate.bat
echo 🌐 虚拟环境已激活
echo 🚀 启动后端服务...
python main.py
goto END

:CLEAN
echo 🎯 清理虚拟环境...
if exist venv (
    rmdir /s /q venv
    echo ✅ 虚拟环境已清理
) else (
    echo ⚠️ 虚拟环境不存在
)
goto END

:HELP
echo 用法: setup-venv.bat [create^|install^|run^|clean]
echo.
echo   create  - 创建虚拟环境
echo   install - 安装依赖包
echo   run     - 启动后端服务
echo   clean   - 清理虚拟环境
echo.

:END
echo.
echo =========================================
echo 🎯 AI-Sound Backend 环境管理器完成 