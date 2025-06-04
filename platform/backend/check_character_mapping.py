#!/usr/bin/env python3
"""
检查项目的角色映射状态
"""
import sqlite3
import json
import os

def check_character_mapping():
    db_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'database.db')
    db_path = os.path.abspath(db_path)  # 转换为绝对路径
    
    print(f"数据库路径: {db_path}")
    print(f"数据库存在: {os.path.exists(db_path)}")
    
    if not os.path.exists(db_path):
        print("数据库文件不存在")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 查看最新项目的角色映射
    cursor.execute('SELECT id, name, character_mapping FROM novel_projects ORDER BY created_at DESC LIMIT 1')
    project = cursor.fetchone()

    if project:
        print(f'=== 最新项目 ===')
        print(f'项目ID: {project[0]}')
        print(f'项目名称: {project[1]}')
        print(f'角色映射原始数据: {project[2]}')
        
        # 解析JSON
        try:
            mapping = json.loads(project[2]) if project[2] else {}
            print(f'解析后的映射: {mapping}')
            print(f'映射数量: {len(mapping)}')
        except json.JSONDecodeError as e:
            print(f'JSON解析错误: {e}')
        
        # 查看该项目的文本段落
        cursor.execute('SELECT id, detected_speaker, voice_profile_id FROM text_segments WHERE project_id = ? ORDER BY segment_order', (project[0],))
        segments = cursor.fetchall()
        
        print(f'\n=== 文本段落 ===')
        speakers = set()
        for segment in segments:
            print(f'段落ID: {segment[0]}, 说话人: {segment[1]}, 声音ID: {segment[2]}')
            if segment[1]:
                speakers.add(segment[1])
        
        print(f'\n=== 识别的角色 ===')
        for speaker in speakers:
            print(f'角色: {speaker}')
            
    else:
        print('没有找到项目')

    conn.close()

if __name__ == "__main__":
    check_character_mapping() 