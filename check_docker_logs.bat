@echo off
echo === 检查Docker容器日志 ===

echo.
echo 1. 检查容器状态...
docker inspect megatts3-api --format="{{.State.Status}}: {{.State.Health.Status}}"

echo.
echo 2. 查看容器日志（最近20行）...
docker logs megatts3-api --tail 20

echo.
echo 3. 查看实时日志（按Ctrl+C停止）...
echo 按Ctrl+C停止日志跟踪...
timeout /t 3 >nul
docker logs megatts3-api --follow --tail 5

pause 