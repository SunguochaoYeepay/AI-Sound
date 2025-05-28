#!/usr/bin/env python3
"""
检查当前API服务的配置
"""

import requests
import json
import os

def check_environment_variables():
    """检查环境变量"""
    print("🔍 检查环境变量...")
    
    env_vars = [
        "MEGATTS3_URL",
        "ESPNET_URL", 
        "BERTVITS2_URL",
        "DB_HOST",
        "DB_PORT"
    ]
    
    for var in env_vars:
        value = os.environ.get(var, "未设置")
        print(f"  {var}: {value}")

def check_api_config():
    """检查API服务配置"""
    print("\n🔍 检查API服务配置...")
    
    try:
        # 检查系统信息
        response = requests.get('http://localhost:9930/info', timeout=5)
        if response.status_code == 200:
            info = response.json()
            print(f"  应用名称: {info.get('name')}")
            print(f"  版本: {info.get('version')}")
            print(f"  调试模式: {info.get('debug')}")
            print(f"  功能: {', '.join(info.get('features', []))}")
        else:
            print(f"  ❌ 获取系统信息失败: {response.status_code}")
    except Exception as e:
        print(f"  ❌ 连接API失败: {e}")

def check_engine_adapters():
    """检查引擎适配器状态"""
    print("\n🔍 检查引擎适配器状态...")
    
    try:
        response = requests.get('http://localhost:9930/api/engines/stats/summary', timeout=5)
        if response.status_code == 200:
            stats = response.json()
            adapter_stats = stats.get('statistics', {}).get('adapter_stats', {})
            
            print(f"  总适配器: {adapter_stats.get('total_adapters', 0)}")
            print(f"  就绪适配器: {adapter_stats.get('ready_adapters', 0)}")
            print(f"  错误适配器: {adapter_stats.get('error_adapters', 0)}")
            print(f"  支持类型: {adapter_stats.get('supported_types', [])}")
            
            adapters = adapter_stats.get('adapters', {})
            if adapters:
                print("  适配器详情:")
                for name, info in adapters.items():
                    print(f"    - {name}: {info.get('status', 'unknown')} ({info.get('type', 'unknown')})")
            else:
                print("  ⚠️ 没有注册的适配器")
        else:
            print(f"  ❌ 获取适配器状态失败: {response.status_code}")
    except Exception as e:
        print(f"  ❌ 连接API失败: {e}")

def check_espnet_direct():
    """直接检查ESPnet服务"""
    print("\n🔍 直接检查ESPnet服务...")
    
    try:
        response = requests.get('http://localhost:9001/health', timeout=5)
        if response.status_code == 200:
            health = response.json()
            print(f"  ✅ ESPnet服务正常")
            print(f"  状态: {health.get('status')}")
            print(f"  模型已加载: {health.get('model_loaded')}")
            print(f"  服务: {health.get('service')}")
            print(f"  版本: {health.get('version')}")
        else:
            print(f"  ❌ ESPnet服务异常: {response.status_code}")
    except Exception as e:
        print(f"  ❌ 无法连接ESPnet服务: {e}")

def test_api_to_espnet():
    """测试API网关到ESPnet的连接"""
    print("\n🧪 测试API网关到ESPnet的连接...")
    
    try:
        response = requests.post(
            'http://localhost:9930/api/tts/synthesize',
            json={
                "text": "测试连接",
                "voice_id": "espnet_zh_female_001",
                "engine": "espnet"
            },
            timeout=10
        )
        
        print(f"  状态码: {response.status_code}")
        if response.status_code == 200:
            print("  ✅ API网关成功连接到ESPnet！")
        else:
            print(f"  ❌ 连接失败: {response.text}")
    except Exception as e:
        print(f"  ❌ 测试失败: {e}")

if __name__ == "__main__":
    print("🚀 AI-Sound 配置检查")
    print("=" * 50)
    
    check_environment_variables()
    check_api_config()
    check_engine_adapters()
    check_espnet_direct()
    test_api_to_espnet()
    
    print("\n" + "=" * 50)
    print("检查完成！") 