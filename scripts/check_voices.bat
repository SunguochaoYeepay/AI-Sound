@echo off
chcp 65001 >nul
echo 🎭 检查声音档案状态...
echo.

docker exec ai-sound-db psql -U ai_sound_user -d ai_sound -c "SELECT id, name, type, color FROM voice_profiles ORDER BY id;"

echo.
echo 🎉 检查完成！
echo.
echo 📝 如果看到角色列表，说明创建成功！
echo 📝 现在可以通过前端界面手工添加声音文件了！
echo.
echo 🌐 访问地址: http://localhost:3001
echo.
pause