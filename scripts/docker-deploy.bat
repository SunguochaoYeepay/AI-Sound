@echo off
chcp 65001 > nul
setlocal EnableDelayedExpansion

echo.
echo ==========================================
echo    🚀 AI-Sound Docker化部署工具
echo ==========================================
echo.

if "%1"=="" set "command=full"
if not "%1"=="" set "command=%1"

REM 颜色定义（Windows暂不支持）
set "info_prefix=[INFO]"
set "warn_prefix=[WARN]"
set "error_prefix=[ERROR]"

goto :%command%

:check
echo %info_prefix% 检查前置条件...

REM 检查Docker
docker --version >nul 2>&1
if errorlevel 1 (
    echo %error_prefix% Docker未安装
    exit /b 1
)

REM 检查Docker Compose
docker-compose --version >nul 2>&1
if errorlevel 1 (
    echo %error_prefix% Docker Compose未安装
    exit /b 1
)

REM 检查.env文件
if not exist ".env" (
    echo %warn_prefix% .env文件不存在，创建模板...
    call :create_env_template
)

echo %info_prefix% 前置条件检查完成
goto :EOF

:create_env_template
echo # AI-Sound Docker Environment Configuration > .env
echo COMPOSE_PROJECT_NAME=ai-sound >> .env
echo NODE_ENV=production >> .env
echo DEBUG=false >> .env
echo. >> .env
echo # 服务端口配置 >> .env
echo FRONTEND_PORT=3000 >> .env
echo BACKEND_PORT=8000 >> .env
echo NGINX_PORT=80 >> .env
echo POSTGRES_PORT=5432 >> .env
echo. >> .env
echo # 数据库配置 >> .env
echo POSTGRES_DB=ai_sound >> .env
echo POSTGRES_USER=ai_sound_user >> .env
echo POSTGRES_PASSWORD=ai_sound_secure_password_2024 >> .env
echo. >> .env
echo # MegaTTS3引擎配置 >> .env
echo MEGATTS3_URL=http://megatts3:9000 >> .env
echo MEGATTS3_PORT=9000 >> .env
echo. >> .env
echo # 文件路径配置 >> .env
echo AUDIO_DIR=/app/storage/audio >> .env
echo UPLOADS_DIR=/app/storage/uploads >> .env
echo VOICE_PROFILES_DIR=/app/storage/voice_profiles >> .env
echo. >> .env
echo # 安全配置 >> .env
echo SECRET_KEY=your_super_secret_key_change_in_production >> .env
echo CORS_ORIGINS=http://localhost:3000,http://localhost >> .env

echo %info_prefix% 已创建.env模板文件，请根据需要修改配置
goto :EOF

:prepare_storage
echo %info_prefix% 准备存储目录...

REM 创建storage子目录
if not exist "storage" mkdir storage
if not exist "storage\audio" mkdir storage\audio
if not exist "storage\uploads" mkdir storage\uploads
if not exist "storage\voice_profiles" mkdir storage\voice_profiles
if not exist "storage\projects" mkdir storage\projects
if not exist "storage\database" mkdir storage\database
if not exist "storage\logs" mkdir storage\logs
if not exist "storage\config" mkdir storage\config
if not exist "storage\backups" mkdir storage\backups
if not exist "storage\redis" mkdir storage\redis

echo %info_prefix% 存储目录准备完成
goto :EOF

:build
call :check
if errorlevel 1 exit /b 1

echo %info_prefix% 构建Docker镜像...

REM 构建后端镜像
echo %info_prefix% 构建后端镜像...
docker build -f docker/backend/Dockerfile -t ai-sound-backend .
if errorlevel 1 (
    echo %error_prefix% 后端镜像构建失败
    exit /b 1
)

REM 构建前端镜像
echo %info_prefix% 构建前端镜像...
docker build -f docker/frontend/Dockerfile -t ai-sound-frontend .
if errorlevel 1 (
    echo %error_prefix% 前端镜像构建失败
    exit /b 1
)

echo %info_prefix% 镜像构建完成
goto :EOF

:infra
call :check
if errorlevel 1 exit /b 1
call :prepare_storage

echo %info_prefix% 启动基础设施服务...

REM 启动数据库和Redis
docker-compose -f docker/docker-compose.full.yml up -d database redis
if errorlevel 1 (
    echo %error_prefix% 基础设施启动失败
    exit /b 1
)

echo %info_prefix% 等待数据库启动...
timeout /t 15 /nobreak >nul

echo %info_prefix% 基础设施启动完成
goto :EOF

:app
echo %info_prefix% 启动应用服务...

REM 启动后端服务
docker-compose -f docker/docker-compose.full.yml up -d backend
if errorlevel 1 (
    echo %error_prefix% 后端服务启动失败
    exit /b 1
)

echo %info_prefix% 等待后端服务启动...
timeout /t 10 /nobreak >nul

REM 启动前端服务
docker-compose -f docker/docker-compose.full.yml up -d frontend
if errorlevel 1 (
    echo %error_prefix% 前端服务启动失败
    exit /b 1
)

REM 启动Nginx网关
docker-compose -f docker/docker-compose.full.yml up -d nginx

echo %info_prefix% 应用服务启动完成
call :health_check
call :show_access_info
goto :EOF

:health_check
echo %info_prefix% 执行健康检查...

REM 检查服务状态
docker-compose -f docker/docker-compose.full.yml ps

REM 简单的端口检查
netstat -an | findstr :3000 >nul && echo %info_prefix% ✅ 前端服务正常 (端口:3000) || echo %warn_prefix% ⚠️ 前端服务可能未就绪
netstat -an | findstr :8000 >nul && echo %info_prefix% ✅ 后端服务正常 (端口:8000) || echo %warn_prefix% ⚠️ 后端服务可能未就绪
netstat -an | findstr :80 >nul && echo %info_prefix% ✅ Nginx服务正常 (端口:80) || echo %warn_prefix% ⚠️ Nginx服务可能未就绪

goto :EOF

:show_access_info
echo.
echo 🎉 AI-Sound Docker部署完成！
echo.
echo 访问地址：
echo   - 前端界面: http://localhost:3000
echo   - 后端API: http://localhost:8000
echo   - API文档: http://localhost:8000/docs
echo   - Nginx网关: http://localhost
echo.
echo 管理命令：
echo   - 查看日志: docker-compose -f docker/docker-compose.full.yml logs -f
echo   - 停止服务: docker-compose -f docker/docker-compose.full.yml down
echo   - 重启服务: docker-compose -f docker/docker-compose.full.yml restart
echo.
goto :EOF

:full
call :check
if errorlevel 1 exit /b 1
call :prepare_storage
call :build
if errorlevel 1 exit /b 1
call :infra
if errorlevel 1 exit /b 1
call :app
goto :EOF

:help
echo 用法: %0 [check^|build^|infra^|app^|full]
echo   check - 检查前置条件
echo   build - 构建Docker镜像
echo   infra - 启动基础设施
echo   app   - 启动应用服务
echo   full  - 完整部署（默认）
goto :EOF

if "%command%"=="help" goto :help
echo %error_prefix% 未知命令: %command%
goto :help 