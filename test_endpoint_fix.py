#!/usr/bin/env python3
"""
测试端点修复效果
"""
import requests

def test_endpoints():
    print("🔍 === 测试MegaTTS3端点 ===")
    
    base_url = "http://localhost:7929"
    
    # 测试各个端点
    endpoints_to_test = [
        "/health",
        "/api/v1/info", 
        "/api/v1/tts/synthesize",
        "/synthesize"  # 旧的错误端点
    ]
    
    for endpoint in endpoints_to_test:
        url = f"{base_url}{endpoint}"
        print(f"\n测试端点: {url}")
        
        try:
            if endpoint == "/health" or endpoint == "/api/v1/info":
                response = requests.get(url, timeout=5)
            else:
                # 对TTS端点进行简单的POST测试
                response = requests.post(url, json={"test": "data"}, timeout=5)
                
            print(f"  状态码: {response.status_code}")
            
            if response.status_code == 200:
                print("  ✅ 端点可访问")
                try:
                    data = response.json()
                    print(f"  响应: {data}")
                except:
                    print("  响应: 非JSON格式")
            elif response.status_code == 404:
                print("  ❌ 端点不存在")
            elif response.status_code == 400:
                print("  ⚠️  端点存在但参数错误（这是好事！）")
            else:
                print(f"  ⚠️  其他状态: {response.status_code}")
                
        except requests.exceptions.ConnectionError:
            print("  ❌ 连接失败")
        except Exception as e:
            print(f"  ❌ 错误: {e}")

if __name__ == "__main__":
    test_endpoints() 