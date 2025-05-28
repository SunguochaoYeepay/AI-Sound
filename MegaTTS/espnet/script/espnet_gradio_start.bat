@echo off
for /f "tokens=*" %%i in ('docker ps -q --filter "ancestor=my-espnet-gradio:latest"') do docker stop %%i
set PORT=9000
docker run --gpus all -it --rm -v "D:/AI-Sound/MegaTTS/espnet:/workspace" -p %PORT%:%PORT% my-espnet-gradio:latest /bin/bash -c "cd /workspace && python espnet_tts_gradio.py --port %PORT%"
pause
