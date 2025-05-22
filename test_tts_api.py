"""
TTS API测试脚本
用于测试各种声音样本的TTS功能
"""

import requests
import base64
import json
import os
import time
import argparse
from pydub import AudioSegment
from pydub.playback import play

# API端点
API_URL = "http://localhost:9930/api/tts"
API_MULTIPART_URL = "http://localhost:9930/api/tts/text_multipart"

def test_tts(text, voice_id, emotion_type="neutral", emotion_intensity=0.5):
    """
    测试基本的TTS功能
    """
    print(f"生成语音 - 文本: '{text}', 声音: {voice_id}, 情感: {emotion_type} ({emotion_intensity})")
    
    # 构建请求
    payload = {
        "text": text,
        "voice_id": voice_id,
        "emotion_type": emotion_type,
        "emotion_intensity": emotion_intensity,
        "return_base64": True
    }
    
    try:
        # 发送请求
        response = requests.post(API_URL, json=payload)
        
        # 检查响应
        if response.status_code == 200:
            result = response.json()
            if result.get("success") and result.get("audio_base64"):
                print(f"成功! 音频长度: {result.get('duration', 0):.2f}秒")
                
                # 保存音频到文件
                audio_data = base64.b64decode(result["audio_base64"])
                filename = f"test_output_{voice_id}_{emotion_type}.wav"
                with open(filename, "wb") as f:
                    f.write(audio_data)
                print(f"已保存到文件: {filename}")
                
                return True, filename
            else:
                print(f"API返回错误: {result.get('message', '未知错误')}")
                return False, None
        else:
            print(f"API请求失败: HTTP {response.status_code}")
            print(response.text)
            return False, None
    except Exception as e:
        print(f"请求出错: {str(e)}")
        return False, None

def test_voice_samples():
    """
    测试所有可用的声音样本
    """
    print("===== 测试所有声音样本 =====")
    
    test_cases = [
        # 测试范闲声音
        {
            "text": "你好，我是范闲，很高兴见到你！",
            "voice_id": "范闲",
            "emotion_type": "happy",
            "emotion_intensity": 0.7
        },
        # 测试周杰伦声音
        {
            "text": "这是周杰伦的声音测试，听听效果如何。",
            "voice_id": "周杰伦",
            "emotion_type": "neutral",
            "emotion_intensity": 0.5
        },
        # 测试英文声音
        {
            "text": "This is an English text sample. How does it sound?",
            "voice_id": "english_talk",
            "emotion_type": "surprised",
            "emotion_intensity": 0.6
        }
    ]
    
    results = []
    for idx, test_case in enumerate(test_cases):
        print(f"\n[测试 {idx+1}/{len(test_cases)}]")
        success, filename = test_tts(**test_case)
        results.append({
            "test_case": test_case,
            "success": success,
            "filename": filename
        })
        time.sleep(1)  # 避免过快请求
    
    # 输出汇总结果
    print("\n===== 测试结果汇总 =====")
    for idx, result in enumerate(results):
        test_case = result["test_case"]
        status = "✅ 成功" if result["success"] else "❌ 失败"
        print(f"{idx+1}. [{status}] 声音: {test_case['voice_id']}, 情感: {test_case['emotion_type']}")
    
    return results

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="测试TTS API功能")
    parser.add_argument("--voice", default=None, help="指定要测试的声音ID")
    parser.add_argument("--text", default=None, help="指定要合成的文本")
    args = parser.parse_args()
    
    if args.voice and args.text:
        # 测试单个声音
        test_tts(args.text, args.voice)
    else:
        # 测试所有声音样本
        test_voice_samples() 