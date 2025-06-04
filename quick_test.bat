@echo off
echo === 快速服务测试 ===

echo.
echo 1. 测试MegaTTS3健康状态...
curl -X GET "http://localhost:7929/health"
echo.

echo 2. 测试MegaTTS3 API信息...
curl -X GET "http://localhost:7929/api/v1/info"
echo.

echo 3. 测试后端服务...
curl -X GET "http://localhost:8000/api/characters"
echo.

echo === 测试完成 ===
pause 