#!/usr/bin/env python3
"""
测试改进后的角色识别功能
"""
import sys
import os
import requests
import json
sys.path.append('app')

BASE_URL = "http://localhost:8000"

def test_character_detection():
    print("🔍 === 测试改进后的角色识别功能 ===")
    
    # 测试文本，包含多种对话模式
    test_text = """
    李明说："今天天气真好啊！"
    
    王小花回答道："是的，我们去公园散步吧。"
    
    张老师："同学们，今天我们学习新课程。"
    
    "好的老师！"学生们异口同声地说。
    
    旁白：天空中飞过一群大雁。
    
    小红想到：我应该早点回家。
    
    "真是太棒了！"小明兴奋地叫道。
    """
    
    # 1. 创建新项目
    print("\n📝 Step 1: 创建测试项目...")
    try:
        form_data = {
            'name': 'character_test_project',
            'description': '角色识别测试项目',
            'text_content': test_text.strip(),
            'character_mapping': '{}'
        }
        
        response = requests.post(f"{BASE_URL}/api/novel-reader/projects", data=form_data)
        print(f"   状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                project_id = data['data']['id']
                print(f"   ✅ 项目创建成功，ID: {project_id}")
                
                # 2. 获取项目详情，检查角色识别结果
                print(f"\n🔍 Step 2: 检查角色识别结果...")
                
                detail_response = requests.get(f"{BASE_URL}/api/novel-reader/projects/{project_id}")
                if detail_response.status_code == 200:
                    detail_data = detail_response.json()
                    if detail_data.get('success'):
                        project = detail_data['data']
                        segments = project.get('segments', [])
                        
                        print(f"   📊 段落总数: {len(segments)}")
                        
                        # 统计识别出的角色
                        speakers = {}
                        for segment in segments:
                            speaker = segment.get('speaker', '未知')
                            speakers[speaker] = speakers.get(speaker, 0) + 1
                        
                        print(f"   🎭 识别出的角色:")
                        for speaker, count in speakers.items():
                            print(f"      {speaker}: {count}个段落")
                        
                        # 显示前几个段落的详细信息
                        print(f"\n📋 前5个段落详情:")
                        for i, segment in enumerate(segments[:5]):
                            print(f"   段落{segment['segment_order']}: '{segment['text_content'][:30]}...' -> 发言人: {segment['speaker']}")
                        
                        if len(speakers) > 1:
                            print(f"   ✅ 角色识别成功！识别出 {len(speakers)} 个角色")
                        else:
                            print(f"   ❌ 角色识别失败，只识别出旁白")
                    else:
                        print(f"   ❌ 获取项目详情失败: {detail_data.get('message')}")
                else:
                    print(f"   ❌ 获取项目详情失败: {detail_response.status_code}")
            else:
                print(f"   ❌ 项目创建失败: {data.get('message')}")
        else:
            print(f"   ❌ 项目创建失败: {response.status_code}")
            print(f"   响应: {response.text}")
            
    except Exception as e:
        print(f"   ❌ 测试异常: {e}")

if __name__ == "__main__":
    test_character_detection() 