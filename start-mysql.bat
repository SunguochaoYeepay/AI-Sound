@echo off
chcp 65001 >nul
echo ========================================
echo    MySQL 数据库服务启动脚本
echo ========================================
echo.

:: 检查MySQL服务状态
echo 🔍 检查MySQL服务状态...
netstat -an | findstr :3306 >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ MySQL服务已在运行 (端口: 3306)
    echo 📍 连接地址: localhost:3306
    echo 👤 用户名: ai_sound_user
    echo 🔑 密码: ai_sound_password
    echo 🗄️  数据库: ai_sound
    echo.
    echo 🔄 开始监控MySQL服务状态...
    echo 📊 每10秒检查一次服务状态
    echo.
    echo 按 Ctrl+C 停止监控
    echo ========================================
    echo.
    
    :monitor_loop
    netstat -an | findstr :3306 >nul 2>&1
    if %errorlevel% equ 0 (
        echo [%date% %time%] ✅ MySQL服务运行正常
    ) else (
        echo [%date% %time%] ❌ MySQL服务已停止
        echo 🔄 尝试重新启动MySQL服务...
        net start mysql >nul 2>&1
        if %errorlevel% equ 0 (
            echo [%date% %time%] ✅ MySQL服务重启成功
        ) else (
            echo [%date% %time%] ❌ MySQL服务重启失败
        )
    )
    timeout /t 10 /nobreak >nul
    goto monitor_loop
)

:: 尝试启动MySQL服务
echo 🚀 尝试启动MySQL服务...
net start mysql >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ MySQL服务启动成功！
    echo 📍 连接地址: localhost:3306
    echo 👤 用户名: ai_sound_user
    echo 🔑 密码: ai_sound_password
    echo 🗄️  数据库: ai_sound
    echo.
    echo 💡 提示：如果数据库不存在，请运行以下SQL：
    echo CREATE DATABASE ai_sound CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
    echo CREATE USER 'ai_sound_user'@'localhost' IDENTIFIED BY 'ai_sound_password';
    echo GRANT ALL PRIVILEGES ON ai_sound.* TO 'ai_sound_user'@'localhost';
    echo FLUSH PRIVILEGES;
    echo.
    echo 🔄 开始监控MySQL服务状态...
    echo 📊 每10秒检查一次服务状态
    echo.
    echo 按 Ctrl+C 停止监控
    echo ========================================
    echo.
    
    :monitor_loop2
    netstat -an | findstr :3306 >nul 2>&1
    if %errorlevel% equ 0 (
        echo [%date% %time%] ✅ MySQL服务运行正常
    ) else (
        echo [%date% %time%] ❌ MySQL服务已停止
        echo 🔄 尝试重新启动MySQL服务...
        net start mysql >nul 2>&1
        if %errorlevel% equ 0 (
            echo [%date% %time%] ✅ MySQL服务重启成功
        ) else (
            echo [%date% %time%] ❌ MySQL服务重启失败
        )
    )
    timeout /t 10 /nobreak >nul
    goto monitor_loop2
)

:: 如果启动失败
echo ❌ MySQL服务启动失败！
echo.
echo 🔧 可能的解决方案：
echo 1. 检查MySQL是否已安装
echo 2. 检查MySQL服务是否已注册
echo 3. 使用管理员权限运行此脚本
echo 4. 手动启动MySQL服务
echo.
echo 📥 下载MySQL：
echo https://dev.mysql.com/downloads/mysql/
echo.
echo 🔧 或者使用XAMPP/WAMP等集成环境
echo.
pause
exit /b 1
