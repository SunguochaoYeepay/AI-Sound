#!/usr/bin/env python3
import sqlite3
import json

conn = sqlite3.connect('data/database.db')
cursor = conn.cursor()

cursor.execute('SELECT id, name, character_mapping FROM novel_projects WHERE id = 16')
project = cursor.fetchone()

if project:
    print(f'项目16: {project[1]}')
    print(f'角色映射原始: {project[2]}')
    
    if project[2] and project[2] != '{}':
        try:
            mapping = json.loads(project[2])
            print(f'解析后角色映射: {mapping}')
        except:
            print('JSON解析失败')
    else:
        print('角色映射为空')
else:
    print('项目16不存在')

conn.close() 