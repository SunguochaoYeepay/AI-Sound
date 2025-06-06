-- 清空现有声音档案数据
DELETE FROM voice_profiles;

-- 创建默认声音角色
INSERT INTO voice_profiles (name, description, type, color, tags, parameters, quality_score, usage_count, status, created_at, updated_at) VALUES
('温柔女声', '温柔甜美的女性声音，适合朗读文学作品和温暖故事', 'female', '#ff6b9d', '["温柔", "甜美", "文学"]', '{"timeStep": 20, "pWeight": 1.0, "tWeight": 1.0}', 3.0, 0, 'active', NOW(), NOW()),
('磁性男声', '低沉有磁性的男性声音，适合商务播报和严肃内容', 'male', '#4e73df', '["磁性", "低沉", "商务"]', '{"timeStep": 20, "pWeight": 1.0, "tWeight": 1.0}', 3.0, 0, 'active', NOW(), NOW()),
('专业主播', '专业播音员声音，声音清晰标准，适合新闻播报', 'female', '#1cc88a', '["专业", "播音", "新闻"]', '{"timeStep": 20, "pWeight": 1.0, "tWeight": 1.0}', 3.0, 0, 'active', NOW(), NOW()),
('青春活力', '年轻有活力的声音，适合娱乐内容和轻松对话', 'female', '#36b9cc', '["青春", "活力", "娱乐"]', '{"timeStep": 20, "pWeight": 1.0, "tWeight": 1.0}', 3.0, 0, 'active', NOW(), NOW()),
('成熟稳重', '成熟稳重的男性声音，适合教育内容和知识分享', 'male', '#f6c23e', '["成熟", "稳重", "教育"]', '{"timeStep": 20, "pWeight": 1.0, "tWeight": 1.0}', 3.0, 0, 'active', NOW(), NOW()),
('童声萌音', '清脆可爱的儿童声音，适合童话故事和儿童内容', 'child', '#e74a3b', '["童声", "可爱", "童话"]', '{"timeStep": 20, "pWeight": 1.0, "tWeight": 1.0}', 3.0, 0, 'active', NOW(), NOW());

-- 查看创建结果
SELECT id, name, type, color FROM voice_profiles ORDER BY id;