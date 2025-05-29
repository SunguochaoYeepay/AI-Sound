#!/usr/bin/env python3
"""
测试修复后的API接口
"""

import requests
import json
import sys

BASE_URL = "http://127.0.0.1:9930"

def test_api_endpoint(method, url, description):
    """测试API端点"""
    full_url = f"{BASE_URL}{url}"
    print(f"测试: {method} {url} - {description}")
    
    try:
        if method == "GET":
            response = requests.get(full_url, timeout=10)
        elif method == "POST":
            response = requests.post(full_url, timeout=10)
        else:
            print(f"  ❌ 不支持的方法: {method}")
            return False
        
        print(f"  状态码: {response.status_code}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"  ✅ 成功")
                if isinstance(data, dict) and 'data' in data:
                    print(f"  数据: {json.dumps(data['data'], ensure_ascii=False, indent=2)[:200]}...")
                return True
            except:
                print(f"  ⚠️ 成功但响应不是JSON")
                return True
        else:
            try:
                error_data = response.json()
                print(f"  ❌ 失败: {error_data}")
            except:
                print(f"  ❌ 失败: {response.text}")
            return False
            
    except Exception as e:
        print(f"  ❌ 连接失败: {e}")
        return False

def main():
    """主函数"""
    print("🔍 测试修复后的API接口...")
    print("=" * 50)
    
    # 之前失败的接口
    failed_endpoints = [
        ("GET", "/api/engines/health", "所有引擎健康检查"),
        ("GET", "/api/voices/", "声音列表"),
        ("GET", "/api/tts/engines", "TTS引擎列表"),
        ("GET", "/api/voices/test-voice-id/preview", "声音预览")
    ]
    
    # 额外测试一些其他接口
    additional_endpoints = [
        ("GET", "/health", "系统健康检查"),
        ("GET", "/api/engines/", "引擎列表"),
        ("GET", "/api/characters/", "角色列表"),
        ("GET", "/api/tts/formats", "支持的音频格式")
    ]
    
    all_endpoints = failed_endpoints + additional_endpoints
    
    success_count = 0
    total_count = len(all_endpoints)
    
    for method, url, description in all_endpoints:
        success = test_api_endpoint(method, url, description)
        if success:
            success_count += 1
        print()
    
    print("=" * 50)
    print(f"📊 测试结果: {success_count}/{total_count} ({success_count/total_count*100:.1f}%) 成功")
    
    if success_count == total_count:
        print("🎉 所有接口测试通过！")
        return 0
    else:
        print("⚠️ 仍有接口需要修复")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 