#!/usr/bin/env python3
"""
直接测试ESPnet服务API
"""

import urllib.request
import urllib.error
import json
import tempfile

def test_espnet_api():
    """测试ESPnet API端点"""
    base_url = "http://127.0.0.1:9001"
    
    print("🔍 ESPnet服务直接测试")
    print("=" * 50)
    
    # 1. 测试健康检查
    print("1️⃣ 测试健康检查 /health")
    try:
        req = urllib.request.Request(f"{base_url}/health")
        with urllib.request.urlopen(req, timeout=10) as response:
            health_data = json.loads(response.read().decode())
            print(f"   ✅ 健康检查成功: {health_data}")
            model_loaded = health_data.get('model_loaded', False)
            print(f"   🧠 模型状态: {'已加载' if model_loaded else '未加载'}")
    except Exception as e:
        print(f"   ❌ 健康检查失败: {e}")
        return False
    
    # 2. 测试声音列表
    print("\n2️⃣ 测试声音列表 /voices")
    try:
        req = urllib.request.Request(f"{base_url}/voices")
        with urllib.request.urlopen(req, timeout=10) as response:
            voices_data = json.loads(response.read().decode())
            print(f"   ✅ 声音列表获取成功: {voices_data}")
            voices = voices_data.get('voices', [])
            print(f"   🎵 可用声音数量: {len(voices)}")
            for voice in voices:
                print(f"      - {voice.get('id', 'unknown')}: {voice.get('name', 'unknown')}")
    except Exception as e:
        print(f"   ❌ 声音列表获取失败: {e}")
    
    # 3. 测试语音合成
    print("\n3️⃣ 测试语音合成 /synthesize")
    try:
        synthesis_data = {
            "text": "这是ESPnet语音合成测试",
            "speaker": "espnet_zh_female_001",
            "speed": 1.0,
            "volume": 1.0,
            "sample_rate": 24000,
            "format": "wav"
        }
        
        json_data = json.dumps(synthesis_data).encode('utf-8')
        req = urllib.request.Request(
            f"{base_url}/synthesize",
            data=json_data,
            headers={'Content-Type': 'application/json'},
            method='POST'
        )
        
        print(f"   📤 发送合成请求: {synthesis_data}")
        
        with urllib.request.urlopen(req, timeout=30) as response:
            content_type = response.headers.get('Content-Type', '')
            content_length = len(response.read())
            
            print(f"   ✅ 合成请求成功!")
            print(f"   📄 响应类型: {content_type}")
            print(f"   📊 响应大小: {content_length} bytes")
            
            if 'audio' in content_type:
                print("   🎵 返回了音频文件 - ESPnet工作正常!")
                return True
            elif 'json' in content_type:
                # 可能是JSON响应（包含文件路径或错误）
                response_data = json.loads(response.read().decode())
                print(f"   📄 JSON响应: {response_data}")
                if response_data.get('success'):
                    print("   ✅ 合成成功!")
                    return True
                else:
                    print(f"   ❌ 合成失败: {response_data.get('error', 'unknown')}")
                    return False
            else:
                print(f"   ⚠️ 未知响应类型: {content_type}")
                return False
                
    except urllib.error.HTTPError as e:
        error_content = e.read().decode() if hasattr(e, 'read') else str(e)
        print(f"   ❌ 合成请求失败 (HTTP {e.code}): {error_content}")
        return False
    except Exception as e:
        print(f"   ❌ 合成请求失败: {e}")
        return False
    
    print("=" * 50)

if __name__ == "__main__":
    test_espnet_api() 