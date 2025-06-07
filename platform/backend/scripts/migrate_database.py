#!/usr/bin/env python3
"""
数据库迁移脚本
用于安全地执行数据库结构更新
"""

import os
import sys
import argparse
import logging
from datetime import datetime

# 添加app目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app'))

from database_health import DatabaseHealthChecker
from database import engine
from sqlalchemy import text

logger = logging.getLogger(__name__)

def backup_database():
    """备份数据库"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = f"../data/backups/backup_{timestamp}.sql"
    
    try:
        # PostgreSQL备份
        import subprocess
        cmd = [
            "docker", "exec", "ai-sound-db", 
            "pg_dump", "-U", "ai_sound_user", "-d", "ai_sound"
        ]
        
        with open(backup_file, 'w') as f:
            result = subprocess.run(cmd, stdout=f, stderr=subprocess.PIPE, text=True)
        
        if result.returncode == 0:
            logger.info(f"数据库备份成功: {backup_file}")
            return backup_file
        else:
            logger.error(f"数据库备份失败: {result.stderr}")
            return None
    except Exception as e:
        logger.error(f"备份过程失败: {str(e)}")
        return None

def check_database():
    """检查数据库健康状况"""
    checker = DatabaseHealthChecker()
    health_report = checker.check_database_health()
    
    print("\n" + "="*50)
    print("数据库健康检查报告")
    print("="*50)
    print(f"状态: {health_report['status']}")
    print(f"检查时间: {health_report['timestamp']}")
    
    if health_report['issues']:
        print("\n发现的问题:")
        for issue in health_report['issues']:
            print(f"  ❌ {issue}")
    
    if health_report['suggestions']:
        print("\n建议:")
        for suggestion in health_report['suggestions']:
            print(f"  💡 {suggestion}")
    
    if health_report['tables']:
        print("\n表统计:")
        for table_name, stats in health_report['tables'].items():
            if stats['exists']:
                print(f"  📊 {table_name}: {stats['row_count']} 条记录")
            else:
                print(f"  ❌ {table_name}: 表不存在或有错误")
    
    print("="*50)
    return health_report

def fix_database():
    """自动修复数据库结构"""
    checker = DatabaseHealthChecker()
    
    print("\n开始自动修复数据库结构...")
    fix_result = checker.auto_fix_structure()
    
    print("\n" + "="*50)
    print("数据库修复结果")
    print("="*50)
    print(f"修复状态: {'成功' if fix_result['success'] else '失败'}")
    print(f"修复时间: {fix_result['timestamp']}")
    
    if fix_result['fixes_applied']:
        print("\n已应用的修复:")
        for fix in fix_result['fixes_applied']:
            print(f"  ✅ {fix}")
    
    if fix_result['errors']:
        print("\n修复错误:")
        for error in fix_result['errors']:
            print(f"  ❌ {error}")
    
    print("="*50)
    return fix_result

def main():
    parser = argparse.ArgumentParser(description='数据库迁移工具')
    parser.add_argument('action', choices=['check', 'fix', 'backup'], 
                       help='执行的操作: check(检查), fix(修复), backup(备份)')
    parser.add_argument('--force', action='store_true', 
                       help='强制执行，跳过确认')
    parser.add_argument('--backup', action='store_true', 
                       help='在修复前自动备份')
    
    args = parser.parse_args()
    
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    if args.action == 'check':
        health_report = check_database()
        exit_code = 0 if health_report['status'] == 'healthy' else 1
        sys.exit(exit_code)
    
    elif args.action == 'backup':
        backup_file = backup_database()
        sys.exit(0 if backup_file else 1)
    
    elif args.action == 'fix':
        # 检查当前状况
        health_report = check_database()
        
        if health_report['status'] == 'healthy':
            print("✅ 数据库结构正常，无需修复")
            sys.exit(0)
        
        # 确认修复操作
        if not args.force:
            print(f"\n⚠️  发现 {len(health_report['issues'])} 个问题需要修复")
            response = input("是否继续修复? (y/N): ")
            if response.lower() != 'y':
                print("修复操作已取消")
                sys.exit(0)
        
        # 可选备份
        if args.backup:
            print("正在备份数据库...")
            backup_file = backup_database()
            if not backup_file:
                print("备份失败，修复操作已取消")
                sys.exit(1)
        
        # 执行修复
        fix_result = fix_database()
        sys.exit(0 if fix_result['success'] else 1)

if __name__ == "__main__":
    main() 