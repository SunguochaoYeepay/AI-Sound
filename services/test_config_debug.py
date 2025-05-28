#!/usr/bin/env python3
"""
调试配置问题
"""

import os
import sys
import requests

# 添加API源码路径
sys.path.append('/app/src')
sys.path.append('api/src')

def test_environment_vars():
    """测试环境变量"""
    print("🔍 检查环境变量...")
    
    vars_to_check = [
        "ESPNET_URL",
        "MEGATTS3_URL", 
        "BERTVITS2_URL"
    ]
    
    for var in vars_to_check:
        value = os.environ.get(var, "未设置")
        print(f"  {var}: {value}")

def test_config_loading():
    """测试配置加载"""
    print("\n🔍 测试配置加载...")
    
    try:
        from api.src.core.config import settings
        print(f"  ESPnet URL: {settings.engines.espnet_url}")
        print(f"  MegaTTS3 URL: {settings.engines.megatts3_url}")
        print(f"  Bert-VITS2 URL: {settings.engines.bertvits2_url}")
    except Exception as e:
        print(f"  ❌ 配置加载失败: {e}")

def test_direct_espnet():
    """直接测试ESPnet"""
    print("\n🔍 直接测试ESPnet服务...")
    
    try:
        response = requests.get('http://localhost:9001/health', timeout=5)
        if response.status_code == 200:
            print("  ✅ ESPnet服务正常")
            health = response.json()
            print(f"  状态: {health.get('status')}")
            print(f"  模型已加载: {health.get('model_loaded')}")
        else:
            print(f"  ❌ ESPnet服务异常: {response.status_code}")
    except Exception as e:
        print(f"  ❌ 无法连接ESPnet: {e}")

def test_docker_network():
    """测试Docker网络连接"""
    print("\n🔍 测试Docker网络连接...")
    
    # 测试容器内部网络
    urls_to_test = [
        "http://espnet-service:9001/health",
        "http://localhost:9001/health"
    ]
    
    for url in urls_to_test:
        try:
            response = requests.get(url, timeout=5)
            print(f"  ✅ {url}: {response.status_code}")
        except Exception as e:
            print(f"  ❌ {url}: {e}")

def test_api_gateway():
    """测试API网关"""
    print("\n🔍 测试API网关...")
    
    try:
        # 检查适配器状态
        response = requests.get('http://localhost:9930/api/engines/stats/summary', timeout=5)
        if response.status_code == 200:
            stats = response.json()
            adapter_stats = stats.get('statistics', {}).get('adapter_stats', {})
            print(f"  总适配器: {adapter_stats.get('total_adapters', 0)}")
            print(f"  就绪适配器: {adapter_stats.get('ready_adapters', 0)}")
            print(f"  支持类型: {adapter_stats.get('supported_types', [])}")
        else:
            print(f"  ❌ 获取适配器状态失败: {response.status_code}")
    except Exception as e:
        print(f"  ❌ API网关连接失败: {e}")

if __name__ == "__main__":
    print("🚀 配置调试")
    print("=" * 50)
    
    test_environment_vars()
    test_config_loading()
    test_direct_espnet()
    test_docker_network()
    test_api_gateway()
    
    print("\n" + "=" * 50)
    print("调试完成！") 