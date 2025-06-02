@echo off
echo ========================================
echo    MongoDB 数据备份工具
echo ========================================
echo.

cd /d "%~dp0"

set BACKUP_DIR=docker\volumes\mongodb_backup
set TIMESTAMP=%date:~0,4%%date:~5,2%%date:~8,2%_%time:~0,2%%time:~3,2%%time:~6,2%
set TIMESTAMP=%TIMESTAMP: =0%

echo 检查MongoDB是否运行...
docker ps --filter "name=ai-sound-mongodb" --filter "status=running" -q | findstr . >nul
if errorlevel 1 (
    echo [错误] MongoDB未运行，请先启动: start_mongodb.bat
    pause
    exit /b 1
)

echo 创建备份目录...
if not exist "%BACKUP_DIR%" mkdir "%BACKUP_DIR%"

echo 开始备份MongoDB数据...
echo 备份时间: %TIMESTAMP%
echo 备份路径: %BACKUP_DIR%\backup_%TIMESTAMP%

docker exec ai-sound-mongodb mongodump --out /backup_%TIMESTAMP%
docker cp ai-sound-mongodb:/backup_%TIMESTAMP% %BACKUP_DIR%\backup_%TIMESTAMP%
docker exec ai-sound-mongodb rm -rf /backup_%TIMESTAMP%

if errorlevel 1 (
    echo [错误] 备份失败
    pause
    exit /b 1
)

echo.
echo [成功] 数据备份完成！
echo 备份位置: %BACKUP_DIR%\backup_%TIMESTAMP%
echo.
echo 备份文件列表:
dir /b "%BACKUP_DIR%\backup_%TIMESTAMP%"

echo.
pause 