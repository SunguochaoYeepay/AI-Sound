#!/usr/bin/env python3
"""
测试创建项目API
"""
import requests
import json
import datetime

def test_create_project():
    print("=== 测试创建项目API ===")
    
    try:
        url = "http://localhost:8000/api/novel-reader/projects"
        
        # 生成带时间戳的项目名称
        timestamp = datetime.datetime.now().strftime("%m%d-%H%M%S")
        project_name = f"测试项目_{timestamp}"
        
        # 测试数据
        data = {
            "name": project_name,
            "description": "这是一个测试项目",
            "text_content": "小明说：\"你好，世界！\"小红回答：\"你好！\"旁白：两人愉快地聊着天。",
            "character_mapping": "{}"
        }
        
        print(f"请求URL: {url}")
        print(f"请求数据: {data}")
        
        # 发送POST请求
        response = requests.post(url, data=data)
        
        print(f"状态码: {response.status_code}")
        print(f"响应头: {dict(response.headers)}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 创建成功: {json.dumps(result, indent=2, ensure_ascii=False)}")
            
            # 获取项目详情查看分段
            project_id = result['data']['id']
            detail_url = f"http://localhost:8000/api/novel-reader/projects/{project_id}"
            detail_response = requests.get(detail_url)
            
            if detail_response.status_code == 200:
                detail_result = detail_response.json()
                print(f"\n=== 项目详情 ===")
                print(f"总段落数: {detail_result['data']['totalSegments']}")
                print(f"段落列表: {len(detail_result['data']['segments'])} 个段落")
                
                for i, segment in enumerate(detail_result['data']['segments'][:5]):  # 只显示前5个
                    print(f"段落 {i+1}: {segment['textContent'][:50]}... (说话人: {segment['detectedSpeaker']})")
            else:
                print(f"获取详情失败: {detail_response.text}")
                
        else:
            print(f"❌ 创建失败")
            print(f"错误响应: {response.text}")
            
            # 尝试解析JSON错误信息
            try:
                error_json = response.json()
                print(f"错误详情: {json.dumps(error_json, indent=2, ensure_ascii=False)}")
            except:
                print("无法解析错误JSON")
                
    except Exception as e:
        print(f"❌ 请求异常: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_create_project() 