#!/usr/bin/env python3
"""
调试项目创建问题
"""
import requests
import json
import time

def test_create_project():
    print("=== 调试项目创建API ===")
    
    # 测试数据
    test_data = {
        'name': f'调试项目_{int(time.time())}',
        'description': '调试用项目',
        'text_content': '小明说："你好！"小红回答："好的。"旁白：两人聊了一会。',
        'character_mapping': '{}'
    }
    
    try:
        print(f"发送请求到: http://localhost:8000/api/novel-reader/projects")
        print(f"请求数据: {test_data}")
        
        # 发送POST请求
        response = requests.post(
            'http://localhost:8000/api/novel-reader/projects',
            data=test_data
        )
        
        print(f"状态码: {response.status_code}")
        print(f"响应头: {dict(response.headers)}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 创建成功")
            print(f"响应: {json.dumps(result, indent=2, ensure_ascii=False)}")
            
            project_id = result['data']['id']
            
            # 立即获取项目详情
            detail_response = requests.get(f'http://localhost:8000/api/novel-reader/projects/{project_id}')
            if detail_response.status_code == 200:
                detail = detail_response.json()
                print(f"\n=== 项目详情 ===")
                print(f"项目ID: {project_id}")
                print(f"项目名称: {detail['data']['name']}")
                print(f"段落数量: {len(detail['data']['segments'])}")
                for segment in detail['data']['segments']:
                    print(f"  段落 {segment['segmentOrder']}: {segment['textContent'][:30]}... (说话人: {segment['detectedSpeaker']})")
                
                # 测试设置角色映射
                print(f"\n=== 测试角色映射 ===")
                
                # 获取可用声音
                voices_response = requests.get('http://localhost:8000/api/characters/')
                if voices_response.status_code == 200:
                    voices = voices_response.json()['data']
                    if voices:
                        voice_id = voices[0]['id']
                        voice_name = voices[0]['name']
                        
                        # 设置角色映射
                        update_data = {
                            'name': detail['data']['name'],
                            'description': detail['data']['description'],
                            'character_mapping': json.dumps({"旁白": voice_id, "小明": voice_id, "小红": voice_id})
                        }
                        
                        update_response = requests.put(f'http://localhost:8000/api/novel-reader/projects/{project_id}', data=update_data)
                        if update_response.status_code == 200:
                            print(f"✅ 角色映射设置成功")
                            
                            # 尝试开始生成
                            gen_data = {'parallel_tasks': 1}
                            gen_response = requests.post(f'http://localhost:8000/api/novel-reader/projects/{project_id}/start-generation', data=gen_data)
                            
                            if gen_response.status_code == 200:
                                print(f"✅ 音频生成开始成功")
                                print(f"生成响应: {json.dumps(gen_response.json(), indent=2, ensure_ascii=False)}")
                            else:
                                print(f"❌ 音频生成失败: {gen_response.status_code}")
                                print(f"错误: {gen_response.text}")
                        else:
                            print(f"❌ 角色映射设置失败: {update_response.status_code}")
                            print(f"错误: {update_response.text}")
                    else:
                        print("❌ 没有可用的声音档案")
                else:
                    print(f"❌ 获取声音档案失败: {voices_response.status_code}")
            else:
                print(f"❌ 获取项目详情失败: {detail_response.status_code}")
        else:
            print(f"❌ 创建失败: {response.status_code}")
            print(f"错误响应: {response.text}")
            
    except Exception as e:
        print(f"❌ 测试异常: {e}")

if __name__ == "__main__":
    test_create_project() 