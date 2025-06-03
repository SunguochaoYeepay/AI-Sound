@echo off
chcp 65001 >nul
echo === MegaTTS API 服务启动 ===

cd /d "%~dp0"
echo 当前目录: %CD%

echo 正在启动API服务...
powershell.exe -ExecutionPolicy Bypass -File "start_api_venv.ps1"

pause 