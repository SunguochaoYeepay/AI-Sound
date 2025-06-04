#!/usr/bin/env python3
"""
验证CORS配置
模拟浏览器发送预检请求
"""
import requests

def verify_cors():
    base_url = "http://soundapi.cpolar.top"
    
    print("🔍 === 验证CORS配置 ===")
    
    # 1. 测试简单请求
    print("\n1. 测试简单GET请求...")
    try:
        response = requests.get(f"{base_url}/api/characters")
        print(f"   状态码: {response.status_code}")
        print(f"   CORS头信息:")
        cors_headers = {k: v for k, v in response.headers.items() if 'access-control' in k.lower()}
        for header, value in cors_headers.items():
            print(f"     {header}: {value}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ 获取到 {len(data.get('data', []))} 个声音档案")
        else:
            print(f"   ❌ 请求失败")
            
    except Exception as e:
        print(f"   ❌ 异常: {str(e)}")
    
    # 2. 测试预检请求 (OPTIONS)
    print("\n2. 测试OPTIONS预检请求...")
    try:
        headers = {
            'Origin': 'http://localhost:3000',
            'Access-Control-Request-Method': 'POST',
            'Access-Control-Request-Headers': 'Content-Type'
        }
        
        response = requests.options(f"{base_url}/api/characters", headers=headers)
        print(f"   状态码: {response.status_code}")
        print(f"   CORS头信息:")
        cors_headers = {k: v for k, v in response.headers.items() if 'access-control' in k.lower()}
        for header, value in cors_headers.items():
            print(f"     {header}: {value}")
            
        if response.status_code in [200, 204]:
            print(f"   ✅ 预检请求成功")
        else:
            print(f"   ❌ 预检请求失败")
            
    except Exception as e:
        print(f"   ❌ 异常: {str(e)}")
    
    # 3. 测试通用OPTIONS处理器
    print("\n3. 测试通用OPTIONS处理器...")
    try:
        response = requests.options(f"{base_url}/test/path")
        print(f"   状态码: {response.status_code}")
        if response.status_code == 200:
            print(f"   ✅ 通用OPTIONS处理器工作正常")
        else:
            print(f"   ❌ 通用OPTIONS处理器异常")
    except Exception as e:
        print(f"   ❌ 异常: {str(e)}")
    
    print("\n🎯 === 验证完成 ===")
    print("如果以上测试都通过，CORS配置应该正常工作")

if __name__ == "__main__":
    verify_cors() 