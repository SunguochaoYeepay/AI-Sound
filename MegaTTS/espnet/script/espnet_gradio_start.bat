@echo off
REM === 1. 先杀掉所有 espnet/espnet:gpu-latest 和 my-espnet-gradio:latest 容器 ===
for /f "tokens=1" %%i in ('docker ps -a --filter "ancestor=my-espnet-gradio:latest" -q') do docker stop %%i
for /f "tokens=1" %%i in ('docker ps -a --filter "ancestor=espnet/espnet:gpu-latest" -q') do docker stop %%i

REM === 2. 选择端口（可自定义） ===
set PORT=9000

REM === 3. 启动自定义镜像并指定端口 ===
docker run --gpus all -it --rm -v D:/AI-Sound/megaTTS/espnet:/workspace -p %PORT%:%PORT% my-espnet-gradio:latest /bin/bash -c "cd /workspace && python espnet_tts_gradio.py --port %PORT%"

pause