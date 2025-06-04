#!/usr/bin/env python3
"""
测试外网API连接
验证 soundapi.cpolar.top 是否可用
"""
import requests
import json

def test_api_connection():
    base_url = "http://soundapi.cpolar.top"
    
    print("🌐 === 测试外网API连接 ===")
    print(f"目标地址: {base_url}")
    
    try:
        # 1. 基础健康检查
        print("\n1. 测试基础连接...")
        response = requests.get(f"{base_url}/", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print("✅ 基础连接成功")
            print(f"   API名称: {data.get('name')}")
            print(f"   版本: {data.get('version')}")
            print(f"   状态: {data.get('status')}")
            print(f"   时间戳: {data.get('timestamp')}")
        else:
            print(f"❌ 连接失败: HTTP {response.status_code}")
            return False
        
        # 2. 健康检查接口
        print("\n2. 测试健康检查...")
        health_response = requests.get(f"{base_url}/health", timeout=10)
        
        if health_response.status_code == 200:
            health_data = health_response.json()
            print("✅ 健康检查成功")
            print(f"   状态: {health_data.get('status')}")
            print(f"   服务: {health_data.get('services', {})}")
        else:
            print(f"⚠️ 健康检查失败: HTTP {health_response.status_code}")
        
        # 3. 测试声音库接口
        print("\n3. 测试声音库接口...")
        chars_response = requests.get(f"{base_url}/api/characters", timeout=10)
        
        if chars_response.status_code == 200:
            chars_data = chars_response.json()
            print("✅ 声音库接口可用")
            print(f"   声音档案数量: {len(chars_data.get('data', []))}")
        else:
            print(f"⚠️ 声音库接口异常: HTTP {chars_response.status_code}")
        
        # 4. 测试朗读项目接口
        print("\n4. 测试朗读项目接口...")
        projects_response = requests.get(f"{base_url}/api/novel-reader/projects", timeout=10)
        
        if projects_response.status_code == 200:
            projects_data = projects_response.json()
            print("✅ 朗读项目接口可用")
            print(f"   项目数量: {len(projects_data.get('data', []))}")
        else:
            print(f"⚠️ 朗读项目接口异常: HTTP {projects_response.status_code}")
        
        print("\n🎉 === API连接测试完成 ===")
        print("前端现在可以使用外网域名访问后端API了！")
        return True
        
    except requests.exceptions.Timeout:
        print("❌ 连接超时，请检查网络或cpolar隧道状态")
        return False
    except requests.exceptions.ConnectionError:
        print("❌ 连接错误，请确认cpolar隧道正在运行")
        return False
    except Exception as e:
        print(f"❌ 测试异常: {str(e)}")
        return False

if __name__ == "__main__":
    test_api_connection() 