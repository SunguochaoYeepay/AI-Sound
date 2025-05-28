#!/usr/bin/env python3
"""
重新构建API服务以应用配置修复
"""

import os
import time
import requests

def main():
    print("🚀 重新构建API服务以应用配置修复...")
    print("=" * 50)
    
    # 停止API服务
    print("🔄 停止API服务...")
    os.system("docker-compose stop api")
    time.sleep(3)
    
    # 重新构建API服务
    print("🔄 重新构建API服务...")
    os.system("docker-compose build api")
    
    # 启动API服务
    print("🔄 启动API服务...")
    os.system("docker-compose up -d api")
    
    # 等待服务启动
    print("⏳ 等待20秒让服务启动...")
    time.sleep(20)
    
    # 测试API服务
    print("🧪 测试API服务...")
    for i in range(5):
        try:
            response = requests.get('http://localhost:9930/health', timeout=10)
            if response.status_code == 200:
                print("✅ API服务启动成功！")
                break
        except Exception as e:
            print(f"⏳ 等待中... ({i+1}/5): {e}")
            time.sleep(5)
    else:
        print("❌ API服务启动超时")
        return
    
    # 检查适配器状态
    print("\n🧪 检查适配器状态...")
    try:
        response = requests.get('http://localhost:9930/api/engines/stats/summary', timeout=10)
        if response.status_code == 200:
            stats = response.json()
            adapter_stats = stats.get('statistics', {}).get('adapter_stats', {})
            print(f"总适配器: {adapter_stats.get('total_adapters', 0)}")
            print(f"就绪适配器: {adapter_stats.get('ready_adapters', 0)}")
            print(f"支持类型: {adapter_stats.get('supported_types', [])}")
            
            adapters = adapter_stats.get('adapters', {})
            if adapters:
                print("适配器详情:")
                for name, info in adapters.items():
                    print(f"  - {name}: {info.get('status', 'unknown')}")
        else:
            print(f"❌ 获取适配器状态失败: {response.status_code}")
    except Exception as e:
        print(f"❌ 检查适配器失败: {e}")
    
    # 测试ESPnet连接
    print("\n🧪 测试ESPnet连接...")
    try:
        response = requests.post(
            'http://localhost:9930/api/tts/synthesize',
            json={
                "text": "老爹，ESPnet集成测试成功！",
                "voice_id": "espnet_zh_female_001",
                "engine": "espnet"
            },
            timeout=15
        )
        
        print(f"状态码: {response.status_code}")
        if response.status_code == 200:
            print("🎉 ESPnet集成成功！")
        else:
            print(f"❌ ESPnet连接失败: {response.text}")
    except Exception as e:
        print(f"❌ ESPnet测试失败: {e}")

if __name__ == "__main__":
    main() 