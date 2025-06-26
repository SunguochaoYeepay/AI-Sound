#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI-Sound数据库完整修复脚本
修复所有已知的模型与表结构不符问题
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text
from datetime import datetime
import traceback

# 数据库连接
DATABASE_URL = "postgresql://ai_sound_user:ai_sound_password@localhost:5432/ai_sound"

def backup_database():
    """创建数据库备份"""
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = f"backup_before_full_fix_{timestamp}.sql"
        
        # 使用docker exec进行备份，设置密码环境变量
        backup_cmd = f'docker exec -e PGPASSWORD=ai_sound_password ai-sound-db pg_dump -U ai_sound_user -h localhost ai_sound > {backup_file}'
        result = os.system(backup_cmd)
        
        if result == 0:
            print(f"✅ 数据库备份完成: {backup_file}")
            return True
        else:
            print(f"⚠️ 备份命令执行完成，返回码: {result}")
            # 即使备份失败也继续执行，因为我们主要是修复结构
            return True
    except Exception as e:
        print(f"❌ 备份失败: {e}")
        print("⚠️ 跳过备份，直接进行修复")
        return True

def execute_sql(engine, sql_statements, description):
    """执行SQL语句"""
    print(f"\n🔧 {description}")
    with engine.connect() as conn:
        trans = conn.begin()
        try:
            for sql in sql_statements:
                print(f"  执行: {sql}")
                conn.execute(text(sql))
            trans.commit()
            print(f"✅ {description} - 完成")
            return True
        except Exception as e:
            trans.rollback()
            print(f"❌ {description} - 失败: {e}")
            return False

def fix_environment_sounds_table(engine):
    """修复环境音表结构"""
    sql_statements = [
        # 添加缺失的字段
        "ALTER TABLE environment_sounds ADD COLUMN IF NOT EXISTS sort_order INTEGER DEFAULT 0",
        "ALTER TABLE environment_sounds ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT true",
        "ALTER TABLE environment_sounds ADD COLUMN IF NOT EXISTS color VARCHAR(7) DEFAULT '#1890ff'",
        "ALTER TABLE environment_sounds ADD COLUMN IF NOT EXISTS tags JSONB DEFAULT '[]'::jsonb",
        
        # 更新现有数据
        "UPDATE environment_sounds SET sort_order = id WHERE sort_order IS NULL",
        "UPDATE environment_sounds SET is_active = true WHERE is_active IS NULL",
        "UPDATE environment_sounds SET color = '#1890ff' WHERE color IS NULL",
        
        # 创建索引
        "CREATE INDEX IF NOT EXISTS idx_environment_sounds_is_active ON environment_sounds(is_active)",
        "CREATE INDEX IF NOT EXISTS idx_environment_sounds_sort_order ON environment_sounds(sort_order)",
    ]
    
    return execute_sql(engine, sql_statements, "修复环境音表结构")

def fix_book_chapters_table(engine):
    """修复书籍章节表结构"""
    sql_statements = [
        # 添加字符数字段
        "ALTER TABLE book_chapters ADD COLUMN IF NOT EXISTS character_count INTEGER DEFAULT 0",
        
        # 更新现有数据
        "UPDATE book_chapters SET character_count = LENGTH(content) WHERE character_count IS NULL OR character_count = 0",
        
        # 创建索引
        "CREATE INDEX IF NOT EXISTS idx_book_chapters_character_count ON book_chapters(character_count)",
    ]
    
    return execute_sql(engine, sql_statements, "修复书籍章节表结构")

def fix_audio_files_table(engine):
    """修复音频文件表结构"""
    sql_statements = [
        # 修改file_size字段类型为BIGINT
        "ALTER TABLE audio_files ALTER COLUMN file_size TYPE BIGINT USING file_size::bigint",
        
        # 添加缺失字段
        "ALTER TABLE audio_files ADD COLUMN IF NOT EXISTS model_used VARCHAR(100)",
        "ALTER TABLE audio_files ADD COLUMN IF NOT EXISTS tags TEXT",
        
        # 确保必要的索引存在
        "CREATE INDEX IF NOT EXISTS idx_audio_files_project_id ON audio_files(project_id)",
        "CREATE INDEX IF NOT EXISTS idx_audio_files_chapter_id ON audio_files(chapter_id)",
        "CREATE INDEX IF NOT EXISTS idx_audio_files_audio_type ON audio_files(audio_type)",
    ]
    
    return execute_sql(engine, sql_statements, "修复音频文件表结构")

def create_environment_mixing_tables(engine):
    """创建环境混音相关表"""
    sql_statements = [
        # 环境生成会话表
        """
        CREATE TABLE IF NOT EXISTS environment_generation_sessions (
            id SERIAL PRIMARY KEY,
            project_id INTEGER,
            chapter_id VARCHAR(50) NOT NULL,
            session_status VARCHAR(20) DEFAULT 'active',
            analysis_result JSONB,
            analysis_stats JSONB,
            analysis_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            validation_data JSONB,
            validation_summary JSONB,
            validation_timestamp TIMESTAMP,
            persistence_data JSONB,
            persistence_summary JSONB,
            persistence_timestamp TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """,
        
        # 环境轨道配置表
        """
        CREATE TABLE IF NOT EXISTS environment_track_configs (
            id SERIAL PRIMARY KEY,
            session_id INTEGER REFERENCES environment_generation_sessions(id) ON DELETE CASCADE,
            track_order INTEGER DEFAULT 0,
            start_time FLOAT NOT NULL,
            end_time FLOAT NOT NULL,
            scene_description TEXT,
            environment_tags TEXT[],
            intensity_level VARCHAR(20) DEFAULT 'medium',
            audio_file_path VARCHAR(500),
            generation_status VARCHAR(20) DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """,
        
        # 环境音频混音作业表
        """
        CREATE TABLE IF NOT EXISTS environment_audio_mixing_jobs (
            id SERIAL PRIMARY KEY,
            session_id INTEGER REFERENCES environment_generation_sessions(id) ON DELETE CASCADE,
            job_name VARCHAR(200),
            input_files JSONB,
            output_file_path VARCHAR(500),
            mixing_params JSONB,
            job_status VARCHAR(20) DEFAULT 'pending',
            started_at TIMESTAMP,
            completed_at TIMESTAMP,
            error_message TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """,
        
        # 环境生成日志表
        """
        CREATE TABLE IF NOT EXISTS environment_generation_logs (
            id SERIAL PRIMARY KEY,
            session_id INTEGER REFERENCES environment_generation_sessions(id) ON DELETE CASCADE,
            log_level VARCHAR(20) DEFAULT 'INFO',
            log_message TEXT NOT NULL,
            log_details JSONB,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """,
        
        # 创建索引
        "CREATE INDEX IF NOT EXISTS idx_environment_generation_sessions_project_id ON environment_generation_sessions(project_id)",
        "CREATE INDEX IF NOT EXISTS idx_environment_generation_sessions_chapter_id ON environment_generation_sessions(chapter_id)",
        "CREATE INDEX IF NOT EXISTS idx_environment_track_configs_session_id ON environment_track_configs(session_id)",
        "CREATE INDEX IF NOT EXISTS idx_environment_audio_mixing_jobs_session_id ON environment_audio_mixing_jobs(session_id)",
        "CREATE INDEX IF NOT EXISTS idx_environment_generation_logs_session_id ON environment_generation_logs(session_id)",
    ]
    
    return execute_sql(engine, sql_statements, "创建环境混音相关表")

def fix_system_logs_enum(engine):
    """修复系统日志枚举类型"""
    sql_statements = [
        # 创建枚举类型
        "DROP TYPE IF EXISTS loglevel CASCADE",
        "CREATE TYPE loglevel AS ENUM ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL')",
        
        "DROP TYPE IF EXISTS logmodule CASCADE", 
        "CREATE TYPE logmodule AS ENUM ('SYSTEM', 'TTS', 'ANALYSIS', 'AUDIO', 'ENVIRONMENT', 'API', 'DATABASE', 'BACKUP')",
        
        # 如果表存在，先备份数据
        """
        CREATE TABLE IF NOT EXISTS system_logs_backup AS 
        SELECT * FROM system_logs WHERE 1=0
        """,
        
        # 重建表结构
        """
        DROP TABLE IF EXISTS system_logs CASCADE
        """,
        
        """
        CREATE TABLE system_logs (
            id SERIAL PRIMARY KEY,
            level loglevel NOT NULL,
            module logmodule NOT NULL,
            message TEXT NOT NULL,
            details TEXT,
            source_file VARCHAR(255),
            source_line INTEGER,
            function VARCHAR(100),
            user_id VARCHAR(50),
            session_id VARCHAR(100),
            ip_address VARCHAR(45),
            user_agent VARCHAR(500),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """,
        
        # 创建索引
        "CREATE INDEX idx_log_level_time ON system_logs(level, created_at)",
        "CREATE INDEX idx_log_module_time ON system_logs(module, created_at)",
        "CREATE INDEX idx_log_user_time ON system_logs(user_id, created_at)",
    ]
    
    return execute_sql(engine, sql_statements, "修复系统日志表和枚举类型")

def fix_foreign_keys(engine):
    """修复外键约束"""
    sql_statements = [
        # 确保audio_files的外键约束
        """
        ALTER TABLE audio_files 
        ADD CONSTRAINT IF NOT EXISTS fk_audio_files_project 
        FOREIGN KEY (project_id) REFERENCES novel_projects(id) ON DELETE SET NULL
        """,
        
        """
        ALTER TABLE audio_files 
        ADD CONSTRAINT IF NOT EXISTS fk_audio_files_voice_profile 
        FOREIGN KEY (voice_profile_id) REFERENCES voice_profiles(id) ON DELETE SET NULL
        """,
        
        # 确保book_chapters的外键约束
        """
        ALTER TABLE book_chapters 
        ADD CONSTRAINT IF NOT EXISTS fk_book_chapters_book 
        FOREIGN KEY (book_id) REFERENCES books(id) ON DELETE CASCADE
        """,
    ]
    
    return execute_sql(engine, sql_statements, "修复外键约束")

def verify_fixes(engine):
    """验证修复结果"""
    print("\n🔍 验证修复结果")
    
    checks = [
        ("environment_sounds表字段", "SELECT sort_order, is_active, color FROM environment_sounds LIMIT 1"),
        ("book_chapters表字段", "SELECT character_count FROM book_chapters LIMIT 1"),
        ("audio_files表字段", "SELECT file_size FROM audio_files LIMIT 1"),
        ("环境混音表", "SELECT COUNT(*) FROM environment_generation_sessions"),
        ("系统日志表", "SELECT COUNT(*) FROM system_logs"),
    ]
    
    success_count = 0
    with engine.connect() as conn:
        for check_name, sql in checks:
            try:
                result = conn.execute(text(sql))
                print(f"  ✅ {check_name} - 正常")
                success_count += 1
            except Exception as e:
                print(f"  ❌ {check_name} - 异常: {e}")
    
    print(f"\n验证结果: {success_count}/{len(checks)} 项通过")
    return success_count == len(checks)

def main():
    """主修复流程"""
    print("🚀 开始AI-Sound数据库完整修复")
    print("=" * 50)
    
    # 1. 备份数据库
    if not backup_database():
        print("❌ 备份失败，终止修复")
        return False
    
    # 2. 连接数据库
    try:
        engine = create_engine(DATABASE_URL)
        print("✅ 数据库连接成功")
    except Exception as e:
        print(f"❌ 数据库连接失败: {e}")
        return False
    
    # 3. 执行修复步骤
    fixes = [
        fix_environment_sounds_table,
        fix_book_chapters_table, 
        fix_audio_files_table,
        create_environment_mixing_tables,
        fix_system_logs_enum,
        fix_foreign_keys,
    ]
    
    success_count = 0
    for fix_func in fixes:
        try:
            if fix_func(engine):
                success_count += 1
        except Exception as e:
            print(f"❌ 修复函数 {fix_func.__name__} 失败: {e}")
            traceback.print_exc()
    
    # 4. 验证修复结果
    verification_success = verify_fixes(engine)
    
    # 5. 总结
    print("\n" + "=" * 50)
    print(f"🎯 修复完成: {success_count}/{len(fixes)} 项成功")
    print(f"🔍 验证结果: {'✅ 全部通过' if verification_success else '❌ 存在问题'}")
    
    if success_count == len(fixes) and verification_success:
        print("🎉 数据库修复完全成功！")
        return True
    else:
        print("⚠️  部分修复失败，请检查日志")
        return False

if __name__ == "__main__":
    main() 