#!/usr/bin/env python3
"""
测试角色检测功能
"""
import requests
import json
import time

def test_simple_detection():
    print("🔍 === 测试简单角色检测 ===")
    
    # 测试各种文本内容
    test_cases = [
        {
            "name": "测试1_空文本",
            "text": ""
        },
        {
            "name": "测试2_纯文本",
            "text": "这是一段普通的叙述文字，没有任何对话。"
        },
        {
            "name": "测试3_简单对话",
            "text": "小明说：\"你好世界！\""
        },
        {
            "name": "测试4_多角色对话",
            "text": "小明说：\"你好！\"小红回答：\"很高兴见到你。\"旁白：他们在公园里相遇了。"
        }
    ]
    
    for i, test_case in enumerate(test_cases):
        print(f"\n{'='*50}")
        print(f"🧪 {test_case['name']}")
        print(f"📝 文本内容: {repr(test_case['text'])}")
        
        if not test_case['text'].strip():
            print("⚠️  跳过空文本测试")
            continue
        
        # 创建项目
        timestamp = int(time.time())
        project_data = {
            'name': f'{test_case["name"]}_{timestamp}',
            'description': '角色检测测试',
            'text_content': test_case['text'],
            'character_mapping': '{}'
        }
        
        try:
            # 创建项目
            create_response = requests.post('http://localhost:8000/api/novel-reader/projects', data=project_data)
            
            if create_response.status_code != 200:
                print(f"❌ 项目创建失败: {create_response.status_code}")
                print(create_response.text)
                continue
            
            project = create_response.json()['data']
            project_id = project['id']
            print(f"✅ 项目创建成功: ID={project_id}")
            
            # 获取项目详情
            detail_response = requests.get(f'http://localhost:8000/api/novel-reader/projects/{project_id}')
            
            if detail_response.status_code != 200:
                print(f"❌ 获取详情失败: {detail_response.status_code}")
                continue
            
            detail = detail_response.json()['data']
            segments = detail.get('segments', [])
            
            print(f"📊 分段结果: {len(segments)}个段落")
            
            # 分析角色检测结果
            speakers = {}
            for segment in segments:
                speaker = segment.get('detectedSpeaker', '未知')
                speakers[speaker] = speakers.get(speaker, 0) + 1
                print(f"  段落{segment['segmentOrder']}: \"{segment['textContent']}\" -> {speaker}")
            
            print(f"🎭 检测到的角色:")
            for speaker, count in speakers.items():
                print(f"  {speaker}: {count}个段落")
            
            # 模拟前端逻辑
            print(f"🔍 前端角色识别逻辑:")
            character_set = set()
            for speaker in speakers.keys():
                if speaker and speaker not in ['narrator', '旁白']:
                    character_set.add(speaker)
            
            print(f"  非旁白角色: {list(character_set)}")
            
            narrator_count = sum([count for speaker, count in speakers.items() if speaker in ['narrator', '旁白']])
            print(f"  旁白段落数: {narrator_count}")
            
            final_characters = list(character_set)
            if narrator_count > 0:
                final_characters.insert(0, '旁白')
            
            print(f"  最终角色列表: {final_characters}")
            
            if len(final_characters) == 0:
                print(f"❌ 无角色识别结果")
            else:
                print(f"✅ 识别成功，共{len(final_characters)}个角色")
            
        except Exception as e:
            print(f"❌ 测试失败: {e}")

if __name__ == "__main__":
    test_simple_detection() 