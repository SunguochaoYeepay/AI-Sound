#!/usr/bin/env python3
import sqlite3
import json
import os

# 使用绝对路径
db_path = r'D:\AI-Sound\platform\data\database.db'
print(f'数据库路径: {db_path}')
print(f'数据库存在: {os.path.exists(db_path)}')

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# 检查表是否存在
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
print(f'数据库表: {[t[0] for t in tables]}')

# 查询项目数量
cursor.execute('SELECT COUNT(*) FROM novel_projects')
count = cursor.fetchone()[0]
print(f'项目总数: {count}')

if count > 0:
    # 查询最新项目
    cursor.execute('SELECT id, name, character_mapping FROM novel_projects ORDER BY id DESC LIMIT 3')
    projects = cursor.fetchall()

    print('\n=== 最新项目 ===')
    for project in projects:
        print(f'ID: {project[0]}, 名称: {project[1]}')
        print(f'映射原始数据: {project[2]}')
        if project[2]:
            try:
                mapping = json.loads(project[2])
                print(f'解析后映射: {mapping}')
            except Exception as e:
                print(f'JSON解析失败: {e}')
        print('---')

    # 查询最新项目的段落
    latest_id = projects[0][0]
    cursor.execute('SELECT id, detected_speaker, voice_profile_id FROM text_segments WHERE project_id = ? ORDER BY segment_order', (latest_id,))
    segments = cursor.fetchall()
    
    print(f'\n=== 项目 {latest_id} 的段落 ===')
    for segment in segments:
        print(f'段落 {segment[0]}: 说话人={segment[1]}, 声音ID={segment[2]}')

conn.close() 