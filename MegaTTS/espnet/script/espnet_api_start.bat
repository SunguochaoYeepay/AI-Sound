@echo off
REM === 启动 Flask API 服务（5000端口） ===
docker run --gpus all -it --rm -v D:/AI-Sound/megaTTS/espnet:/workspace -p 5000:5000 my-espnet-gradio:latest /bin/bash -c "cd /workspace && python espnet_tts_api.py"
pause
