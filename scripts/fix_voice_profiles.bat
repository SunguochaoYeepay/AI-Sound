@echo off
echo 🔧 修复声音配置文件访问问题...

echo 📋 停止Nginx容器...
docker-compose -f docker-compose.prod.yml stop nginx

echo 🔄 重新启动Nginx容器...
docker-compose -f docker-compose.prod.yml up -d nginx

echo ⏳ 等待Nginx启动...
timeout /t 5 >nul

echo 🧪 测试声音配置文件访问...
curl -I http://localhost:3001/voice_profiles/专业主播_8f731640a7714934b2a2bf997868e67c.wav

echo 🎉 修复完成！请刷新前端页面测试音频播放功能。

pause