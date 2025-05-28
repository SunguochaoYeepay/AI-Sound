@echo off
REM 停止所有AI-Sound服务

echo 正在停止API和Web服务...
cd ..\services
docker-compose down
if %ERRORLEVEL% NEQ 0 (
    echo API和Web服务停止失败！
)

echo 正在停止ESPnet服务...
cd ..\espnet
docker-compose down
if %ERRORLEVEL% NEQ 0 (
    echo ESPnet服务停止失败！
)

echo 正在停止MegaTTS3服务...
cd ..\MegaTTS3
docker-compose down
if %ERRORLEVEL% NEQ 0 (
    echo MegaTTS3服务停止失败！
)

echo 所有服务已停止！

pause