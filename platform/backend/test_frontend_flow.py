#!/usr/bin/env python3
"""
模拟前端完整流程测试
"""
import requests
import json
import time

def test_frontend_flow():
    print("=== 测试前端完整流程 ===")
    
    # 1. 创建项目
    test_data = {
        'name': f'前端测试_{int(time.time())}',
        'description': '模拟前端流程',
        'text_content': '小明说："早上好！"小红回答："你好，小明。"旁白：两人在公园里相遇了。',
        'character_mapping': '{}'
    }
    
    print("1. 创建项目...")
    response = requests.post('http://localhost:8000/api/novel-reader/projects', data=test_data)
    
    if response.status_code != 200:
        print(f"❌ 项目创建失败: {response.status_code}")
        print(response.text)
        return
    
    project = response.json()['data']
    project_id = project['id']
    print(f"✅ 项目创建成功: ID={project_id}")
    
    # 2. 获取项目详情，查看分段结果
    print("\n2. 获取项目详情...")
    detail_response = requests.get(f'http://localhost:8000/api/novel-reader/projects/{project_id}')
    
    if detail_response.status_code != 200:
        print(f"❌ 获取详情失败: {detail_response.status_code}")
        return
    
    detail = detail_response.json()['data']
    segments = detail['segments']
    print(f"✅ 获取详情成功，共 {len(segments)} 个段落")
    
    # 提取角色
    characters = set()
    for segment in segments:
        characters.add(segment['detectedSpeaker'])
        print(f"  段落 {segment['segmentOrder']}: {segment['textContent'][:20]}... (说话人: {segment['detectedSpeaker']})")
    
    print(f"识别的角色: {list(characters)}")
    
    # 3. 获取可用声音
    print("\n3. 获取可用声音...")
    voices_response = requests.get('http://localhost:8000/api/characters/')
    
    if voices_response.status_code != 200:
        print(f"❌ 获取声音失败: {voices_response.status_code}")
        return
    
    voices = voices_response.json()['data']
    if not voices:
        print("❌ 没有可用的声音档案")
        return
    
    print(f"✅ 找到 {len(voices)} 个声音档案")
    for voice in voices[:3]:  # 只显示前3个
        print(f"  ID={voice['id']}: {voice['name']} ({voice.get('type', 'unknown')})")
    
    # 4. 设置角色映射
    print("\n4. 设置角色映射...")
    
    # 为每个角色分配声音
    character_mapping = {}
    for i, character in enumerate(characters):
        voice_id = voices[i % len(voices)]['id']  # 循环分配
        character_mapping[character] = voice_id
        print(f"  {character} -> 声音ID {voice_id}")
    
    # 更新项目
    update_data = {
        'name': detail['name'],
        'description': detail['description'],
        'character_mapping': json.dumps(character_mapping)
    }
    
    update_response = requests.put(f'http://localhost:8000/api/novel-reader/projects/{project_id}', data=update_data)
    
    if update_response.status_code != 200:
        print(f"❌ 角色映射设置失败: {update_response.status_code}")
        print(update_response.text)
        return
    
    print("✅ 角色映射设置成功")
    
    # 5. 开始音频生成
    print("\n5. 开始音频生成...")
    gen_data = {'parallel_tasks': 1}
    gen_response = requests.post(f'http://localhost:8000/api/novel-reader/projects/{project_id}/start-generation', data=gen_data)
    
    if gen_response.status_code == 200:
        print("✅ 音频生成开始成功")
        result = gen_response.json()
        print(f"总段落数: {result['totalSegments']}")
        print("🎉 前端流程测试完全成功!")
    else:
        print(f"❌ 音频生成失败: {gen_response.status_code}")
        print(f"错误: {gen_response.text}")
        
        # 检查数据库中的角色映射
        print("\n调试信息：检查数据库中的角色映射...")
        import sqlite3
        conn = sqlite3.connect('data/database.db')
        cursor = conn.cursor()
        cursor.execute('SELECT character_mapping FROM novel_projects WHERE id = ?', (project_id,))
        db_mapping = cursor.fetchone()
        if db_mapping:
            print(f"数据库中的角色映射: {db_mapping[0]}")
        conn.close()

if __name__ == "__main__":
    test_frontend_flow() 