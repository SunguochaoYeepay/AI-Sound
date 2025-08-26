@echo off
echo [MYSQL-SETUP] 设置MySQL数据库...

REM 停止MySQL服务
taskkill /f /im mysqld.exe >nul 2>&1
timeout /t 2 /nobreak >nul

REM 启动MySQL服务
echo 启动MySQL服务...
start /B "MySQL" "C:\xampp\mysql\bin\mysqld.exe" --console --basedir=C:\xampp\mysql --datadir=C:\xampp\mysql\data --port=3306

REM 等待MySQL启动
echo 等待MySQL启动...
timeout /t 10 /nobreak >nul

REM 创建数据库和用户
echo 创建数据库和用户...
C:\xampp\mysql\bin\mysql.exe -u root -e "CREATE DATABASE IF NOT EXISTS ai_sound CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;" 2>nul
C:\xampp\mysql\bin\mysql.exe -u root -e "CREATE USER IF NOT EXISTS 'ai_sound_user'@'localhost' IDENTIFIED BY 'ai_sound_password';" 2>nul
C:\xampp\mysql\bin\mysql.exe -u root -e "GRANT ALL PRIVILEGES ON ai_sound.* TO 'ai_sound_user'@'localhost';" 2>nul
C:\xampp\mysql\bin\mysql.exe -u root -e "FLUSH PRIVILEGES;" 2>nul

echo.
echo 数据库设置完成！
echo.
echo 数据库信息:
echo - 数据库名: ai_sound
echo - 用户名: ai_sound_user
echo - 密码: ai_sound_password
echo - 主机: localhost
echo - 端口: 3306
echo.

REM 测试连接
echo 测试数据库连接...
C:\xampp\mysql\bin\mysql.exe -u ai_sound_user -pai_sound_password ai_sound -e "SELECT 'Database connection successful!' as status;" 2>nul
if %errorlevel% equ 0 (
    echo ✅ 数据库连接成功！
) else (
    echo ❌ 数据库连接失败
)

echo.
echo 按任意键退出...
pause
