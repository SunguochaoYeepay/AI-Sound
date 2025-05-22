"""
API服务测试脚本
"""

import os
import sys
import time
import json
import requests
import argparse
from pathlib import Path

def main():
    """主测试函数"""
    # 解析命令行参数
    parser = argparse.ArgumentParser(description="测试MegaTTS API服务")
    parser.add_argument("--host", default="127.0.0.1", help="API服务主机地址")
    parser.add_argument("--port", default="9930", help="API服务端口")
    args = parser.parse_args()
    
    # 定义服务地址
    base_url = f"http://{args.host}:{args.port}"
    
    print(f"测试MegaTTS API服务... 地址: {base_url}")
    
    # 测试健康状态
    print("\n1. 测试健康检查接口...")
    health_success = False
    try:
        response = requests.get(f"{base_url}/health", timeout=30)  # 增加超时时间到30秒
        if response.status_code == 200:
            print(f"✅ 健康检查成功: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
            health_success = True
        else:
            print(f"❌ 健康检查失败: HTTP {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"❌ 健康检查请求失败: {str(e)}")
        print("服务可能未启动，请先运行 python main.py api --host 127.0.0.1 --port 9930")
    
    # 仅在健康检查成功时测试其他接口
    if health_success:
        # 测试语音模型列表接口
        print("\n2. 测试语音模型列表接口...")
        try:
            response = requests.get(f"{base_url}/api/voices", timeout=30)
            if response.status_code == 200:
                print(f"✅ 获取语音模型列表成功:")
                data = response.json()
                if data.get("success"):
                    voices = data.get("voices", [])
                    print(f"  找到 {len(voices)} 个语音模型")
                    for voice in voices[:3]:  # 只显示前3个模型
                        print(f"  - {voice.get('id')}: {voice.get('name')}")
                    if len(voices) > 3:
                        print(f"  - ... 等共 {len(voices)} 个模型")
                else:
                    print(f"❌ 获取语音模型列表返回错误: {json.dumps(data, indent=2, ensure_ascii=False)}")
            else:
                print(f"❌ 获取语音模型列表失败: HTTP {response.status_code}")
                print(response.text)
        except Exception as e:
            print(f"❌ 获取语音模型列表请求失败: {str(e)}")
        
        # 测试情感类型列表接口
        print("\n3. 测试情感类型列表接口...")
        try:
            response = requests.get(f"{base_url}/api/emotions", timeout=30)
            if response.status_code == 200:
                print(f"✅ 获取情感类型列表成功:")
                data = response.json()
                if data.get("success"):
                    emotions = data.get("emotions", [])
                    print(f"  找到 {len(emotions)} 个情感类型")
                    for emotion in emotions[:3]:  # 只显示前3个
                        print(f"  - {emotion.get('id')}: {emotion.get('name')}")
                    if len(emotions) > 3:
                        print(f"  - ... 等共 {len(emotions)} 个情感类型")
                else:
                    print(f"❌ 获取情感类型列表返回错误: {json.dumps(data, indent=2, ensure_ascii=False)}")
            else:
                print(f"❌ 获取情感类型列表失败: HTTP {response.status_code}")
                print(response.text)
        except Exception as e:
            print(f"❌ 获取情感类型列表请求失败: {str(e)}")
        
        # 测试TTS基本功能
        print("\n4. 测试文本转语音功能...")
        test_text = "这是一段测试文本，用于测试MegaTTS的文本转语音功能。"
        try:
            payload = {
                "text": test_text,
                "voice_id": "female_young",
                "emotion_type": "happy",
                "emotion_intensity": 0.7,
                "output_format": "wav",
                "return_base64": False
            }
            
            response = requests.post(f"{base_url}/api/tts", json=payload, timeout=60)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    print(f"✅ 语音合成成功:")
                    audio_url = data.get("audio_url")
                    duration = data.get("duration", 0)
                    print(f"  音频URL: {audio_url}")
                    print(f"  音频时长: {duration:.2f}秒")
                    
                    # 测试下载生成的音频
                    if audio_url:
                        print("\n5. 测试音频下载功能...")
                        try:
                            audio_response = requests.get(f"{base_url}{audio_url}", timeout=30)
                            if audio_response.status_code == 200:
                                print(f"✅ 音频下载成功，内容长度: {len(audio_response.content)} 字节")
                            else:
                                print(f"❌ 音频下载失败: HTTP {audio_response.status_code}")
                        except Exception as e:
                            print(f"❌ 音频下载请求失败: {str(e)}")
                else:
                    print(f"❌ 语音合成返回错误: {json.dumps(data, indent=2, ensure_ascii=False)}")
            else:
                print(f"❌ 语音合成请求失败: HTTP {response.status_code}")
                print(response.text)
        except Exception as e:
            print(f"❌ 语音合成请求失败: {str(e)}")
            
        # 测试预览接口
        print("\n6. 测试语音预览接口...")
        try:
            payload = {
                "text": "这是一段预览文本，用于测试预览功能。",
                "voice_id": "male_young",
                "emotion_type": "neutral",
                "output_format": "wav"
            }
            
            response = requests.post(f"{base_url}/api/voices/preview", json=payload, timeout=60)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    print(f"✅ 预览音频生成成功:")
                    preview_url = data.get("preview_url")
                    duration = data.get("duration", 0)
                    print(f"  预览URL: {preview_url}")
                    print(f"  预览时长: {duration:.2f}秒")
                else:
                    print(f"❌ 预览音频生成返回错误: {json.dumps(data, indent=2, ensure_ascii=False)}")
            else:
                print(f"❌ 预览音频生成请求失败: HTTP {response.status_code}")
                print(response.text)
        except Exception as e:
            print(f"❌ 预览音频生成请求失败: {str(e)}")
        
        print("\n所有测试完成!")
    else:
        print("\n由于健康检查失败，跳过其他测试。")

def test_voices_api():
    """测试声音API接口"""
    print("\n===== 测试声音API接口 =====")
    
    # 定义服务地址
    base_url = "http://127.0.0.1:9930"
    
    # 获取声音列表
    response = requests.get(f"{base_url}/api/voices", timeout=30)
    assert response.status_code == 200, f"获取声音列表失败: {response.text}"
    
    result = response.json()
    assert result["success"], f"API返回错误: {result}"
    print(f"系统内置声音数量: {len(result['voices'])}")
    
    # 测试声纹特征API
    try:
        # 获取自定义声音列表
        response = requests.get(f"{base_url}/api/voices/list", timeout=30)
        if response.status_code == 200:
            result = response.json()
            print(f"自定义声纹特征数量: {result.get('count', 0)}")
            
            # 获取声音标签
            response = requests.get(f"{base_url}/api/voices/tags", timeout=30)
            if response.status_code == 200:
                result = response.json()
                print(f"声音标签: {len(result.get('tags', []))}")
                
        else:
            print(f"获取自定义声音列表失败: {response.status_code}")
    except Exception as e:
        print(f"测试声纹特征API失败: {e}")
    
    print("声音API测试完成")

if __name__ == "__main__":
    main()
    test_voices_api()  # 添加声音API测试 