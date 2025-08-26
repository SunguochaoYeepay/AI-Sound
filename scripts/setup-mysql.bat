@echo off
echo [MYSQL-SETUP] AI-Sound MySQL数据库初始化...

REM 检查MySQL是否运行
echo [INFO] 检查MySQL服务状态...
netstat -an | findstr :3306 >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] MySQL服务未运行，请先启动MySQL服务
    echo [INFO] 可以使用以下命令启动MySQL:
    echo [INFO] net start mysql
    echo [INFO] 或者使用XAMPP/WAMP等集成环境
    pause
    exit /b 1
)

echo [INFO] MySQL服务运行正常

REM 创建数据库和用户
echo [INFO] 创建数据库和用户...

REM 使用MySQL命令行工具创建数据库
mysql -u root -p -e "CREATE DATABASE IF NOT EXISTS ai_sound CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
if %errorlevel% neq 0 (
    echo [ERROR] 创建数据库失败，请检查MySQL root密码
    pause
    exit /b 1
)

REM 创建用户并授权
mysql -u root -p -e "CREATE USER IF NOT EXISTS 'ai_sound_user'@'localhost' IDENTIFIED BY 'ai_sound_password';"
mysql -u root -p -e "GRANT ALL PRIVILEGES ON ai_sound.* TO 'ai_sound_user'@'localhost';"
mysql -u root -p -e "FLUSH PRIVILEGES;"

echo [SUCCESS] MySQL数据库初始化完成！
echo [INFO] 数据库名: ai_sound
echo [INFO] 用户名: ai_sound_user
echo [INFO] 密码: ai_sound_password
echo [INFO] 字符集: utf8mb4

pause
