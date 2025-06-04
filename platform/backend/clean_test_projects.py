#!/usr/bin/env python3
"""
清理测试项目
"""
import sqlite3
import os

def clean_test_projects():
    db_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'database.db')
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 查看现有项目
    cursor.execute('SELECT id, name, created_at FROM novel_projects ORDER BY created_at DESC')
    projects = cursor.fetchall()

    print('=== 现有项目 ===')
    for project in projects:
        print(f'ID: {project[0]}, 名称: {project[1]}, 创建时间: {project[2]}')

    # 删除重复的测试项目
    cursor.execute('DELETE FROM novel_projects WHERE name LIKE "%测试%"')
    deleted_count = cursor.rowcount

    print(f'\n=== 清理结果 ===')
    print(f'删除了 {deleted_count} 个测试项目')

    conn.commit()
    conn.close()

if __name__ == "__main__":
    clean_test_projects() 