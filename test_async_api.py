#!/usr/bin/env python3
"""
测试直接音乐生成API
"""

import requests
import json

def test_direct_music_generation():
    """测试直接音乐生成API（音乐库使用的）"""
    
    # API端点
    url = "http://localhost:8000/api/v1/music-generation/generate-direct"
    
    # 测试数据
    data = {
        "lyrics": "[Verse]\n这是一个测试歌曲\n旋律优美动听\n\n[Chorus]\n美好的时光\n值得纪念",
        "genre": "Pop",
        "description": "测试直接音乐生成",
        "cfg_coef": 1.5,
        "temperature": 0.9,
        "top_k": 50,
        "volume_level": -12.0
    }
    
    print("🎵 测试直接音乐生成API (音乐库使用)")
    print(f"URL: {url}")
    print(f"请求数据: {json.dumps(data, indent=2, ensure_ascii=False)}")
    print("⏳ 音乐生成大约需要5-6分钟，请耐心等待...")
    
    try:
        # 发送请求，增加超时时间到15分钟
        response = requests.post(url, json=data, timeout=900)  
        
        print(f"\n📊 响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 直接音乐生成API响应成功!")
            print(f"成功: {result.get('success')}")
            print(f"音频路径: {result.get('audio_path')}")
            print(f"音频URL: {result.get('audio_url')}")
            print(f"生成时间: {result.get('generation_time')}秒")
            if result.get('error'):
                print(f"错误信息: {result.get('error')}")
            else:
                print("🎉 音乐生成成功！")
        else:
            print(f"❌ API调用失败: {response.text}")
            
    except Exception as e:
        print(f"❌ 请求异常: {e}")

if __name__ == "__main__":
    test_direct_music_generation()