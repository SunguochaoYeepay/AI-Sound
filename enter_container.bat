@echo off
echo === 进入MegaTTS3容器 ===

echo 检查容器状态...
docker ps | findstr megatts3-api

echo.
echo 进入容器...
docker exec -it megatts3-api /bin/bash

echo.
echo 如果上面失败，尝试sh...
docker exec -it megatts3-api /bin/sh

pause 