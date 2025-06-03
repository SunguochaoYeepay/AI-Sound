#!/usr/bin/env python3
"""
简单的API健康检查测试脚本
"""

import requests
import json

def test_endpoints():
    """测试各个端点"""
    base_url = "http://localhost:9930"
    
    endpoints = [
        "/health",
        "/api/health", 
        "/api/tts/megatts3/health",
        "/docs"
    ]
    
    print("🔍 测试API端点...")
    print(f"基础URL: {base_url}")
    print("-" * 50)
    
    for endpoint in endpoints:
        full_url = f"{base_url}{endpoint}"
        try:
            print(f"测试: {endpoint}")
            response = requests.get(full_url, timeout=5)
            
            if response.status_code == 200:
                print(f"✅ {endpoint} - 200 OK")
                if endpoint != "/docs":
                    try:
                        data = response.json()
                        print(f"   📄 响应: {json.dumps(data, ensure_ascii=False, indent=2)[:200]}...")
                    except:
                        print(f"   📄 响应: {response.text[:100]}...")
            else:
                print(f"❌ {endpoint} - {response.status_code}")
                print(f"   📄 错误: {response.text[:100]}")
                
        except requests.exceptions.ConnectionError:
            print(f"🔴 {endpoint} - 连接失败 (服务可能未启动)")
        except requests.exceptions.Timeout:
            print(f"⏰ {endpoint} - 请求超时")
        except Exception as e:
            print(f"❌ {endpoint} - 错误: {e}")
        
        print()

if __name__ == "__main__":
    test_endpoints() 