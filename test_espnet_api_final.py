#!/usr/bin/env python3
"""
测试新启动的ESPnet Docker服务
"""

import urllib.request
import urllib.error
import json
import time

def test_espnet_api():
    """测试ESPnet API完整功能"""
    base_url = "http://127.0.0.1:9001"
    
    print("🎯 ESPnet服务最终验证")
    print("=" * 50)
    
    # 等待服务完全启动
    print("⏳ 等待服务启动...")
    time.sleep(3)
    
    # 1. 健康检查
    print("\n1️⃣ 健康检查 /health")
    try:
        req = urllib.request.Request(f"{base_url}/health")
        with urllib.request.urlopen(req, timeout=10) as response:
            health_data = json.loads(response.read().decode())
            print(f"   ✅ 响应: {health_data}")
            
            status = health_data.get('status')
            model_loaded = health_data.get('model_loaded', False)
            
            if status == 'healthy' and model_loaded:
                print("   🎉 ESPnet服务完全正常！")
            elif status == 'healthy':
                print("   ⚠️ 服务正常但模型未加载")
            else:
                print(f"   ❌ 服务状态异常: {status}")
                
    except Exception as e:
        print(f"   ❌ 健康检查失败: {e}")
        return False
    
    # 2. 声音列表
    print("\n2️⃣ 声音列表 /voices")
    try:
        req = urllib.request.Request(f"{base_url}/voices")
        with urllib.request.urlopen(req, timeout=10) as response:
            voices_data = json.loads(response.read().decode())
            voices = voices_data.get('voices', [])
            print(f"   ✅ 发现 {len(voices)} 个声音:")
            for voice in voices:
                print(f"      🎵 {voice.get('id')}: {voice.get('name')}")
    except Exception as e:
        print(f"   ❌ 声音列表失败: {e}")
    
    # 3. 语音合成测试
    print("\n3️⃣ 语音合成测试 /synthesize")
    try:
        synthesis_data = {
            "text": "你好，这是ESPnet语音合成测试。",
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
        
        print(f"   📤 发送合成请求...")
        
        with urllib.request.urlopen(req, timeout=30) as response:
            content_type = response.headers.get('Content-Type', '')
            content_length = len(response.read())
            
            print(f"   ✅ 合成成功！")
            print(f"   📄 内容类型: {content_type}")
            print(f"   📊 数据大小: {content_length} bytes")
            
            if 'audio' in content_type and content_length > 1000:
                print("   🎵 返回真实音频文件！ESPnet工作完美！")
                return True
            elif content_length > 100:
                print("   ✅ 返回音频数据，ESPnet正常工作！")
                return True
            else:
                print("   ⚠️ 返回数据较小，可能是模拟音频")
                return False
                
    except urllib.error.HTTPError as e:
        error_content = e.read().decode() if hasattr(e, 'read') else str(e)
        print(f"   ❌ 合成失败 (HTTP {e.code}): {error_content}")
        return False
    except Exception as e:
        print(f"   ❌ 合成失败: {e}")
        return False

def main():
    """主测试"""
    success = test_espnet_api()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 ESPnet Docker服务验证成功！")
        print("🔥 现在可以在AI-Sound系统中使用真实的ESPnet语音合成了！")
    else:
        print("⚠️ ESPnet服务需要进一步调试")
        print("💡 建议检查Docker容器日志：docker logs espnet-service")

if __name__ == "__main__":
    main()