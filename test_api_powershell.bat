@echo off
echo === PowerShell API测试 ===

echo.
echo 1. 测试MegaTTS3健康状态...
powershell -Command "Invoke-RestMethod -Uri 'http://localhost:7929/health' -Method Get"

echo.
echo 2. 测试MegaTTS3 API信息...
powershell -Command "Invoke-RestMethod -Uri 'http://localhost:7929/api/v1/info' -Method Get"

echo.
echo 3. 测试后端服务...
powershell -Command "Invoke-RestMethod -Uri 'http://localhost:8000/api/characters' -Method Get"

echo.
echo === 测试完成 ===
pause 