#!/usr/bin/env python3
"""
调试测试脚本 - 检查失败的API端点
"""

import requests
import json

def test_endpoint(url, description):
    """测试单个端点"""
    try:
        print(f"\n测试: {description}")
        print(f"URL: {url}")
        
        response = requests.get(url, timeout=10)
        print(f"状态码: {response.status_code}")
        
        if response.status_code != 200:
            print(f"错误响应: {response.text}")
        else:
            try:
                data = response.json()
                print(f"响应: {json.dumps(data, indent=2, ensure_ascii=False)}")
            except:
                print(f"响应: {response.text}")
                
    except Exception as e:
        print(f"异常: {e}")

def main():
    """主函数"""
    base_url = "http://localhost:9930"
    
    print("=== 调试失败的API端点 ===")
    
    # 失败的端点
    failed_endpoints = [
        ("/api/engines/health", "引擎健康检查"),
        ("/api/voices/", "声音列表"),
        ("/api/characters/", "角色列表"),
        ("/api/tts/engines", "TTS引擎列表"),
        ("/api/voices/test-voice-id/preview", "声音预览"),
    ]
    
    for endpoint, desc in failed_endpoints:
        test_endpoint(f"{base_url}{endpoint}", desc)
    
    print("\n=== 测试系统端点 ===")
    
    # 正常工作的端点
    working_endpoints = [
        ("/health", "系统健康检查"),
        ("/info", "系统信息"),
    ]
    
    for endpoint, desc in working_endpoints:
        test_endpoint(f"{base_url}{endpoint}", desc)

if __name__ == "__main__":
    main() 