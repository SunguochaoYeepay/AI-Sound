@echo off
echo 🚀 启动 AI-Sound Platform Backend...

REM 进入后端目录
cd /d "%~dp0\..\backend"

REM 检查虚拟环境
if not exist "venv" (
    echo 📦 创建 Python 虚拟环境...
    python -m venv venv
)

REM 激活虚拟环境
call venv\Scripts\activate.bat

REM 安装依赖
echo 📥 安装依赖...
pip install -r requirements.txt

REM 进入应用目录
cd app

REM 启动服务
echo ✅ 启动 FastAPI 服务 (端口 8000)...
echo 🌐 API文档: http://localhost:8000/docs
echo 🔍 健康检查: http://localhost:8000/health
echo.
echo 按 Ctrl+C 停止服务
echo.

python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload

pause 