#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库备份表迁移脚本
创建备份相关的数据表
"""

import asyncio
import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.config import Settings
from app.models.base import Base
from app.models.backup import (
    BackupTask, BackupConfig, RestoreTask, BackupSchedule, BackupStats
)
from app.utils import log_system_event


def create_backup_tables():
    """创建备份相关表"""
    try:
        # 直接从环境变量获取数据库URL
        database_url = os.getenv("DATABASE_URL", "postgresql://ai_sound_user:ai_sound_password@localhost:5432/ai_sound")
        
        print(f"正在连接数据库: {database_url}")
        
        # 创建数据库引擎
        engine = create_engine(database_url, echo=True)
        
        # 测试连接
        with engine.connect() as connection:
            result = connection.execute(text("SELECT version()"))
            version = result.fetchone()[0]
            print(f"数据库连接成功，版本: {version}")
        
        print("正在创建备份相关表...")
        
        # 创建所有表
        Base.metadata.create_all(engine, tables=[
            BackupTask.__table__,
            BackupConfig.__table__,
            RestoreTask.__table__,
            BackupSchedule.__table__,
            BackupStats.__table__
        ])
        
        print("✅ 备份相关表创建成功！")
        
        # 插入默认配置
        SessionLocal = sessionmaker(bind=engine)
        db = SessionLocal()
        
        try:
            # 检查是否已有配置
            existing_config = db.query(BackupConfig).first()
            if not existing_config:
                print("正在插入默认配置...")
                
                default_configs = [
                    {
                        "config_key": "backup_retention_days",
                        "config_value": "30",
                        "config_type": "integer",
                        "description": "备份文件保留天数",
                        "category": "storage"
                    },
                    {
                        "config_key": "backup_compression_enabled",
                        "config_value": "true",
                        "config_type": "boolean",
                        "description": "是否启用备份压缩",
                        "category": "storage"
                    },
                    {
                        "config_key": "backup_encryption_enabled",
                        "config_value": "true",
                        "config_type": "boolean",
                        "description": "是否启用备份加密",
                        "category": "security"
                    },
                    {
                        "config_key": "backup_max_parallel",
                        "config_value": "2",
                        "config_type": "integer",
                        "description": "最大并行备份任务数",
                        "category": "performance"
                    },
                    {
                        "config_key": "auto_backup_enabled",
                        "config_value": "false",
                        "config_type": "boolean",
                        "description": "是否启用自动备份",
                        "category": "schedule"
                    },
                    {
                        "config_key": "auto_backup_time",
                        "config_value": "02:00",
                        "config_type": "string",
                        "description": "自动备份时间",
                        "category": "schedule"
                    },
                    {
                        "config_key": "notification_enabled",
                        "config_value": "true",
                        "config_type": "boolean",
                        "description": "是否启用通知",
                        "category": "notification"
                    },
                    {
                        "config_key": "notification_email",
                        "config_value": "",
                        "config_type": "string",
                        "description": "通知邮箱地址",
                        "category": "notification",
                        "is_sensitive": True
                    }
                ]
                
                for config_data in default_configs:
                    config = BackupConfig(
                        config_key=config_data["config_key"],
                        config_value=config_data["config_value"],
                        config_type=config_data["config_type"],
                        description=config_data["description"],
                        category=config_data["category"],
                        is_sensitive=config_data.get("is_sensitive", False),
                        is_active=True,
                        updated_by="system"
                    )
                    db.add(config)
                
                db.commit()
                print("✅ 默认配置插入成功！")
            else:
                print("默认配置已存在，跳过插入")
                
        finally:
            db.close()
        
        # 创建备份目录
        backup_dir = "/app/backups"
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir, exist_ok=True)
            print(f"✅ 备份目录创建成功: {backup_dir}")
        else:
            print(f"备份目录已存在: {backup_dir}")
        
        print("\n🎉 备份系统初始化完成！")
        print("📋 已创建的表:")
        print("  - backup_tasks (备份任务)")
        print("  - backup_configs (备份配置)")
        print("  - restore_tasks (恢复任务)")
        print("  - backup_schedules (备份调度)")
        print("  - backup_stats (备份统计)")
        print("\n📁 已创建目录:")
        print(f"  - {backup_dir} (备份文件存储)")
        
        return True
        
    except Exception as e:
        print(f"❌ 创建备份表失败: {str(e)}")
        return False


def check_backup_tables():
    """检查备份表是否存在"""
    try:
        # 直接从环境变量获取数据库URL
        database_url = os.getenv("DATABASE_URL", "postgresql://ai_sound_user:ai_sound_password@localhost:5432/ai_sound")
        
        engine = create_engine(database_url)
        
        with engine.connect() as connection:
            # 检查表是否存在
            tables_to_check = [
                'backup_tasks', 'backup_configs', 'restore_tasks', 
                'backup_schedules', 'backup_stats'
            ]
            
            existing_tables = []
            for table_name in tables_to_check:
                result = connection.execute(text(
                    "SELECT EXISTS (SELECT FROM information_schema.tables "
                    "WHERE table_schema = 'public' AND table_name = :table_name)"
                ), {"table_name": table_name})
                
                if result.fetchone()[0]:
                    existing_tables.append(table_name)
            
            print(f"现有备份表: {existing_tables}")
            print(f"缺少的表: {set(tables_to_check) - set(existing_tables)}")
            
            return len(existing_tables) == len(tables_to_check)
            
    except Exception as e:
        print(f"检查备份表失败: {str(e)}")
        return False


def main():
    """主函数"""
    print("🚀 数据库备份系统迁移脚本")
    print("="*50)
    
    # 检查当前状态
    print("1. 检查当前备份表状态...")
    if check_backup_tables():
        print("✅ 所有备份表已存在")
        
        # 询问是否重新创建
        response = input("是否要重新创建备份表？这将删除现有数据 (y/N): ")
        if response.lower() != 'y':
            print("操作已取消")
            return
    
    # 创建备份表
    print("\n2. 创建备份表...")
    if create_backup_tables():
        print("\n✅ 备份系统迁移完成！")
        print("\n下一步:")
        print("1. 启动后端服务")
        print("2. 访问 /docs 查看备份API文档")
        print("3. 创建前端备份管理界面")
    else:
        print("\n❌ 备份系统迁移失败！")
        sys.exit(1)


if __name__ == "__main__":
    main()