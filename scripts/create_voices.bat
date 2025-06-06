@echo off
echo 🎭 创建默认声音角色...

echo 📡 执行SQL脚本...
docker exec ai-sound-db psql -U ai_sound_user -d ai_sound -c "DELETE FROM voice_profiles;"

docker exec ai-sound-db psql -U ai_sound_user -d ai_sound -c "INSERT INTO voice_profiles (name, description, type, color, tags, parameters, quality_score, usage_count, status, created_at, updated_at) VALUES ('温柔女声', '温柔甜美的女性声音，适合朗读文学作品和温暖故事', 'female', '#ff6b9d', '[\"温柔\", \"甜美\", \"文学\"]', '{\"timeStep\": 20, \"pWeight\": 1.0, \"tWeight\": 1.0}', 3.0, 0, 'active', NOW(), NOW());"

docker exec ai-sound-db psql -U ai_sound_user -d ai_sound -c "INSERT INTO voice_profiles (name, description, type, color, tags, parameters, quality_score, usage_count, status, created_at, updated_at) VALUES ('磁性男声', '低沉有磁性的男性声音，适合商务播报和严肃内容', 'male', '#4e73df', '[\"磁性\", \"低沉\", \"商务\"]', '{\"timeStep\": 20, \"pWeight\": 1.0, \"tWeight\": 1.0}', 3.0, 0, 'active', NOW(), NOW());"

docker exec ai-sound-db psql -U ai_sound_user -d ai_sound -c "INSERT INTO voice_profiles (name, description, type, color, tags, parameters, quality_score, usage_count, status, created_at, updated_at) VALUES ('专业主播', '专业播音员声音，声音清晰标准，适合新闻播报', 'female', '#1cc88a', '[\"专业\", \"播音\", \"新闻\"]', '{\"timeStep\": 20, \"pWeight\": 1.0, \"tWeight\": 1.0}', 3.0, 0, 'active', NOW(), NOW());"

docker exec ai-sound-db psql -U ai_sound_user -d ai_sound -c "INSERT INTO voice_profiles (name, description, type, color, tags, parameters, quality_score, usage_count, status, created_at, updated_at) VALUES ('青春活力', '年轻有活力的声音，适合娱乐内容和轻松对话', 'female', '#36b9cc', '[\"青春\", \"活力\", \"娱乐\"]', '{\"timeStep\": 20, \"pWeight\": 1.0, \"tWeight\": 1.0}', 3.0, 0, 'active', NOW(), NOW());"

docker exec ai-sound-db psql -U ai_sound_user -d ai_sound -c "INSERT INTO voice_profiles (name, description, type, color, tags, parameters, quality_score, usage_count, status, created_at, updated_at) VALUES ('成熟稳重', '成熟稳重的男性声音，适合教育内容和知识分享', 'male', '#f6c23e', '[\"成熟\", \"稳重\", \"教育\"]', '{\"timeStep\": 20, \"pWeight\": 1.0, \"tWeight\": 1.0}', 3.0, 0, 'active', NOW(), NOW());"

docker exec ai-sound-db psql -U ai_sound_user -d ai_sound -c "INSERT INTO voice_profiles (name, description, type, color, tags, parameters, quality_score, usage_count, status, created_at, updated_at) VALUES ('童声萌音', '清脆可爱的儿童声音，适合童话故事和儿童内容', 'child', '#e74a3b', '[\"童声\", \"可爱\", \"童话\"]', '{\"timeStep\": 20, \"pWeight\": 1.0, \"tWeight\": 1.0}', 3.0, 0, 'active', NOW(), NOW());"

echo.
echo 📋 查看创建结果...
docker exec ai-sound-db psql -U ai_sound_user -d ai_sound -c "SELECT id, name, type, color FROM voice_profiles ORDER BY id;"

echo.
echo 🎉 默认角色创建完成！
echo.
echo 📝 下一步操作：
echo 1. 打开浏览器访问: http://localhost:3001
echo 2. 进入声音库管理页面
echo 3. 选择任意角色，点击编辑
echo 4. 上传对应的音频文件和latent文件
echo 5. 保存后即可使用该声音进行合成
echo.
echo 🔧 音频文件要求：
echo - 格式：WAV, MP3, FLAC, M4A, OGG
echo - 大小：不超过100MB
echo - 建议：10-30秒的清晰语音
echo.
pause