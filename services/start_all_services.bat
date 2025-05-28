@echo off
REM 启动所有AI-Sound服务

echo 正在创建共享网络...
call create_network.bat

echo 正在启动MegaTTS3服务...
cd ..\MegaTTS3
docker-compose up -d
if %ERRORLEVEL% NEQ 0 (
    echo MegaTTS3服务启动失败！
    goto error
)

echo 正在启动ESPnet服务...
cd ..\espnet
docker-compose up -d
if %ERRORLEVEL% NEQ 0 (
    echo ESPnet服务启动失败！
    goto error
)

echo 正在启动API和Web服务...
cd ..\services
docker-compose up -d
if %ERRORLEVEL% NEQ 0 (
    echo API和Web服务启动失败！
    goto error
)

echo 所有服务已启动完成！
echo 请访问以下地址：
echo Web管理界面: http://localhost:8080
echo API服务: http://localhost:9930
goto end

:error
echo 服务启动过程中出错，请检查日志！

:end
pause