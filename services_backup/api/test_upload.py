#!/usr/bin/env python3
"""
测试声音上传接口
"""

import requests
import json
import io

def test_voice_upload():
    """测试声音上传接口"""
    
    # API端点
    url = "http://localhost:9930/api/voices/upload"
    
    # 创建模拟音频文件
    fake_audio = b"RIFF" + b"\x00" * 44 + b"fake audio data" * 100  # 模拟WAV文件
    audio_file = io.BytesIO(fake_audio)
    audio_file.name = "test_voice.wav"
    
    # 元数据
    metadata = {
        "name": "测试声音",
        "engine": "megatts3",
        "gender": "female",
        "language": "zh-CN",
        "description": "这是一个测试声音",
        "tags": ["测试", "女性"]
    }
    
    # 准备文件和数据
    files = {
        'audio': ('test_voice.wav', audio_file, 'audio/wav')
    }
    
    data = {
        'metadata': json.dumps(metadata)
    }
    
    try:
        print("正在测试声音上传接口...")
        print(f"URL: {url}")
        print(f"Metadata: {json.dumps(metadata, ensure_ascii=False, indent=2)}")
        
        response = requests.post(url, files=files, data=data)
        
        print(f"\n响应状态码: {response.status_code}")
        print(f"响应头: {dict(response.headers)}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ 上传成功!")
            print(f"响应内容: {json.dumps(result, ensure_ascii=False, indent=2)}")
        else:
            print(f"❌ 上传失败: {response.status_code}")
            print(f"错误响应: {response.text}")
            
    except Exception as e:
        print(f"❌ 请求异常: {e}")

if __name__ == "__main__":
    test_voice_upload() 