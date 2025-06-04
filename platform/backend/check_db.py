#!/usr/bin/env python3
"""
检查数据库状态
"""
import sqlite3
import os

def check_database():
    db_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'database.db')
    db_path = os.path.abspath(db_path)  # 转换为绝对路径
    
    print(f"数据库路径: {db_path}")
    print(f"数据库存在: {os.path.exists(db_path)}")
    
    if not os.path.exists(db_path):
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 查看所有表
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    print(f"\n数据库表: {[table[0] for table in tables]}")
    
    # 查看novel_projects表是否存在和内容
    if 'novel_projects' in [table[0] for table in tables]:
        cursor.execute("SELECT COUNT(*) FROM novel_projects")
        count = cursor.fetchone()[0]
        print(f"\nnovel_projects表记录数: {count}")
        
        if count > 0:
            cursor.execute("SELECT id, name, character_mapping FROM novel_projects ORDER BY created_at DESC LIMIT 5")
            projects = cursor.fetchall()
            print("\n最近的项目:")
            for project in projects:
                print(f"  ID: {project[0]}, 名称: {project[1]}, 映射: {project[2]}")
    else:
        print("\n❌ novel_projects表不存在")

    conn.close()

if __name__ == "__main__":
    check_database() 