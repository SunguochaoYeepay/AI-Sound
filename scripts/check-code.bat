@echo off
echo [CHECK] 检查容器内代码是否更新...

set "search_term=%1"
if "%search_term%"=="" set "search_term=book_id.*Optional"

echo [CHECK] 检查本地代码...
findstr /n "%search_term%" platform\backend\app\novel_reader.py

echo.
echo [CHECK] 检查容器内代码...
docker exec ai-sound-backend grep -n "%search_term%" /app/app/novel_reader.py

echo.
echo [CHECK] 容器内代码时间戳...
docker exec ai-sound-backend ls -la /app/app/novel_reader.py

echo.
echo [CHECK] 本地代码时间戳...
dir platform\backend\app\novel_reader.py

pause 