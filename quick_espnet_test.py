#!/usr/bin/env python3
"""
快速测试ESPnet接口可用性
"""

import urllib.request
import urllib.error
import json

def quick_test():
    """快速测试ESPnet核心功能"""
    base_url = "http://127.0.0.1:9001"
    
    print("🔥 ESPnet接口快速验证")
    print("=" * 40)
    
    # 1. 健康检查
    try:
        req = urllib.request.Request(f"{base_url}/health")
        with urllib.request.urlopen(req, timeout=5) as response:
            health = json.loads(response.read().decode())
            print(f"✅ 健康检查: {health['status']} (模型: {health['model_loaded']})")
    except Exception as e:
        print(f"❌ 健康检查失败: {e}")
        return False
    
    # 2. 语音合成
    try:
        data = {
            "text": "快速测试ESPnet",
            "speaker": "espnet_zh_female_001"
        }
        
        json_data = json.dumps(data).encode('utf-8')
        req = urllib.request.Request(
            f"{base_url}/synthesize",
            data=json_data,
            headers={'Content-Type': 'application/json'},
            method='POST'
        )
        
        with urllib.request.urlopen(req, timeout=15) as response:
            audio_size = len(response.read())
            content_type = response.headers.get('Content-Type', '')
            
            print(f"✅ 语音合成: {audio_size} bytes ({content_type})")
            
            if 'audio' in content_type and audio_size > 10000:
                print("🎵 ESPnet接口完全可用！返回真实音频！")
                return True
            else:
                print("⚠️ 返回数据异常")
                return False
                
    except Exception as e:
        print(f"❌ 语音合成失败: {e}")
        return False

if __name__ == "__main__":
    success = quick_test()
    print("=" * 40)
    if success:
        print("🎉 结论: ESPnet接口可用，老爹可以测试了！")
    else:
        print("💥 结论: ESPnet接口有问题，需要修复！")