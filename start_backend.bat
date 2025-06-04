@echo off
echo === 启动后端服务 ===

echo 切换到后端目录...
cd platform\backend

echo 启动服务...
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

pause 