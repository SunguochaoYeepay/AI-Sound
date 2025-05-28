@echo off
REM 在本地启动模拟服务（不使用Docker）

echo 创建temp目录
mkdir temp 2>nul

echo 启动MegaTTS3模拟服务...
start cmd /k "python megatts3_mock.py"

echo 启动ESPnet模拟服务...
start cmd /k "python espnet_mock.py"

echo 模拟服务已启动：
echo MegaTTS3: http://localhost:9931
echo ESPnet: http://localhost:9932