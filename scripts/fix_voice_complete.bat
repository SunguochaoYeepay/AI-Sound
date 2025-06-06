@echo off
echo 🔧 完整修复声音档案访问问题...

echo.
echo 📋 第一步：修复Docker映射配置（已完成）
echo ✅ Docker Compose配置已修复

echo.
echo 📋 第二步：修复数据库路径
cd /d D:\AI-Sound
python scripts\fix_voice_paths_comprehensive.py

echo.
echo 📋 第三步：重启Nginx容器
docker-compose -f docker-compose.prod.yml stop nginx
docker-compose -f docker-compose.prod.yml up -d nginx

echo.
echo ⏳ 等待Nginx重启...
timeout /t 10 >nul

echo.
echo 🧪 第四步：测试文件访问
echo 测试声音文件访问：
curl -I "http://localhost:3001/voice_profiles/专业主播_8f731640a7714934b2a2bf997868e67c.wav"

echo.
echo 🧪 测试API接口：
curl -s "http://localhost:3001/api/characters/" | jq ".data[0].referenceAudioUrl" 2>nul || echo "请安装jq工具或手动检查API返回"

echo.
echo 🎉 修复完成！请刷新前端页面测试音频播放功能。
echo.
echo 如果还有问题，请检查：
echo 1. 数据库中的文件路径是否正确
echo 2. voice_profiles目录中是否有对应的文件
echo 3. Nginx容器是否正常运行
echo.
pause