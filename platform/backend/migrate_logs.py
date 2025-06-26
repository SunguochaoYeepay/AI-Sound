#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
日志表数据库迁移脚本
为SystemLog表添加新字段
"""

import os
import sys
sys.path.append(".")

from app.database import engine, SessionLocal
from sqlalchemy import text, inspect
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_column_exists(table_name: str, column_name: str) -> bool:
    """检查列是否存在"""
    inspector = inspect(engine)
    columns = [col['name'] for col in inspector.get_columns(table_name)]
    return column_name in columns

def migrate_system_logs_table():
    """迁移SystemLog表结构"""
    logger.info("开始迁移SystemLog表结构...")
    
    db = SessionLocal()
    try:
        # 检查表是否存在
        inspector = inspect(engine)
        if 'system_logs' not in inspector.get_table_names():
            logger.info("系统日志表不存在，跳过迁移")
            return
        
        # 需要添加的新列
        new_columns = [
            ("source_file", "VARCHAR(255)"),
            ("source_line", "INTEGER"),
            ("user_agent", "VARCHAR(500)"),
        ]
        
        # 需要修改的列
        modifications = [
            ("user_id", "VARCHAR(50)"),  # 从INTEGER改为VARCHAR(50)
            ("ip_address", "VARCHAR(45)"),  # 从VARCHAR(50)改为VARCHAR(45)
            ("details", "TEXT"),  # 从JSON改为TEXT
        ]
        
        # 添加新列
        for column_name, column_type in new_columns:
            if not check_column_exists('system_logs', column_name):
                logger.info(f"添加列: {column_name}")
                sql = f"ALTER TABLE system_logs ADD COLUMN {column_name} {column_type}"
                db.execute(text(sql))
            else:
                logger.info(f"列已存在，跳过: {column_name}")
        
        # 如果需要修改列类型（PostgreSQL）
        if engine.dialect.name == 'postgresql':
            logger.info("PostgreSQL数据库，检查列类型...")
            
            # 检查user_id列类型
            result = db.execute(text("""
                SELECT data_type 
                FROM information_schema.columns 
                WHERE table_name = 'system_logs' AND column_name = 'user_id'
            """)).fetchone()
            
            if result and result[0] in ['integer', 'bigint']:
                logger.info("修改user_id列类型为VARCHAR(50)")
                db.execute(text("ALTER TABLE system_logs ALTER COLUMN user_id TYPE VARCHAR(50)"))
        
        # 添加索引
        indexes = [
            ("idx_log_level_time", "level, created_at"),
            ("idx_log_module_time", "module, created_at"), 
            ("idx_log_user_time", "user_id, created_at"),
        ]
        
        for index_name, columns in indexes:
            try:
                logger.info(f"创建索引: {index_name}")
                sql = f"CREATE INDEX IF NOT EXISTS {index_name} ON system_logs ({columns})"
                db.execute(text(sql))
            except Exception as e:
                logger.warning(f"创建索引失败: {index_name} - {e}")
        
        db.commit()
        logger.info("SystemLog表迁移完成！")
        
    except Exception as e:
        logger.error(f"迁移失败: {e}")
        db.rollback()
        raise
    finally:
        db.close()

def test_log_creation():
    """测试日志创建功能"""
    logger.info("测试日志创建功能...")
    
    try:
        from app.models.system import SystemLog
        from app.utils.logger import LogLevel, LogModule
        
        db = SessionLocal()
        try:
            # 创建测试日志
            test_log = SystemLog.create_log(
                level=LogLevel.INFO,
                module=LogModule.SYSTEM,
                message="数据库迁移测试日志",
                details='{"test": "migration", "timestamp": "2024-01-01"}',
                user_id="test_user",
                ip_address="127.0.0.1",
                user_agent="Migration Script"
            )
            
            db.add(test_log)
            db.commit()
            
            logger.info(f"测试日志创建成功，ID: {test_log.id}")
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"测试日志创建失败: {e}")
        raise

if __name__ == "__main__":
    logger.info("开始日志表迁移...")
    
    try:
        migrate_system_logs_table()
        test_log_creation()
        logger.info("✅ 迁移完成！")
        
    except Exception as e:
        logger.error(f"❌ 迁移失败: {e}")
        sys.exit(1)