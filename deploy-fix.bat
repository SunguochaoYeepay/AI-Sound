@echo off
echo ========================================
echo AI-Sound 服务修复与重新部署
echo ========================================

echo.
echo [1/6] 停止所有服务...
docker-compose down

echo.
echo [2/6] 清理旧的后端镜像...
docker rmi ai-sound-backend:latest -f

echo.
echo [3/6] 重新构建后端镜像（修复psutil依赖）...
docker build -t ai-sound-backend:latest -f docker/backend/Dockerfile .

if %ERRORLEVEL% NEQ 0 (
    echo 错误：后端镜像构建失败！
    pause
    exit /b 1
)

echo.
echo [4/6] 重新启动所有服务...
docker-compose up -d

if %ERRORLEVEL% NEQ 0 (
    echo 错误：服务启动失败！
    pause
    exit /b 1
)

echo.
echo [5/6] 等待服务启动（30秒）...
timeout /t 30 /nobreak > nul

echo.
echo [6/6] 测试服务状态...
echo 正在测试前端...
curl -s -o nul -w "前端状态: %%{http_code}\n" http://localhost:3001/

echo 正在测试API健康检查...
curl -s -o nul -w "API健康检查: %%{http_code}\n" http://localhost:3001/api/v1/health

echo 正在测试API文档...
curl -s -o nul -w "API文档: %%{http_code}\n" http://localhost:3001/docs

echo.
echo ========================================
echo 修复完成！请访问以下地址验证：
echo   前端界面: http://localhost:3001
echo   API文档:  http://localhost:3001/docs
echo   健康检查: http://localhost:3001/api/v1/health  
echo ========================================
echo.
echo 如果还有问题，请检查容器日志：
echo   docker logs ai-sound-backend
echo   docker logs ai-sound-nginx
echo.
pause 