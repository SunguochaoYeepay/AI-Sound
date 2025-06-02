#!/usr/bin/env python3
"""
验证AI-Sound系统与TTS引擎的完整对接
"""

import urllib.request
import urllib.error
import json

def test_ai_sound_integration():
    """测试AI-Sound系统完整集成"""
    
    print("🔥 AI-Sound系统引擎对接验证")
    print("=" * 60)
    
    # 1. 检查AI-Sound API健康状态
    print("\n1️⃣ AI-Sound API健康检查")
    try:
        req = urllib.request.Request("http://localhost:9930/health")
        with urllib.request.urlopen(req, timeout=10) as response:
            health = json.loads(response.read().decode())
            print(f"   ✅ API健康: {health['status']}")
            print(f"   📊 服务状态: {health.get('services', {})}")
    except Exception as e:
        print(f"   ❌ API健康检查失败: {e}")
        return False
    
    # 2. 检查引擎列表
    print("\n2️⃣ 检查注册的引擎")
    try:
        req = urllib.request.Request("http://localhost:9930/api/engines")
        with urllib.request.urlopen(req, timeout=10) as response:
            engines_data = json.loads(response.read().decode())
            engines = engines_data.get('data', {}).get('engines', [])
            print(f"   ✅ 发现 {len(engines)} 个引擎:")
            for engine in engines:
                print(f"      🔹 {engine['id']}: {engine['name']} ({engine['status']})")
    except Exception as e:
        print(f"   ❌ 获取引擎列表失败: {e}")
        return False
    
    # 3. 检查引擎健康状态
    print("\n3️⃣ 检查引擎健康状态")
    try:
        req = urllib.request.Request("http://localhost:9930/api/engines/health")
        with urllib.request.urlopen(req, timeout=10) as response:
            health_data = json.loads(response.read().decode())
            overall = health_data.get('data', {})
            print(f"   ✅ 总体状态: {overall['overall_status']}")
            print(f"   📊 健康引擎: {overall['healthy_engines']}/{overall['total_engines']}")
            
            for engine in overall['engines']:
                status_icon = "✅" if engine['status'] == 'healthy' else "❌"
                print(f"      {status_icon} {engine['id']}: {engine['status']}")
    except Exception as e:
        print(f"   ❌ 引擎健康检查失败: {e}")
    
    # 4. 测试MegaTTS3引擎
    print("\n4️⃣ 测试MegaTTS3引擎")
    try:
        data = {
            "text": "测试MegaTTS3引擎的语音合成功能",
            "engine_id": "megatts3_001",
            "voice_id": "default_voice"
        }
        
        json_data = json.dumps(data).encode('utf-8')
        req = urllib.request.Request(
            "http://localhost:9930/api/tts/synthesize",
            data=json_data,
            headers={'Content-Type': 'application/json'},
            method='POST'
        )
        
        with urllib.request.urlopen(req, timeout=30) as response:
            result = json.loads(response.read().decode())
            if result.get('success'):
                print(f"   ✅ MegaTTS3合成成功")
                print(f"   🎵 音频文件: {result['data']['audio_url']}")
                print(f"   ⏱️ 时长: {result['data']['duration']}秒")
                print(f"   🔧 使用引擎: {result['data']['engine_used']}")
            else:
                print(f"   ❌ MegaTTS3合成失败: {result.get('message')}")
    except Exception as e:
        print(f"   ❌ MegaTTS3测试失败: {e}")
    
    # 5. 测试ESPnet引擎
    print("\n5️⃣ 测试ESPnet引擎")
    try:
        data = {
            "text": "测试ESPnet引擎的语音合成功能",
            "engine_id": "espnet",
            "voice_id": "espnet_zh_female_001"
        }
        
        json_data = json.dumps(data).encode('utf-8')
        req = urllib.request.Request(
            "http://localhost:9930/api/tts/synthesize",
            data=json_data,
            headers={'Content-Type': 'application/json'},
            method='POST'
        )
        
        with urllib.request.urlopen(req, timeout=30) as response:
            result = json.loads(response.read().decode())
            if result.get('success'):
                print(f"   ✅ ESPnet合成成功")
                print(f"   🎵 音频文件: {result['data']['audio_url']}")
                print(f"   ⏱️ 时长: {result['data']['duration']}秒")
                print(f"   🔧 使用引擎: {result['data']['engine_used']}")
            else:
                print(f"   ❌ ESPnet合成失败: {result.get('message')}")
    except Exception as e:
        print(f"   ❌ ESPnet测试失败: {e}")
    
    # 6. 检查声音列表
    print("\n6️⃣ 检查可用声音")
    try:
        # 尝试获取MegaTTS3声音
        req = urllib.request.Request("http://localhost:9930/api/engines/megatts3_001/voices")
        with urllib.request.urlopen(req, timeout=10) as response:
            voices = json.loads(response.read().decode())
            print(f"   🎵 MegaTTS3声音: {len(voices.get('voices', []))} 个")
            
        # 尝试获取ESPnet声音
        req = urllib.request.Request("http://localhost:9930/api/engines/espnet/voices")
        with urllib.request.urlopen(req, timeout=10) as response:
            voices = json.loads(response.read().decode())
            print(f"   🎵 ESPnet声音: {len(voices.get('voices', []))} 个")
            for voice in voices.get('voices', []):
                print(f"      - {voice['id']}: {voice['name']}")
            
    except Exception as e:
        print(f"   ⚠️ 声音列表检查: {e}")
    
    print("\n" + "=" * 60)
    print("📊 对接验证完成!")
    print("💡 如果所有测试都通过，说明AI-Sound与两个引擎对接成功!")
    
if __name__ == "__main__":
    test_ai_sound_integration()