@echo off
echo [LOCAL-MODE] 启动AI-Sound本地开发环境...

REM 检查Python是否安装
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python未安装，请先安装Python 3.9+
    pause
    exit /b 1
)

REM 检查MySQL是否运行
echo [INFO] 检查MySQL服务状态...
netstat -an | findstr :3306 >nul 2>&1
if %errorlevel% neq 0 (
    echo [WARNING] MySQL服务未运行，请先启动MySQL服务
    echo [INFO] 可以使用以下命令启动MySQL:
    echo [INFO] net start mysql
    echo [INFO] 或者使用XAMPP/WAMP等集成环境
    pause
)

REM 检查Redis是否运行
echo [INFO] 检查Redis服务状态...
netstat -an | findstr :6379 >nul 2>&1
if %errorlevel% neq 0 (
    echo [WARNING] Redis服务未运行，尝试启动Redis...
    echo [INFO] 如果没有安装Redis，可以使用以下方式:
    echo [INFO] 1. 下载Redis for Windows: https://github.com/tporadowski/redis/releases
    echo [INFO] 2. 或者使用Docker: docker run -d -p 6379:6379 redis:7-alpine
    pause
)

REM 进入后端目录
cd platform\backend

REM 检查虚拟环境是否存在
if not exist "venv" (
    echo [INFO] 创建Python虚拟环境...
    python -m venv venv
)

REM 激活虚拟环境
echo [INFO] 激活虚拟环境...
call venv\Scripts\activate.bat

REM 安装MySQL版本依赖
echo [INFO] 安装MySQL版本依赖...
pip install -r requirements-mysql.txt

REM 设置环境变量
echo [INFO] 设置环境变量...
set DATABASE_URL=mysql+pymysql://ai_sound_user:ai_sound_password@localhost:3306/ai_sound?charset=utf8mb4
set MEGATTS3_URL=http://localhost:7929
set TANGOFLUX_URL=http://localhost:7930
set SONGGENERATION_URL=http://localhost:7862
set OLLAMA_URL=http://localhost:11434
set AUDIO_DIR=./data/audio
set UPLOADS_DIR=./data/uploads
set VOICE_PROFILES_DIR=./data/voice_profiles
set BACKUP_DIR=./data/backups
set DEBUG=true
set LOCAL_DEV=true

REM 创建数据目录
echo [INFO] 创建数据目录...
if not exist "data" mkdir data
if not exist "data\audio" mkdir data\audio
if not exist "data\uploads" mkdir data\uploads
if not exist "data\voice_profiles" mkdir data\voice_profiles
if not exist "data\backups" mkdir data\backups
if not exist "data\logs" mkdir data\logs

REM 启动后端服务
echo [INFO] 启动后端服务...
echo [INFO] 后端地址: http://localhost:8000
echo [INFO] API文档: http://localhost:8000/docs
echo [INFO] 健康检查: http://localhost:8000/health
echo.
echo [INFO] 按 Ctrl+C 停止服务
echo.

python main.py

pause
