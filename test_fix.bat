@echo off
echo === 测试端点修复效果 ===

echo.
echo 1. 检查MegaTTS3服务状态...
curl -X GET "http://localhost:7929/health" 2>nul
if %errorlevel% neq 0 (
    echo ❌ MegaTTS3服务未响应
) else (
    echo ✅ MegaTTS3服务正常
)

echo.
echo 2. 检查后端服务状态...
curl -X GET "http://localhost:8000/api/characters" 2>nul
if %errorlevel% neq 0 (
    echo ❌ 后端服务未响应
    echo 启动后端服务...
    start /b python -m uvicorn platform.backend.app.main:app --host 0.0.0.0 --port 8000
    timeout /t 5 >nul
) else (
    echo ✅ 后端服务正常
)

echo.
echo 3. 测试API端点...
curl -X GET "http://localhost:7929/api/v1/info" 2>nul

echo.
echo === 测试完成 ===
pause 