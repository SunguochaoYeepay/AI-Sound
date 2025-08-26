@echo off
echo [MYSQL-SETUP] AI-Sound MySQL数据库初始化 (XAMPP版本)...

REM 检查MySQL是否运行
echo [INFO] 检查MySQL服务状态...
netstat -an | findstr :3306 >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] MySQL服务未运行，请先启动MySQL服务
    echo [INFO] 可以使用以下命令启动MySQL:
    echo [INFO] net start mysql
    echo [INFO] 或者使用XAMPP控制面板启动
    pause
    exit /b 1
)

echo [INFO] MySQL服务运行正常

REM 尝试找到XAMPP的MySQL命令行工具
set MYSQL_PATH=

REM 检查常见的XAMPP安装路径
if exist "C:\xampp\mysql\bin\mysql.exe" (
    set MYSQL_PATH=C:\xampp\mysql\bin\mysql.exe
    echo [INFO] 找到XAMPP MySQL: %MYSQL_PATH%
) else if exist "C:\Program Files\xampp\mysql\bin\mysql.exe" (
    set MYSQL_PATH=C:\Program Files\xampp\mysql\bin\mysql.exe
    echo [INFO] 找到XAMPP MySQL: %MYSQL_PATH%
) else if exist "D:\xampp\mysql\bin\mysql.exe" (
    set MYSQL_PATH=D:\xampp\mysql\bin\mysql.exe
    echo [INFO] 找到XAMPP MySQL: %MYSQL_PATH%
) else (
    echo [ERROR] 未找到XAMPP MySQL命令行工具
    echo [INFO] 请检查XAMPP安装路径，或者手动创建数据库
    echo [INFO] 可以使用phpMyAdmin创建数据库和用户
    pause
    exit /b 1
)

REM 创建数据库和用户
echo [INFO] 创建数据库和用户...

REM 使用XAMPP的MySQL命令行工具创建数据库
"%MYSQL_PATH%" -u root -e "CREATE DATABASE IF NOT EXISTS ai_sound CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
if %errorlevel% neq 0 (
    echo [ERROR] 创建数据库失败，请检查MySQL root密码
    echo [INFO] XAMPP默认root密码为空，如果设置了密码请使用 -p 参数
    pause
    exit /b 1
)

REM 创建用户并授权
"%MYSQL_PATH%" -u root -e "CREATE USER IF NOT EXISTS 'ai_sound_user'@'localhost' IDENTIFIED BY 'ai_sound_password';"
"%MYSQL_PATH%" -u root -e "GRANT ALL PRIVILEGES ON ai_sound.* TO 'ai_sound_user'@'localhost';"
"%MYSQL_PATH%" -u root -e "FLUSH PRIVILEGES;"

echo [SUCCESS] MySQL数据库初始化完成！
echo [INFO] 数据库名: ai_sound
echo [INFO] 用户名: ai_sound_user
echo [INFO] 密码: ai_sound_password
echo [INFO] 字符集: utf8mb4
echo [INFO] MySQL路径: %MYSQL_PATH%

pause
