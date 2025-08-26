@echo off
echo [XAMPP-SERVICES] 启动XAMPP服务...

REM 停止可能存在的服务
taskkill /f /im httpd.exe >nul 2>&1
taskkill /f /im mysqld.exe >nul 2>&1

REM 启动Apache服务
echo 正在启动Apache服务 (端口8080)...
start /B "Apache" "C:\xampp\apache\bin\httpd.exe" -f "C:\xampp\apache\conf\httpd.conf"

REM 等待Apache启动
timeout /t 3 /nobreak >nul

REM 启动MySQL服务
echo 正在启动MySQL服务...
start /B "MySQL" "C:\xampp\mysql\bin\mysqld.exe" --console --basedir=C:\xampp\mysql --datadir=C:\xampp\mysql\data --port=3306

REM 等待MySQL启动
timeout /t 5 /nobreak >nul

echo.
echo 服务启动完成！
echo.
echo 访问地址:
echo - phpMyAdmin: http://localhost:8080/phpmyadmin
echo - XAMPP主页: http://localhost:8080
echo.
echo 按任意键测试连接...
pause

REM 测试MySQL连接
echo 测试MySQL连接...
C:\xampp\mysql\bin\mysql.exe -u root -e "SELECT VERSION();" 2>nul
if %errorlevel% equ 0 (
    echo ✅ MySQL连接成功！
) else (
    echo ❌ MySQL连接失败
)

echo.
echo 按任意键退出...
pause
