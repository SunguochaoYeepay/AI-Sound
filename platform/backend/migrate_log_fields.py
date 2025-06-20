#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
日志字段迁移脚本
使用Python执行SQL迁移，不需要psql命令
"""

import sys
import os
sys.path.append(".")

from sqlalchemy import text
from app.database import engine
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def execute_migration():
    """执行日志字段迁移"""
    
    migration_sql = """
    -- 检查并添加字段的函数
    DO $$ 
    DECLARE
        column_exists boolean;
    BEGIN
        -- 检查 source_file 字段
        SELECT EXISTS (
            SELECT 1 FROM information_schema.columns 
            WHERE table_name='system_logs' AND column_name='source_file'
        ) INTO column_exists;
        
        IF NOT column_exists THEN
            ALTER TABLE system_logs ADD COLUMN source_file VARCHAR(500);
            RAISE NOTICE 'Added source_file column';
        ELSE
            RAISE NOTICE 'source_file column already exists';
        END IF;

        -- 检查 source_line 字段
        SELECT EXISTS (
            SELECT 1 FROM information_schema.columns 
            WHERE table_name='system_logs' AND column_name='source_line'
        ) INTO column_exists;
        
        IF NOT column_exists THEN
            ALTER TABLE system_logs ADD COLUMN source_line INTEGER;
            RAISE NOTICE 'Added source_line column';
        ELSE
            RAISE NOTICE 'source_line column already exists';
        END IF;

        -- 检查 function 字段
        SELECT EXISTS (
            SELECT 1 FROM information_schema.columns 
            WHERE table_name='system_logs' AND column_name='function'
        ) INTO column_exists;
        
        IF NOT column_exists THEN
            ALTER TABLE system_logs ADD COLUMN function VARCHAR(200);
            RAISE NOTICE 'Added function column';
        ELSE
            RAISE NOTICE 'function column already exists';
        END IF;

        -- 检查 user_id 字段
        SELECT EXISTS (
            SELECT 1 FROM information_schema.columns 
            WHERE table_name='system_logs' AND column_name='user_id'
        ) INTO column_exists;
        
        IF NOT column_exists THEN
            ALTER TABLE system_logs ADD COLUMN user_id VARCHAR(50);
            RAISE NOTICE 'Added user_id column';
        ELSE
            RAISE NOTICE 'user_id column already exists';
        END IF;

        -- 检查 session_id 字段
        SELECT EXISTS (
            SELECT 1 FROM information_schema.columns 
            WHERE table_name='system_logs' AND column_name='session_id'
        ) INTO column_exists;
        
        IF NOT column_exists THEN
            ALTER TABLE system_logs ADD COLUMN session_id VARCHAR(100);
            RAISE NOTICE 'Added session_id column';
        ELSE
            RAISE NOTICE 'session_id column already exists';
        END IF;

        -- 检查 ip_address 字段
        SELECT EXISTS (
            SELECT 1 FROM information_schema.columns 
            WHERE table_name='system_logs' AND column_name='ip_address'
        ) INTO column_exists;
        
        IF NOT column_exists THEN
            ALTER TABLE system_logs ADD COLUMN ip_address INET;
            RAISE NOTICE 'Added ip_address column';
        ELSE
            RAISE NOTICE 'ip_address column already exists';
        END IF;

        -- 检查 user_agent 字段
        SELECT EXISTS (
            SELECT 1 FROM information_schema.columns 
            WHERE table_name='system_logs' AND column_name='user_agent'
        ) INTO column_exists;
        
        IF NOT column_exists THEN
            ALTER TABLE system_logs ADD COLUMN user_agent TEXT;
            RAISE NOTICE 'Added user_agent column';
        ELSE
            RAISE NOTICE 'user_agent column already exists';
        END IF;

    END $$;
    """
    
    # 索引创建SQL
    index_sql = [
        "CREATE INDEX IF NOT EXISTS idx_system_logs_level ON system_logs(level);",
        "CREATE INDEX IF NOT EXISTS idx_system_logs_module ON system_logs(module);",
        "CREATE INDEX IF NOT EXISTS idx_system_logs_created_at ON system_logs(created_at);",
        "CREATE INDEX IF NOT EXISTS idx_system_logs_user_id ON system_logs(user_id);",
        "CREATE INDEX IF NOT EXISTS idx_system_logs_level_created ON system_logs(level, created_at);"
    ]
    
    try:
        logger.info("开始执行日志字段迁移...")
        
        # 连接数据库
        with engine.connect() as conn:
            # 执行字段添加
            logger.info("添加字段...")
            conn.execute(text(migration_sql))
            conn.commit()
            
            # 执行索引创建
            logger.info("创建索引...")
            for idx_sql in index_sql:
                conn.execute(text(idx_sql))
            conn.commit()
            
            logger.info("迁移完成！检查表结构...")
            
            # 检查表结构
            result = conn.execute(text("""
                SELECT column_name, data_type, is_nullable 
                FROM information_schema.columns 
                WHERE table_name = 'system_logs' 
                ORDER BY ordinal_position;
            """))
            
            print("\n=== system_logs 表结构 ===")
            for row in result:
                print(f"  {row.column_name:20} {row.data_type:15} {'NULL' if row.is_nullable == 'YES' else 'NOT NULL'}")
            
            print("\n✅ 迁移成功完成！")
            
    except Exception as e:
        logger.error(f"迁移失败: {e}")
        print(f"\n❌ 迁移失败: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("🚀 开始日志字段迁移...")
    success = execute_migration()
    if success:
        print("\n🎉 所有字段已成功添加，日志监控功能现在可以正常使用了！")
    else:
        print("\n💥 迁移失败，请检查错误信息")
        sys.exit(1)