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
    file_path VARCHAR(500) NOT NULL,
    file_size INTEGER DEFAULT 0,
    duration REAL DEFAULT 0.0,
    sample_rate INTEGER DEFAULT 22050,
    channels INTEGER DEFAULT 1,
    project_id INTEGER REFERENCES novel_projects(id),
    segment_id INTEGER,
    voice_profile_id INTEGER REFERENCES voice_profiles(id),
    text_content TEXT,
    audio_type VARCHAR(20) DEFAULT 'segment',
    processing_time REAL,
    model_used VARCHAR(50),
    parameters TEXT,
    status VARCHAR(20) DEFAULT 'active',
    tags TEXT DEFAULT '[]',
    is_favorite BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- 创建约束
    CONSTRAINT unique_audio_filename UNIQUE(filename)
);

-- 创建文本段落表
CREATE TABLE IF NOT EXISTS text_segments (
    id SERIAL PRIMARY KEY,
    project_id INTEGER REFERENCES novel_projects(id) ON DELETE CASCADE,
    segment_order INTEGER NOT NULL,
    text_content TEXT NOT NULL,
    detected_speaker VARCHAR(100),
    voice_profile_id INTEGER REFERENCES voice_profiles(id),
    status VARCHAR(20) DEFAULT 'pending',
    audio_file_path VARCHAR(500),
    processing_time REAL,
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- 创建约束
    CONSTRAINT unique_project_segment UNIQUE(project_id, segment_order)
);

-- 创建声音档案表
CREATE TABLE IF NOT EXISTS voice_profiles (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    type VARCHAR(20) NOT NULL,
    reference_audio_path VARCHAR(500),
    latent_file_path VARCHAR(500),
    sample_audio_path VARCHAR(500),
    parameters TEXT NOT NULL DEFAULT '{"timeStep": 20, "pWeight": 1.0, "tWeight": 1.0}',
    quality_score REAL DEFAULT 3.0,
    usage_count INTEGER DEFAULT 0,
    last_used TIMESTAMP WITH TIME ZONE,
    color VARCHAR(20) DEFAULT '#06b6d4',
    tags TEXT DEFAULT '[]',
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- 创建约束
    CONSTRAINT unique_voice_profile_name UNIQUE(name)
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

-- 创建书籍管理表
CREATE TABLE IF NOT EXISTS books (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    author VARCHAR(255) DEFAULT '',
    description TEXT DEFAULT '',
    content TEXT NOT NULL,
    chapters JSONB DEFAULT '[]',
    status VARCHAR(50) DEFAULT 'draft',
    tags JSONB DEFAULT '[]',
    word_count INTEGER DEFAULT 0,
    chapter_count INTEGER DEFAULT 0,
    source_file_path TEXT,
    source_file_name VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- 创建约束
    CONSTRAINT unique_book_title UNIQUE(title)
);

-- 创建小说合成项目表
CREATE TABLE IF NOT EXISTS novel_projects (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    book_id INTEGER REFERENCES books(id) ON DELETE CASCADE,
    initial_characters TEXT DEFAULT '[]',
    status VARCHAR(20) DEFAULT 'pending',
    total_segments INTEGER DEFAULT 0,
    processed_segments INTEGER DEFAULT 0,
    failed_segments TEXT DEFAULT '[]',
    current_segment INTEGER DEFAULT 0,
    character_mapping TEXT DEFAULT '{}',
    final_audio_path VARCHAR(500),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    estimated_completion TIMESTAMP WITH TIME ZONE,
    
    -- 创建约束
    CONSTRAINT unique_novel_project_name UNIQUE(name)
);

-- 创建系统日志表
CREATE TABLE IF NOT EXISTS system_logs (
    id SERIAL PRIMARY KEY,
    level VARCHAR(10) NOT NULL,
    message TEXT NOT NULL,
    module VARCHAR(50),
    details TEXT,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 创建使用统计表
CREATE TABLE IF NOT EXISTS usage_stats (
    id SERIAL PRIMARY KEY,
    date VARCHAR(10) NOT NULL UNIQUE,
    total_requests INTEGER DEFAULT 0,
    successful_requests INTEGER DEFAULT 0,
    failed_requests INTEGER DEFAULT 0,
    total_processing_time REAL DEFAULT 0.0,
    audio_files_generated INTEGER DEFAULT 0
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
    completed_at TIMESTAMP WITH TIME ZONE
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
CREATE INDEX IF NOT EXISTS idx_audio_files_type ON audio_files(audio_type);
CREATE INDEX IF NOT EXISTS idx_audio_files_project ON audio_files(project_id);
CREATE INDEX IF NOT EXISTS idx_audio_files_created ON audio_files(created_at);
CREATE INDEX IF NOT EXISTS idx_audio_files_favorite ON audio_files(is_favorite);
CREATE INDEX IF NOT EXISTS idx_audio_files_voice_profile ON audio_files(voice_profile_id);

CREATE INDEX IF NOT EXISTS idx_voice_profiles_type ON voice_profiles(type);
CREATE INDEX IF NOT EXISTS idx_voice_profiles_status ON voice_profiles(status);
CREATE INDEX IF NOT EXISTS idx_voice_profiles_name ON voice_profiles(name);

CREATE INDEX IF NOT EXISTS idx_text_segments_project ON text_segments(project_id);
CREATE INDEX IF NOT EXISTS idx_text_segments_status ON text_segments(status);
CREATE INDEX IF NOT EXISTS idx_text_segments_voice_profile ON text_segments(voice_profile_id);

CREATE INDEX IF NOT EXISTS idx_books_status ON books(status);
CREATE INDEX IF NOT EXISTS idx_books_author ON books(author);
CREATE INDEX IF NOT EXISTS idx_books_created ON books(created_at);
CREATE INDEX IF NOT EXISTS idx_books_updated ON books(updated_at);
CREATE INDEX IF NOT EXISTS idx_books_tags ON books USING GIN(tags);

CREATE INDEX IF NOT EXISTS idx_novel_projects_book ON novel_projects(book_id);
CREATE INDEX IF NOT EXISTS idx_novel_projects_status ON novel_projects(status);

CREATE INDEX IF NOT EXISTS idx_system_logs_level ON system_logs(level);
CREATE INDEX IF NOT EXISTS idx_system_logs_module ON system_logs(module);
CREATE INDEX IF NOT EXISTS idx_system_logs_timestamp ON system_logs(timestamp);



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

CREATE TRIGGER update_voice_profiles_updated_at BEFORE UPDATE ON voice_profiles 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_books_updated_at BEFORE UPDATE ON books 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_novel_projects_updated_at BEFORE UPDATE ON novel_projects 
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
INSERT INTO voice_profiles (name, description, type, quality_score, tags, color) VALUES
('温柔女声', '适合朗读浪漫小说和温馨故事', 'female', 4.5, '["温柔", "清新", "甜美"]', '#f472b6'),
('磁性男声', '适合朗读悬疑小说和商业文档', 'male', 4.7, '["磁性", "低沉", "成熟"]', '#3b82f6'),
('活泼少女', '适合朗读青春小说和儿童故事', 'female', 4.3, '["活泼", "可爱", "青春"]', '#ec4899'),
('沉稳长者', '适合朗读历史小说和学术文档', 'male', 4.6, '["沉稳", "智慧", "权威"]', '#6b7280')
ON CONFLICT (name) DO NOTHING;

-- 创建数据库视图便于查询
CREATE OR REPLACE VIEW v_project_stats AS
SELECT 
    p.id,
    p.name,
    p.status,
    p.total_segments,
    p.processed_segments,
    COUNT(af.id) as audio_file_count,
    SUM(af.file_size) as total_size,
    SUM(af.duration) as total_duration,
    p.created_at
FROM novel_projects p
LEFT JOIN audio_files af ON p.id = af.project_id
GROUP BY p.id, p.name, p.status, p.total_segments, p.processed_segments, p.created_at;

CREATE OR REPLACE VIEW v_voice_profile_usage AS
SELECT 
    vp.id,
    vp.name,
    vp.type,
    vp.quality_score,
    COUNT(af.id) as usage_count,
    MAX(af.created_at) as last_used
FROM voice_profiles vp
LEFT JOIN audio_files af ON vp.id = af.voice_profile_id
GROUP BY vp.id, vp.name, vp.type, vp.quality_score;

-- 设置表权限
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO ai_sound_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO ai_sound_user;

-- 完成初始化
SELECT 'AI-Sound Platform 数据库初始化完成!' as message; 