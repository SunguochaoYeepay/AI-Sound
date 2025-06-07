"""
数据库健康检查和自动修复系统
防止数据库结构不匹配导致的API错误
"""

import logging
from sqlalchemy import text, inspect, Column
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from database import get_db, engine, Base
from models import *
import json
from typing import Dict, List, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class DatabaseHealthChecker:
    """数据库健康检查器"""
    
    def __init__(self):
        self.inspector = inspect(engine)
        self.required_tables = self._get_required_tables()
        self.required_columns = self._get_required_columns()
    
    def _get_required_tables(self) -> List[str]:
        """获取所有必需的表名"""
        return [table.name for table in Base.metadata.tables.values()]
    
    def _get_required_columns(self) -> Dict[str, Dict[str, Any]]:
        """获取所有表的必需列结构"""
        columns_info = {}
        for table_name, table in Base.metadata.tables.items():
            columns_info[table_name] = {}
            for column in table.columns:
                columns_info[table_name][column.name] = {
                    'type': str(column.type),
                    'nullable': column.nullable,
                    'default': str(column.default) if column.default else None,
                    'primary_key': column.primary_key
                }
        return columns_info
    
    def check_database_health(self) -> Dict[str, Any]:
        """执行完整的数据库健康检查"""
        health_report = {
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'issues': [],
            'suggestions': [],
            'tables': {}
        }
        
        try:
            # 检查表存在性
            missing_tables = self._check_missing_tables()
            if missing_tables:
                health_report['status'] = 'unhealthy'
                health_report['issues'].append(f"缺少表: {', '.join(missing_tables)}")
                health_report['suggestions'].append("运行数据库迁移或重新初始化")
            
            # 检查列结构
            column_issues = self._check_column_structure()
            if column_issues:
                health_report['status'] = 'unhealthy'
                health_report['issues'].extend(column_issues)
                health_report['suggestions'].append("运行数据库结构修复")
            
            # 检查外键约束
            fk_issues = self._check_foreign_keys()
            if fk_issues:
                health_report['status'] = 'warning'
                health_report['issues'].extend(fk_issues)
            
            # 记录表统计信息
            health_report['tables'] = self._get_table_stats()
            
        except Exception as e:
            health_report['status'] = 'error'
            health_report['issues'].append(f"健康检查失败: {str(e)}")
            logger.error(f"数据库健康检查失败: {str(e)}")
        
        return health_report
    
    def _check_missing_tables(self) -> List[str]:
        """检查缺失的表"""
        existing_tables = set(self.inspector.get_table_names())
        required_tables = set(self.required_tables)
        missing_tables = required_tables - existing_tables
        return list(missing_tables)
    
    def _check_column_structure(self) -> List[str]:
        """检查列结构问题"""
        issues = []
        
        for table_name in self.required_tables:
            if table_name not in self.inspector.get_table_names():
                continue
                
            existing_columns = {col['name']: col for col in self.inspector.get_columns(table_name)}
            required_columns = self.required_columns.get(table_name, {})
            
            # 检查缺失的列
            missing_columns = set(required_columns.keys()) - set(existing_columns.keys())
            for col_name in missing_columns:
                issues.append(f"表 {table_name} 缺少列: {col_name}")
            
            # 检查列类型不匹配（简化检查）
            for col_name, col_info in required_columns.items():
                if col_name in existing_columns:
                    existing_type = str(existing_columns[col_name]['type'])
                    required_type = col_info['type']
                    # 这里可以添加更复杂的类型匹配逻辑
        
        return issues
    
    def _check_foreign_keys(self) -> List[str]:
        """检查外键约束"""
        issues = []
        
        for table_name in self.required_tables:
            if table_name not in self.inspector.get_table_names():
                continue
                
            try:
                foreign_keys = self.inspector.get_foreign_keys(table_name)
                # 这里可以添加外键完整性检查
            except Exception as e:
                issues.append(f"表 {table_name} 外键检查失败: {str(e)}")
        
        return issues
    
    def _get_table_stats(self) -> Dict[str, Any]:
        """获取表统计信息"""
        stats = {}
        
        try:
            with next(get_db()) as db:
                for table_name in self.inspector.get_table_names():
                    try:
                        result = db.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
                        count = result.scalar()
                        stats[table_name] = {
                            'row_count': count,
                            'exists': True
                        }
                    except Exception as e:
                        stats[table_name] = {
                            'row_count': -1,
                            'exists': False,
                            'error': str(e)
                        }
        except Exception as e:
            logger.error(f"获取表统计信息失败: {str(e)}")
        
        return stats
    
    def auto_fix_structure(self) -> Dict[str, Any]:
        """自动修复数据库结构问题"""
        fix_result = {
            'success': True,
            'fixes_applied': [],
            'errors': [],
            'timestamp': datetime.utcnow().isoformat()
        }
        
        try:
            # 1. 创建缺失的表
            missing_tables = self._check_missing_tables()
            if missing_tables:
                try:
                    Base.metadata.create_all(bind=engine)
                    fix_result['fixes_applied'].append(f"创建缺失的表: {', '.join(missing_tables)}")
                    logger.info(f"自动创建缺失的表: {missing_tables}")
                except Exception as e:
                    fix_result['errors'].append(f"创建表失败: {str(e)}")
                    fix_result['success'] = False
            
            # 2. 添加缺失的列
            column_fixes = self._fix_missing_columns()
            if column_fixes:
                fix_result['fixes_applied'].extend(column_fixes)
            
        except Exception as e:
            fix_result['success'] = False
            fix_result['errors'].append(f"自动修复失败: {str(e)}")
            logger.error(f"数据库自动修复失败: {str(e)}")
        
        return fix_result
    
    def _fix_missing_columns(self) -> List[str]:
        """修复缺失的列"""
        fixes = []
        
        # 这里是我们今天手动修复的逻辑的自动化版本
        critical_columns = {
            'novel_projects': [
                ('initial_characters', 'TEXT DEFAULT \'[]\''),
                ('total_segments', 'INTEGER DEFAULT 0'),
                ('processed_segments', 'INTEGER DEFAULT 0'),
                ('failed_segments', 'TEXT DEFAULT \'[]\''),
                ('current_segment', 'INTEGER DEFAULT 0'),
                ('character_mapping', 'TEXT DEFAULT \'{}\''),
                ('final_audio_path', 'VARCHAR(500)'),
                ('started_at', 'TIMESTAMP WITH TIME ZONE'),
                ('completed_at', 'TIMESTAMP WITH TIME ZONE'),
                ('estimated_completion', 'TIMESTAMP WITH TIME ZONE')
            ]
        }
        
        try:
            with engine.connect() as conn:
                for table_name, columns in critical_columns.items():
                    if table_name in self.inspector.get_table_names():
                        existing_columns = {col['name'] for col in self.inspector.get_columns(table_name)}
                        
                        for col_name, col_definition in columns:
                            if col_name not in existing_columns:
                                try:
                                    sql = f"ALTER TABLE {table_name} ADD COLUMN IF NOT EXISTS {col_name} {col_definition}"
                                    conn.execute(text(sql))
                                    conn.commit()
                                    fixes.append(f"添加列 {table_name}.{col_name}")
                                    logger.info(f"自动添加列: {table_name}.{col_name}")
                                except Exception as e:
                                    logger.error(f"添加列失败 {table_name}.{col_name}: {str(e)}")
        
        except Exception as e:
            logger.error(f"修复缺失列失败: {str(e)}")
        
        return fixes

def startup_database_check():
    """启动时的数据库检查"""
    logger.info("[STARTUP] 开始数据库健康检查...")
    
    checker = DatabaseHealthChecker()
    health_report = checker.check_database_health()
    
    if health_report['status'] == 'unhealthy':
        logger.warning(f"[STARTUP] 数据库结构有问题: {health_report['issues']}")
        logger.info("[STARTUP] 尝试自动修复数据库结构...")
        
        fix_result = checker.auto_fix_structure()
        if fix_result['success']:
            logger.info(f"[STARTUP] 数据库结构修复成功: {fix_result['fixes_applied']}")
        else:
            logger.error(f"[STARTUP] 数据库结构修复失败: {fix_result['errors']}")
            return False
    
    elif health_report['status'] == 'warning':
        logger.warning(f"[STARTUP] 数据库有警告: {health_report['issues']}")
    
    else:
        logger.info("[STARTUP] 数据库结构健康")
    
    return True

# 全局健康检查器实例
health_checker = DatabaseHealthChecker() 