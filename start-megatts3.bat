@echo off
chcp 65001 >nul
echo ========================================
echo    MegaTTS3 语音合成服务启动脚本
echo ========================================
echo.

:: 检查虚拟环境是否存在
if not exist "MegaTTS\espnet\espnet_env" (
    echo ❌ 错误：虚拟环境不存在！
    echo 请先创建虚拟环境：python -m venv MegaTTS\espnet\espnet_env
    pause
    exit /b 1
)

:: 切换到MegaTTS3目录
cd /d "%~dp0MegaTTS\espnet"

:: 激活虚拟环境
echo 🔄 激活虚拟环境...
call espnet_env\Scripts\activate.bat

:: 检查激活是否成功
if errorlevel 1 (
    echo ❌ 虚拟环境激活失败！
    pause
    exit /b 1
)

:: 检查Python和依赖
echo 🔍 检查Python环境...
python --version
if errorlevel 1 (
    echo ❌ Python未找到！
    pause
    exit /b 1
)

:: 检查必要文件
if not exist "start_megatts3.py" (
    echo ❌ 找不到 start_megatts3.py！
    pause
    exit /b 1
)

:: 启动服务
echo.
echo 🚀 启动MegaTTS3 API服务...
echo 📍 服务地址：http://127.0.0.1:7929
echo 📍 API文档：http://127.0.0.1:7929/docs
echo.
echo 按 Ctrl+C 停止服务
echo ========================================
echo.

python start_megatts3.py

:: 如果服务异常退出
echo.
echo ❌ 服务已停止
pause
