# 数据库重新设计 - 支持分章节智能分析

## 🎯 **设计目标**
- 支持书籍分章节管理
- 持久化智能分析结果  
- 分批处理大模型请求
- 跟踪分析和合成进度
- 支持配置保存和恢复

## 📊 **新增表结构**

### 1. 书籍章节表 (book_chapters)
```sql
CREATE TABLE book_chapters (
    id SERIAL PRIMARY KEY,
    book_id INTEGER REFERENCES books(id) ON DELETE CASCADE,
    chapter_number INTEGER NOT NULL,
    chapter_title VARCHAR(200),
    content TEXT NOT NULL,
    word_count INTEGER DEFAULT 0,
    
    -- 处理状态
    analysis_status VARCHAR(20) DEFAULT 'pending', -- 'pending'|'analyzing'|'completed'|'failed'
    synthesis_status VARCHAR(20) DEFAULT 'pending',
    
    -- 时间戳
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(book_id, chapter_number)
);
```

### 2. 智能分析会话表 (analysis_sessions)
```sql
CREATE TABLE analysis_sessions (
    id SERIAL PRIMARY KEY,
    project_id INTEGER REFERENCES novel_projects(id) ON DELETE CASCADE,
    book_id INTEGER REFERENCES books(id),
    
    -- 分析范围
    target_type VARCHAR(20) NOT NULL, -- 'full_book'|'chapters'|'segments'
    target_ids TEXT, -- JSON数组，章节ID或段落ID列表
    
    -- 大模型配置
    llm_provider VARCHAR(50) DEFAULT 'dify',
    llm_model VARCHAR(100),
    llm_workflow_id VARCHAR(100),
    
    -- 会话状态
    status VARCHAR(20) DEFAULT 'pending', -- 'pending'|'running'|'completed'|'failed'|'cancelled'
    progress INTEGER DEFAULT 0, -- 0-100
    current_processing TEXT, -- 当前处理的章节/段落
    
    -- 结果统计
    total_tasks INTEGER DEFAULT 0,
    completed_tasks INTEGER DEFAULT 0,
    failed_tasks INTEGER DEFAULT 0,
    
    -- 时间信息
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    estimated_duration INTEGER, -- 预估时长(秒)
    
    -- 错误信息
    error_message TEXT,
    error_details JSONB
);
```

### 3. 智能分析结果表 (analysis_results)
```sql
CREATE TABLE analysis_results (
    id SERIAL PRIMARY KEY,
    session_id INTEGER REFERENCES analysis_sessions(id) ON DELETE CASCADE,
    chapter_id INTEGER REFERENCES book_chapters(id),
    
    -- 分析输入
    input_text TEXT NOT NULL,
    input_hash VARCHAR(64), -- 输入文本的哈希值，用于去重
    
    -- LLM响应
    llm_request_id VARCHAR(100),
    llm_response_time INTEGER, -- 响应时间(毫秒)
    raw_response JSONB, -- 大模型原始响应
    
    -- 解析后的结果
    project_info JSONB,
    synthesis_plan JSONB NOT NULL,
    characters JSONB NOT NULL,
    
    -- 用户修改
    user_modified BOOLEAN DEFAULT FALSE,
    user_config JSONB, -- 用户的修改配置
    final_config JSONB, -- 最终使用的配置
    
    -- 状态
    status VARCHAR(20) DEFAULT 'active', -- 'active'|'archived'|'superseded'
    version INTEGER DEFAULT 1,
    
    -- 时间戳
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    applied_at TIMESTAMP,
    
    INDEX idx_session_chapter (session_id, chapter_id),
    INDEX idx_input_hash (input_hash),
    INDEX idx_status_version (status, version)
);
```

### 4. 合成任务表 (synthesis_tasks)
```sql
CREATE TABLE synthesis_tasks (
    id SERIAL PRIMARY KEY,
    project_id INTEGER REFERENCES novel_projects(id) ON DELETE CASCADE,
    analysis_result_id INTEGER REFERENCES analysis_results(id),
    chapter_id INTEGER REFERENCES book_chapters(id),
    
    -- 任务配置
    synthesis_plan JSONB NOT NULL, -- 来自analysis_results的最终配置
    batch_size INTEGER DEFAULT 10, -- 批处理大小
    
    -- 进度跟踪
    status VARCHAR(20) DEFAULT 'pending', -- 'pending'|'running'|'completed'|'failed'|'paused'
    total_segments INTEGER DEFAULT 0,
    completed_segments INTEGER DEFAULT 0,
    failed_segments TEXT DEFAULT '[]', -- JSON数组，失败的segment_id
    current_segment INTEGER,
    
    -- 输出
    output_files JSONB DEFAULT '[]', -- 生成的音频文件列表
    final_audio_path VARCHAR(500),
    
    -- 时间信息
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    processing_time INTEGER, -- 总处理时间(秒)
    
    -- 错误处理
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3
);
```

### 5. 用户配置预设表 (user_presets)
```sql
CREATE TABLE user_presets (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    
    -- 配置内容
    config_type VARCHAR(20) NOT NULL, -- 'voice_mapping'|'synthesis_params'|'analysis_params'
    config_data JSONB NOT NULL,
    
    -- 适用范围
    scope VARCHAR(20) DEFAULT 'global', -- 'global'|'project'|'book'
    scope_id INTEGER, -- project_id 或 book_id
    
    -- 使用统计
    usage_count INTEGER DEFAULT 0,
    last_used TIMESTAMP,
    
    -- 时间戳
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_scope_type (scope, config_type)
);
```

## 🔄 **修改现有表结构**

### books表增强
```sql
ALTER TABLE books ADD COLUMN structure_status VARCHAR(20) DEFAULT 'raw'; -- 'raw'|'structured'|'analyzed'
ALTER TABLE books ADD COLUMN chapter_detection_method VARCHAR(20) DEFAULT 'auto'; -- 'auto'|'manual'|'regex'
ALTER TABLE books ADD COLUMN total_chapters INTEGER DEFAULT 0;
ALTER TABLE books ADD COLUMN analysis_priority INTEGER DEFAULT 0; -- 分析优先级
```

### novel_projects表增强  
```sql
ALTER TABLE novel_projects ADD COLUMN analysis_config JSONB; -- 分析配置
ALTER TABLE novel_projects ADD COLUMN synthesis_config JSONB; -- 合成配置
ALTER TABLE novel_projects ADD COLUMN target_chapters TEXT DEFAULT '[]'; -- 目标章节列表
ALTER TABLE novel_projects ADD COLUMN batch_mode BOOLEAN DEFAULT TRUE; -- 是否批处理模式
```

## 🚀 **数据索引优化**
```sql
-- 性能优化索引
CREATE INDEX idx_chapters_book_status ON book_chapters(book_id, analysis_status);
CREATE INDEX idx_sessions_project_status ON analysis_sessions(project_id, status);
CREATE INDEX idx_results_session_status ON analysis_results(session_id, status);
CREATE INDEX idx_tasks_project_status ON synthesis_tasks(project_id, status);
CREATE INDEX idx_presets_usage ON user_presets(usage_count DESC, last_used DESC);
``` 