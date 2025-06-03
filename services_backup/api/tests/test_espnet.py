#!/usr/bin/env python3
"""
测试ESPnet引擎
"""

import requests
import json

def test_espnet_engine():
    """测试ESPnet引擎"""
    
    print("🧪 测试ESPnet引擎...")
    print("=" * 50)
    
    # 测试请求
    test_request = {
        "text": "你好，这是ESPnet引擎测试",
        "voice_id": "test_voice", 
        "engine": "espnet"
    }
    
    try:
        print(f"📋 发送请求: {test_request}")
        response = requests.post(
            'http://localhost:9930/api/tts/synthesize', 
            json=test_request,
            timeout=30
        )
        
        print(f"📊 状态码: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ 成功!")
            result = response.json()
            print(f"📄 响应: {json.dumps(result, indent=2, ensure_ascii=False)}")
        else:
            print("❌ 失败!")
            print(f"📄 错误响应: {response.text}")
            
    except requests.exceptions.Timeout:
        print("⏰ 请求超时")
    except requests.exceptions.ConnectionError:
        print("🔌 连接错误")
    except Exception as e:
        print(f"💥 异常: {e}")

def test_bert_vits2_engine():
    """测试Bert-VITS2引擎"""
    
    print("\n🧪 测试Bert-VITS2引擎...")
    print("=" * 50)
    
    # 测试请求
    test_request = {
        "text": "你好，这是Bert-VITS2引擎测试",
        "voice_id": "test_voice",
        "engine": "bert_vits2"
    }
    
    try:
        print(f"📋 发送请求: {test_request}")
        response = requests.post(
            'http://localhost:9930/api/tts/synthesize', 
            json=test_request,
            timeout=30
        )
        
        print(f"📊 状态码: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ 成功!")
            result = response.json()
            print(f"📄 响应: {json.dumps(result, indent=2, ensure_ascii=False)}")
        else:
            print("❌ 失败!")
            print(f"📄 错误响应: {response.text}")
            
    except requests.exceptions.Timeout:
        print("⏰ 请求超时")
    except requests.exceptions.ConnectionError:
        print("🔌 连接错误")
    except Exception as e:
        print(f"💥 异常: {e}")

def check_engine_status():
    """检查引擎状态"""
    
    print("\n🔍 检查引擎状态...")
    print("=" * 50)
    
    try:
        # 检查可用引擎
        response = requests.get('http://localhost:9930/api/tts/engines')
        print(f"📊 可用引擎: {response.json()}")
        
        # 检查引擎统计
        response = requests.get('http://localhost:9930/api/engines/stats/summary')
        stats = response.json()
        
        print(f"📈 适配器统计:")
        adapter_stats = stats.get('statistics', {}).get('adapter_stats', {})
        print(f"  - 总适配器: {adapter_stats.get('total_adapters', 0)}")
        print(f"  - 就绪适配器: {adapter_stats.get('ready_adapters', 0)}")
        print(f"  - 错误适配器: {adapter_stats.get('error_adapters', 0)}")
        print(f"  - 支持类型: {adapter_stats.get('supported_types', [])}")
        
        adapters = adapter_stats.get('adapters', {})
        if adapters:
            print(f"📋 适配器详情:")
            for name, info in adapters.items():
                print(f"  - {name}: {info.get('status', 'unknown')} ({info.get('type', 'unknown')})")
        
    except Exception as e:
        print(f"💥 检查失败: {e}")

if __name__ == "__main__":
    # 先检查引擎状态
    check_engine_status()
    
    # 测试ESPnet引擎
    test_espnet_engine()
    
    # 测试Bert-VITS2引擎
    test_bert_vits2_engine() 