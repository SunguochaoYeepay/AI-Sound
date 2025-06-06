@echo off
echo 🧹 完整清理声音档案数据并重启服务...

echo.
echo ⚠️  警告：此操作将删除所有现有的声音档案数据！
echo.
set /p confirm="确定要继续吗？(输入 Y 继续): "
if /i not "%confirm%"=="Y" (
    echo 操作已取消
    pause
    exit /b
)

echo.
echo 📋 第一步：清理历史数据
cd /d D:\AI-Sound
python scripts\clean_voice_data.py

if %errorlevel% neq 0 (
    echo ❌ 数据清理失败！
    pause
    exit /b 1
)

echo.
echo 📋 第二步：重启后端服务（清理缓存）
docker-compose -f docker-compose.prod.yml restart backend

echo.
echo 📋 第三步：重启Nginx服务（确保配置生效）
docker-compose -f docker-compose.prod.yml restart nginx

echo.
echo ⏳ 等待服务重启...
timeout /t 15 >nul

echo.
echo 🧪 第四步：验证服务状态
echo 检查后端健康状态：
curl -s http://localhost:3001/api/health || echo "后端服务未响应"

echo.
echo 检查声音档案API：
curl -s "http://localhost:3001/api/characters/" | findstr "success" || echo "API接口异常"

echo.
echo 🎉 清理和重启完成！
echo.
echo ✅ 现在可以通过前端界面重新创建声音档案了
echo.
echo 📝 创建新声音档案的步骤：
echo 1. 打开浏览器访问 http://localhost:3001
echo 2. 进入"声音库管理"页面
echo 3. 点击"创建新声音档案"
echo 4. 上传音频文件并填写信息
echo 5. 新档案将自动使用正确的路径结构
echo.
echo 🔧 如果遇到问题，请检查：
echo - Docker容器是否正常运行：docker-compose -f docker-compose.prod.yml ps
echo - 后端日志：docker logs ai-sound-backend --tail 50
echo - Nginx日志：docker logs ai-sound-nginx --tail 50
echo.
pause