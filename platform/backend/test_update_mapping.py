#!/usr/bin/env python3
"""
测试角色映射更新功能
"""
import requests
import json

def test_update_mapping():
    project_id = 16
    
    print(f"=== 测试项目 {project_id} 角色映射更新 ===")
    
    # 1. 获取项目详情
    print("1. 获取项目详情...")
    detail_response = requests.get(f'http://localhost:8000/api/novel-reader/projects/{project_id}')
    
    if detail_response.status_code != 200:
        print(f"❌ 获取项目详情失败: {detail_response.status_code}")
        return
    
    detail = detail_response.json()['data']
    print(f"✅ 项目名称: {detail['name']}")
    print(f"当前角色映射: {detail['characterMapping']}")
    
    # 获取段落和角色
    segments = detail.get('segments', [])
    characters = set()
    for segment in segments:
        characters.add(segment['detectedSpeaker'])
        print(f"  段落 {segment['segmentOrder']}: {segment['detectedSpeaker']}")
    
    print(f"识别的角色: {list(characters)}")
    
    # 2. 获取可用声音
    print("\n2. 获取可用声音...")
    voices_response = requests.get('http://localhost:8000/api/characters/')
    
    if voices_response.status_code != 200:
        print(f"❌ 获取声音失败: {voices_response.status_code}")
        return
    
    voices = voices_response.json()['data']
    if not voices:
        print("❌ 没有可用的声音档案")
        return
    
    print(f"✅ 找到 {len(voices)} 个声音档案")
    print(f"声音ID {voices[0]['id']}: {voices[0]['name']}")
    
    # 3. 设置角色映射
    print("\n3. 设置角色映射...")
    
    # 为所有角色分配声音ID=1
    character_mapping = {}
    for character in characters:
        character_mapping[character] = 1
        print(f"  {character} -> 声音ID 1")
    
    print(f"要设置的角色映射: {json.dumps(character_mapping, ensure_ascii=False)}")
    
    # 4. 发送更新请求
    print("\n4. 发送更新请求...")
    update_data = {
        'name': detail['name'],
        'description': detail['description'],
        'character_mapping': json.dumps(character_mapping)
    }
    
    print(f"请求数据: {update_data}")
    
    update_response = requests.put(f'http://localhost:8000/api/novel-reader/projects/{project_id}', data=update_data)
    
    print(f"响应状态码: {update_response.status_code}")
    
    if update_response.status_code == 200:
        print("✅ 更新请求成功")
        result = update_response.json()
        print(f"响应: {json.dumps(result, indent=2, ensure_ascii=False)}")
    else:
        print(f"❌ 更新请求失败")
        print(f"错误: {update_response.text}")
        return
    
    # 5. 验证数据库中的角色映射
    print("\n5. 验证数据库中的角色映射...")
    import sqlite3
    conn = sqlite3.connect('data/database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT character_mapping FROM novel_projects WHERE id = ?', (project_id,))
    db_mapping = cursor.fetchone()
    
    if db_mapping:
        print(f"数据库中的角色映射: {db_mapping[0]}")
        if db_mapping[0] and db_mapping[0] != '{}':
            try:
                mapping = json.loads(db_mapping[0])
                print(f"解析后: {mapping}")
                print("✅ 角色映射保存成功")
            except:
                print("❌ JSON解析失败")
        else:
            print("❌ 角色映射为空，保存失败")
    else:
        print("❌ 项目不存在")
    
    conn.close()

if __name__ == "__main__":
    test_update_mapping() 