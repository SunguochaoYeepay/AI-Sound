#!/usr/bin/env python3
"""
最终验证：完整模拟前端流程
"""
import requests
import json
import time

def final_verification():
    print("🔍 === 最终验证：完整前端流程 ===")
    
    # Step 1: 创建全新项目（模拟前端的精确流程）
    print("\n📝 Step 1: 创建全新项目...")
    timestamp = int(time.time())
    
    test_data = {
        'name': f'最终验证项目_{timestamp}',
        'description': '完整验证测试',
        'text_content': '小明说："你好世界！"小红回答："很高兴见到你。"旁白：他们在咖啡厅里聊天。',
        'character_mapping': '{}'  # 初始为空
    }
    
    create_response = requests.post('http://localhost:8000/api/novel-reader/projects', data=test_data)
    
    if create_response.status_code != 200:
        print(f"❌ 项目创建失败: {create_response.status_code}")
        print(create_response.text)
        return False
    
    project = create_response.json()['data']
    project_id = project['id']
    print(f"✅ 项目创建成功: ID={project_id}, 名称={project['name']}")
    
    # Step 2: 获取项目详情（检查分段和角色检测）
    print(f"\n📋 Step 2: 获取项目详情...")
    detail_response = requests.get(f'http://localhost:8000/api/novel-reader/projects/{project_id}')
    
    if detail_response.status_code != 200:
        print(f"❌ 获取详情失败: {detail_response.status_code}")
        return False
    
    detail = detail_response.json()['data']
    segments = detail.get('segments', [])
    
    print(f"✅ 获取详情成功")
    print(f"   段落数量: {len(segments)}")
    print(f"   当前角色映射: {detail['characterMapping']}")
    
    # 收集角色
    characters = set()
    for segment in segments:
        speaker = segment['detectedSpeaker']
        characters.add(speaker)
        print(f"   段落 {segment['segmentOrder']}: '{segment['textContent'][:30]}...' -> 说话人: {speaker}")
    
    print(f"   识别角色: {list(characters)}")
    
    if not segments:
        print("❌ 没有分段，无法继续")
        return False
    
    # Step 3: 获取可用声音档案
    print(f"\n🎵 Step 3: 获取可用声音档案...")
    voices_response = requests.get('http://localhost:8000/api/characters/')
    
    if voices_response.status_code != 200:
        print(f"❌ 获取声音档案失败: {voices_response.status_code}")
        return False
    
    voices = voices_response.json()['data']
    if not voices:
        print("❌ 没有可用声音档案")
        return False
    
    print(f"✅ 找到 {len(voices)} 个声音档案")
    for voice in voices:
        print(f"   ID={voice['id']}: {voice['name']} ({voice.get('type', 'unknown')})")
    
    # Step 4: 设置角色映射（模拟前端的PUT请求）
    print(f"\n🎭 Step 4: 设置角色声音映射...")
    
    # 为每个角色分配声音
    character_mapping = {}
    for i, character in enumerate(characters):
        voice_id = voices[i % len(voices)]['id']
        character_mapping[character] = voice_id
        print(f"   {character} -> 声音ID {voice_id} ({voices[i % len(voices)]['name']})")
    
    # 发送更新请求（完全模拟前端）
    update_data = {
        'name': detail['name'],
        'description': detail['description'],
        'character_mapping': json.dumps(character_mapping)
    }
    
    print(f"   发送映射数据: {json.dumps(character_mapping, ensure_ascii=False)}")
    
    update_response = requests.put(f'http://localhost:8000/api/novel-reader/projects/{project_id}', data=update_data)
    
    if update_response.status_code != 200:
        print(f"❌ 角色映射设置失败: {update_response.status_code}")
        print(f"   错误: {update_response.text}")
        return False
    
    print("✅ 角色映射设置成功")
    
    # Step 5: 验证映射确实保存了
    print(f"\n🔍 Step 5: 验证映射保存...")
    
    # 重新获取项目详情
    verify_response = requests.get(f'http://localhost:8000/api/novel-reader/projects/{project_id}')
    if verify_response.status_code == 200:
        verify_detail = verify_response.json()['data']
        saved_mapping = verify_detail['characterMapping']
        print(f"   API返回的角色映射: {saved_mapping}")
        
        if saved_mapping:
            print("✅ 角色映射验证通过")
        else:
            print("❌ 角色映射验证失败 - API返回空映射")
            return False
    else:
        print("❌ 无法验证角色映射")
        return False
    
    # 直接检查数据库
    print(f"   直接检查数据库...")
    import sqlite3
    conn = sqlite3.connect('data/database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT character_mapping FROM novel_projects WHERE id = ?', (project_id,))
    db_result = cursor.fetchone()
    conn.close()
    
    if db_result and db_result[0] and db_result[0] != '{}':
        db_mapping = json.loads(db_result[0])
        print(f"   数据库中的映射: {db_mapping}")
        print("✅ 数据库验证通过")
    else:
        print("❌ 数据库验证失败 - 映射为空")
        return False
    
    # Step 6: 开始音频生成（关键测试）
    print(f"\n🎤 Step 6: 开始音频生成...")
    
    gen_data = {'parallel_tasks': 1}
    gen_response = requests.post(f'http://localhost:8000/api/novel-reader/projects/{project_id}/start-generation', data=gen_data)
    
    print(f"   响应状态码: {gen_response.status_code}")
    
    if gen_response.status_code == 200:
        result = gen_response.json()
        print("✅ 音频生成启动成功")
        print(f"   总段落: {result['totalSegments']}")
        print(f"   并行任务: {result['parallelTasks']}")
        print("🎉 === 完整流程验证成功！===")
        return True
    else:
        print(f"❌ 音频生成启动失败: {gen_response.status_code}")
        try:
            error_detail = gen_response.json()
            print(f"   错误详情: {error_detail.get('detail', '未知错误')}")
        except:
            print(f"   原始错误: {gen_response.text}")
        
        print("💥 === 验证失败！问题仍然存在 ===")
        return False

if __name__ == "__main__":
    success = final_verification()
    if success:
        print("\n🎊 恭喜！问题真正解决了！")
    else:
        print("\n😞 抱歉，问题仍然存在，需要进一步调试...") 