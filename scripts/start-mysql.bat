@echo off
echo [MYSQL-START] 启动MySQL服务...

REM 停止可能存在的MySQL进程
taskkill /f /im mysqld.exe >nul 2>&1

REM 启动MySQL服务
echo 正在启动MySQL...
C:\xampp\mysql\bin\mysqld.exe --console --basedir=C:\xampp\mysql --datadir=C:\xampp\mysql\data --port=3306 --socket=C:\xampp\mysql\data\mysql.sock

echo MySQL启动完成！
pause
