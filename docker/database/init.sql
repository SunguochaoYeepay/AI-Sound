-- AI-Sound Platform 数据库初始化脚本
-- PostgreSQL 版本

-- 创建数据库和用户（如果需要）
-- CREATE DATABASE ai_sound;
-- CREATE USER ai_sound_user WITH PASSWORD 'ai_sound_password';
-- GRANT ALL PRIVILEGES ON DATABASE ai_sound TO ai_sound_user;

-- 连接到ai_sound数据库
\c ai_sound;

-- 启用必要的扩展
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- 创建音频文件表
CREATE TABLE IF NOT EXISTS audio_files (
    id SERIAL PRIMARY KEY,
    filename VARCHAR(255) NOT NULL,
    original_name VARCHAR(255),
    file_path TEXT NOT NULL,
    file_size BIGINT DEFAULT 0,
    duration REAL DEFAULT 0.0,
    type VARCHAR(50) DEFAULT 'unknown',
    project_id INTEGER,
    chapter_id INTEGER,
    character_name VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    is_favorite BOOLEAN DEFAULT FALSE,
    metadata JSONB DEFAULT '{}',
    
    -- 创建索引
    CONSTRAINT unique_file_path UNIQUE(file_path)
);

-- 创建朗读项目表
CREATE TABLE IF NOT EXISTS reader_projects (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    content TEXT,
    status VARCHAR(50) DEFAULT 'pending',
    total_chapters INTEGER DEFAULT 0,
    completed_chapters INTEGER DEFAULT 0,
    settings JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- 创建索引
    CONSTRAINT unique_project_name UNIQUE(name)
);

-- 创建章节表
CREATE TABLE IF NOT EXISTS chapters (
    id SERIAL PRIMARY KEY,
    project_id INTEGER NOT NULL REFERENCES reader_projects(id) ON DELETE CASCADE,
    title VARCHAR(255),
    content TEXT,
    chapter_number INTEGER,
    status VARCHAR(50) DEFAULT 'pending',
    characters JSONB DEFAULT '[]',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- 创建索引
    CONSTRAINT unique_project_chapter UNIQUE(project_id, chapter_number)
);

-- 创建声音配置表
CREATE TABLE IF NOT EXISTS voice_characters (
    id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    gender VARCHAR(20),
    age_range VARCHAR(50),
    tags TEXT[],
    quality_score REAL DEFAULT 0.0,
    usage_count INTEGER DEFAULT 0,
    description TEXT,
    audio_sample_path TEXT,
    config JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- 创建索引
    CONSTRAINT unique_character_name UNIQUE(name)
);

-- 创建用户表（可选）
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) NOT NULL,
    email VARCHAR(255),
    password_hash VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE,
    is_admin BOOLEAN DEFAULT FALSE,
    last_login TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- 创建索引
    CONSTRAINT unique_username UNIQUE(username),
    CONSTRAINT unique_email UNIQUE(email)
);

-- 创建任务队列表
CREATE TABLE IF NOT EXISTS task_queue (
    id SERIAL PRIMARY KEY,
    task_type VARCHAR(50) NOT NULL,
    task_data JSONB DEFAULT '{}',
    status VARCHAR(50) DEFAULT 'pending',
    priority INTEGER DEFAULT 0,
    progress INTEGER DEFAULT 0,
    result JSONB,
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    
    -- 创建索引
    INDEX idx_task_status (status),
    INDEX idx_task_type (task_type),
    INDEX idx_task_created (created_at)
);

-- 创建系统配置表
CREATE TABLE IF NOT EXISTS system_config (
    key VARCHAR(100) PRIMARY KEY,
    value JSONB,
    description TEXT,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 创建操作日志表
CREATE TABLE IF NOT EXISTS operation_logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER,
    operation VARCHAR(100) NOT NULL,
    resource_type VARCHAR(50),
    resource_id VARCHAR(100),
    details JSONB DEFAULT '{}',
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- 创建索引
    INDEX idx_logs_user (user_id),
    INDEX idx_logs_operation (operation),
    INDEX idx_logs_created (created_at)
);

-- 创建索引优化查询
CREATE INDEX IF NOT EXISTS idx_audio_files_type ON audio_files(type);
CREATE INDEX IF NOT EXISTS idx_audio_files_project ON audio_files(project_id);
CREATE INDEX IF NOT EXISTS idx_audio_files_created ON audio_files(created_at);
CREATE INDEX IF NOT EXISTS idx_audio_files_favorite ON audio_files(is_favorite);

CREATE INDEX IF NOT EXISTS idx_projects_status ON reader_projects(status);
CREATE INDEX IF NOT EXISTS idx_projects_created ON reader_projects(created_at);

CREATE INDEX IF NOT EXISTS idx_chapters_project ON chapters(project_id);
CREATE INDEX IF NOT EXISTS idx_chapters_status ON chapters(status);

CREATE INDEX IF NOT EXISTS idx_characters_gender ON voice_characters(gender);
CREATE INDEX IF NOT EXISTS idx_characters_tags ON voice_characters USING GIN(tags);

-- 创建全文搜索索引
CREATE INDEX IF NOT EXISTS idx_audio_files_search ON audio_files USING GIN(
    (original_name || ' ' || COALESCE(character_name, '')) gin_trgm_ops
);

CREATE INDEX IF NOT EXISTS idx_projects_search ON reader_projects USING GIN(
    name gin_trgm_ops
);

-- 创建触发器更新 updated_at 字段
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_audio_files_updated_at BEFORE UPDATE ON audio_files 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_projects_updated_at BEFORE UPDATE ON reader_projects 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_chapters_updated_at BEFORE UPDATE ON chapters 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_characters_updated_at BEFORE UPDATE ON voice_characters 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- 插入默认数据
INSERT INTO system_config (key, value, description) VALUES
('app_version', '"1.0.0"', '应用版本号'),
('max_file_size', '104857600', '最大文件上传大小（100MB）'),
('supported_formats', '["wav", "mp3", "m4a", "flac"]', '支持的音频格式'),
('default_tts_settings', '{"speed": 1.0, "pitch": 1.0, "emotion": "neutral"}', '默认TTS设置')
ON CONFLICT (key) DO NOTHING;

-- 插入默认管理员用户（密码: admin123，请在生产环境中修改）
INSERT INTO users (username, email, password_hash, is_admin) VALUES
('admin', 'admin@aisound.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj3sp3jIXl2u', TRUE)
ON CONFLICT (username) DO NOTHING;

-- 插入示例声音配置
INSERT INTO voice_characters (id, name, gender, age_range, tags, quality_score, description) VALUES
('voice_001', '温柔女声', 'female', 'young_adult', ARRAY['温柔', '清新', '甜美'], 4.5, '适合朗读浪漫小说和温馨故事'),
('voice_002', '磁性男声', 'male', 'adult', ARRAY['磁性', '低沉', '成熟'], 4.7, '适合朗读悬疑小说和商业文档'),
('voice_003', '活泼少女', 'female', 'teenager', ARRAY['活泼', '可爱', '青春'], 4.3, '适合朗读青春小说和儿童故事'),
('voice_004', '沉稳长者', 'male', 'senior', ARRAY['沉稳', '智慧', '权威'], 4.6, '适合朗读历史小说和学术文档')
ON CONFLICT (id) DO NOTHING;

-- 创建数据库视图便于查询
CREATE OR REPLACE VIEW v_project_stats AS
SELECT 
    p.id,
    p.name,
    p.status,
    p.total_chapters,
    p.completed_chapters,
    COUNT(af.id) as audio_file_count,
    SUM(af.file_size) as total_size,
    SUM(af.duration) as total_duration,
    p.created_at,
    p.updated_at
FROM reader_projects p
LEFT JOIN audio_files af ON p.id = af.project_id
GROUP BY p.id, p.name, p.status, p.total_chapters, p.completed_chapters, p.created_at, p.updated_at;

CREATE OR REPLACE VIEW v_character_usage AS
SELECT 
    vc.id,
    vc.name,
    vc.gender,
    vc.quality_score,
    COUNT(af.id) as usage_count,
    MAX(af.created_at) as last_used
FROM voice_characters vc
LEFT JOIN audio_files af ON vc.id = af.character_name
GROUP BY vc.id, vc.name, vc.gender, vc.quality_score;

-- 设置表权限
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO ai_sound_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO ai_sound_user;

-- 完成初始化
SELECT 'AI-Sound Platform 数据库初始化完成!' as message; 