#!/usr/bin/env python3
"""
测试Docker网络连接
"""

import requests
import time

def test_direct_connection():
    """测试直接连接"""
    print("🔍 测试直接连接到ESPnet...")
    try:
        response = requests.get('http://localhost:9001/health', timeout=5)
        print(f"✅ 直接连接成功: {response.status_code}")
        print(f"响应: {response.json()}")
        return True
    except Exception as e:
        print(f"❌ 直接连接失败: {e}")
        return False

def test_host_gateway():
    """测试通过host.docker.internal连接"""
    print("\n🔍 测试通过host.docker.internal连接...")
    try:
        response = requests.get('http://host.docker.internal:9001/health', timeout=5)
        print(f"✅ host.docker.internal连接成功: {response.status_code}")
        print(f"响应: {response.json()}")
        return True
    except Exception as e:
        print(f"❌ host.docker.internal连接失败: {e}")
        return False

def test_api_gateway():
    """测试API网关"""
    print("\n🔍 测试API网关...")
    try:
        response = requests.get('http://localhost:9930/api/engines/stats/summary', timeout=5)
        print(f"✅ API网关连接成功: {response.status_code}")
        result = response.json()
        print(f"适配器统计: {result.get('statistics', {}).get('adapter_stats', {})}")
        return True
    except Exception as e:
        print(f"❌ API网关连接失败: {e}")
        return False

if __name__ == "__main__":
    print("🚀 开始网络连接测试...")
    print("=" * 50)
    
    test_direct_connection()
    test_host_gateway()
    test_api_gateway()
    
    print("\n🔄 等待5秒后重新测试API网关...")
    time.sleep(5)
    test_api_gateway() 