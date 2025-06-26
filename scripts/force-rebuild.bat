@echo off
echo [REBUILD] 强制重建AI-Sound服务...

REM 停止所有服务
echo [REBUILD] 停止所有服务...
docker-compose down

REM 清理旧镜像和容器
echo [REBUILD] 清理旧镜像...
docker system prune -f
docker-compose build --no-cache

REM 重新启动服务
echo [REBUILD] 重新启动服务...
docker-compose up -d

REM 检查服务状态
echo [REBUILD] 检查服务状态...
timeout /t 15 /nobreak >nul
docker-compose ps

echo [REBUILD] 重建完成！
echo [INFO] 查看日志: docker-compose logs -f
pause 