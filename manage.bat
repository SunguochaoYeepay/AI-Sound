@echo off
chcp 65001 > nul
setlocal EnableDelayedExpansion

echo.
echo ==========================================
echo    🎵 AI-Sound 项目管理工具
echo ==========================================
echo.

if "%1"=="" (
    echo 用法: manage.bat [命令]
    echo.
    echo 📋 可用命令:
    echo.
    echo 🚀 启动相关:
    echo   start-backend     启动后端服务
    echo   start-full        启动完整平台 ^(Docker^)
    echo   start-megatts3    启动MegaTTS3引擎
    echo.
    echo 🔧 诊断修复:
    echo   diagnose         完整系统诊断
    echo   diagnose-tts     TTS服务诊断
    echo   fix-megatts3     修复MegaTTS3问题
    echo   fix-cuda         修复CUDA错误
    echo   check-logs       查看Docker日志
    echo.
    echo 🧪 测试相关:
    echo   test-api         测试API接口
    echo   test-quick       快速功能测试
    echo   test-character   测试角色检测
    echo.
    echo 🛠️ 容器管理:
    echo   enter-container  进入容器调试
    echo   rebuild          重建MegaTTS3容器
    echo   deep-fix         深度修复容器
    echo.
    echo 📊 项目管理:
    echo   commit           Git提交更改
    echo   backup           备份项目
    echo   health           健康检查
    echo.
    goto :EOF
)

REM 启动相关命令
if "%1"=="start-backend" (
    echo 🚀 启动后端服务...
    call start_backend.bat
    goto :EOF
)

if "%1"=="start-full" (
    echo 🚀 启动完整平台...
    docker-compose up -d
    goto :EOF
)

if "%1"=="start-megatts3" (
    echo 🚀 启动MegaTTS3引擎...
    docker-compose -f docker-compose.microservices.yml up -d
    goto :EOF
)

REM 诊断修复命令
if "%1"=="diagnose" (
    echo 🔍 执行完整系统诊断...
    call diagnose_services.bat
    goto :EOF
)

if "%1"=="diagnose-tts" (
    echo 🔍 执行TTS服务诊断...
    python diagnose_tts.py
    goto :EOF
)

if "%1"=="fix-megatts3" (
    echo 🔧 修复MegaTTS3问题...
    call fix_megatts3.bat
    goto :EOF
)

if "%1"=="fix-cuda" (
    echo 🔧 修复CUDA错误...
    python fix_cuda_error.py
    goto :EOF
)

if "%1"=="check-logs" (
    echo 📋 查看Docker日志...
    call check_docker_logs.bat
    goto :EOF
)

REM 测试相关命令
if "%1"=="test-api" (
    echo 🧪 测试API接口...
    call test_api_powershell.bat
    goto :EOF
)

if "%1"=="test-quick" (
    echo 🧪 快速功能测试...
    call quick_test.bat
    goto :EOF
)

if "%1"=="test-character" (
    echo 🧪 测试角色检测...
    python test_character_detection_simple.py
    goto :EOF
)

REM 容器管理命令
if "%1"=="enter-container" (
    echo 🛠️ 进入容器调试...
    call enter_container.bat
    goto :EOF
)

if "%1"=="rebuild" (
    echo 🛠️ 重建MegaTTS3容器...
    call rebuild_megatts3.bat
    goto :EOF
)

if "%1"=="deep-fix" (
    echo 🛠️ 深度修复容器...
    call deep_fix_megatts3.bat
    goto :EOF
)

REM 项目管理命令
if "%1"=="commit" (
    echo 📊 Git提交更改...
    call git_commit.bat
    goto :EOF
)

if "%1"=="backup" (
    echo 📊 备份项目...
    call commit_backup.bat
    goto :EOF
)

if "%1"=="health" (
    echo 📊 健康检查...
    bash scripts/megatts3_health.sh
    goto :EOF
)

echo ❌ 未知命令: %1
echo 使用 'manage.bat' 查看所有可用命令 