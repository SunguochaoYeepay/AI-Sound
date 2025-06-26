@echo off
echo 🎵 重新构建SongGeneration服务（软连接方案）...
cd /d D:\AI-Sound

echo 🛑 停止现有容器...
docker stop ai-sound-songgeneration
docker rm ai-sound-songgeneration

echo 🗑️ 删除旧镜像...
docker rmi ai-sound_songgeneration

echo 🔨 重新构建镜像...
docker-compose build songgeneration

echo 🚀 启动服务（挂载模型）...
docker-compose up -d songgeneration

echo ⏳ 等待启动...
timeout /t 10 /nobreak

echo 📊 检查服务状态...
docker-compose ps songgeneration

echo 📄 显示日志...
docker-compose logs --tail=20 songgeneration

echo ✅ 重建完成！
echo 🔗 测试链接: http://localhost:8081/health
pause 