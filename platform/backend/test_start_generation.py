#!/usr/bin/env python3
"""
测试音频生成开始功能
"""
import requests
import json

def test_start_generation():
    project_id = 16
    
    print(f"=== 测试项目 {project_id} 开始音频生成 ===")
    
    # 1. 先验证角色映射
    print("1. 验证角色映射...")
    detail_response = requests.get(f'http://localhost:8000/api/novel-reader/projects/{project_id}')
    
    if detail_response.status_code != 200:
        print(f"❌ 获取项目详情失败: {detail_response.status_code}")
        return
    
    detail = detail_response.json()['data']
    print(f"✅ 项目名称: {detail['name']}")
    print(f"角色映射: {detail['characterMapping']}")
    print(f"段落数量: {len(detail.get('segments', []))}")
    
    if not detail['characterMapping']:
        print("❌ 角色映射为空，无法开始生成")
        return
    
    print("✅ 角色映射验证通过")
    
    # 2. 开始音频生成
    print("\n2. 开始音频生成...")
    gen_data = {'parallel_tasks': 1}
    
    gen_response = requests.post(f'http://localhost:8000/api/novel-reader/projects/{project_id}/start-generation', data=gen_data)
    
    print(f"响应状态码: {gen_response.status_code}")
    
    if gen_response.status_code == 200:
        print("✅ 音频生成开始成功")
        result = gen_response.json()
        print(f"响应: {json.dumps(result, indent=2, ensure_ascii=False)}")
        print("🎉 测试完全成功!")
    else:
        print(f"❌ 音频生成失败: {gen_response.status_code}")
        print(f"错误响应: {gen_response.text}")
        
        # 尝试解析错误信息
        try:
            error_data = gen_response.json()
            print(f"错误详情: {error_data.get('detail', '未知错误')}")
        except:
            print("无法解析错误响应")

if __name__ == "__main__":
    test_start_generation() 