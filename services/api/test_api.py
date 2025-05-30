#!/usr/bin/env python3
"""
测试API服务
"""

import requests
import time
import json

def test_api():
    """测试API服务是否正常工作"""
    base_url = "http://127.0.0.1:9931"
    
    print("=== 测试API服务 ===")
    
    # 1. 测试健康检查
    try:
        print("1. 测试健康检查...")
        response = requests.get(f"{base_url}/api/health", timeout=5)
        if response.status_code == 200:
            print("   ✅ 健康检查通过")
            print(f"   响应: {response.json()}")
        else:
            print(f"   ❌ 健康检查失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ 健康检查异常: {e}")
        return False
    
    # 2. 测试声音列表
    try:
        print("2. 测试声音列表...")
        response = requests.get(f"{base_url}/api/voices/", timeout=10)
        if response.status_code == 200:
            data = response.json()
            voices = data.get("data", {}).get("voices", [])
            print(f"   ✅ 获取到 {len(voices)} 个声音")
            if voices:
                print(f"   第一个声音: {voices[0]['id']} - {voices[0]['name']}")
                return voices[0]['id']  # 返回第一个声音ID用于测试预览
        else:
            print(f"   ❌ 获取声音列表失败: {response.status_code}")
            print(f"   错误内容: {response.text}")
    except Exception as e:
        print(f"   ❌ 声音列表异常: {e}")
    
    return None

def test_preview(voice_id):
    """测试声音预览"""
    if not voice_id:
        return
        
    base_url = "http://127.0.0.1:9931"
    
    print(f"3. 测试声音预览 ({voice_id})...")
    try:
        response = requests.get(
            f"{base_url}/api/voices/{voice_id}/preview",
            params={"text": "测试预览"},
            timeout=30
        )
        if response.status_code == 200:
            print("   ✅ 声音预览成功")
            print(f"   响应: {response.json()}")
        else:
            print(f"   ❌ 声音预览失败: {response.status_code}")
            print(f"   错误内容: {response.text}")
    except Exception as e:
        print(f"   ❌ 声音预览异常: {e}")

if __name__ == "__main__":
    # 等待服务启动
    print("等待服务启动...")
    time.sleep(3)
    
    voice_id = test_api()
    test_preview(voice_id) 