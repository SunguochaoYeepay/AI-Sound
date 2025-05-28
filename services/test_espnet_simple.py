#!/usr/bin/env python3
"""
简单的ESPnet服务测试
"""

import requests
import json

def test_espnet_health():
    """测试ESPnet健康检查"""
    try:
        print("🔍 测试ESPnet健康检查...")
        response = requests.get('http://localhost:9001/health', timeout=5)
        print(f"状态码: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"响应: {json.dumps(result, indent=2, ensure_ascii=False)}")
            return True
        else:
            print(f"错误: {response.text}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ 连接失败 - ESPnet服务可能未启动")
        return False
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

def test_espnet_info():
    """测试ESPnet信息端点"""
    try:
        print("\n🔍 测试ESPnet信息端点...")
        response = requests.get('http://localhost:9001/info', timeout=5)
        print(f"状态码: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"响应: {json.dumps(result, indent=2, ensure_ascii=False)}")
            return True
        else:
            print(f"错误: {response.text}")
            return False
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

def test_espnet_voices():
    """测试ESPnet声音列表"""
    try:
        print("\n🔍 测试ESPnet声音列表...")
        response = requests.get('http://localhost:9001/voices', timeout=5)
        print(f"状态码: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"响应: {json.dumps(result, indent=2, ensure_ascii=False)}")
            return True
        else:
            print(f"错误: {response.text}")
            return False
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

if __name__ == "__main__":
    print("🚀 开始测试ESPnet服务...")
    print("=" * 50)
    
    # 测试健康检查
    health_ok = test_espnet_health()
    
    if health_ok:
        # 测试其他端点
        test_espnet_info()
        test_espnet_voices()
        
        print("\n✅ ESPnet服务基本功能正常！")
    else:
        print("\n❌ ESPnet服务不可用") 