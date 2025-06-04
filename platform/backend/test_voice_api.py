#!/usr/bin/env python3
"""
测试声音API
验证声音测试功能是否正常
"""
import requests
import json

def test_voice_api():
    base_url = "http://soundapi.cpolar.top"
    
    print("🎤 === 测试声音API ===")
    
    # 1. 获取声音库列表
    print("\n1. 获取声音库列表...")
    try:
        response = requests.get(f"{base_url}/api/characters")
        
        if response.status_code == 200:
            data = response.json()
            voices = data.get('data', [])
            print(f"✅ 获取到 {len(voices)} 个声音档案")
            
            # 显示声音档案信息
            for voice in voices[:3]:  # 只显示前3个
                print(f"   ID: {voice['id']}, 名称: {voice['name']}, 类型: {voice['type']}")
                print(f"   参考音频: {voice.get('referenceAudioUrl', 'None')}")
                print(f"   Latent文件: {voice.get('latentFileUrl', 'None')}")
            
            # 测试第一个声音
            if voices:
                test_voice_id = voices[0]['id']
                test_voice_synthesis(base_url, test_voice_id, voices[0]['name'])
            else:
                print("❌ 没有可用的声音档案")
                
        else:
            print(f"❌ 获取声音库失败: HTTP {response.status_code}")
            
    except Exception as e:
        print(f"❌ 异常: {str(e)}")

def test_voice_synthesis(base_url: str, voice_id: int, voice_name: str):
    """测试声音合成"""
    print(f"\n2. 测试声音合成 - {voice_name} (ID: {voice_id})...")
    
    try:
        # 准备测试数据
        test_data = {
            'text': '你好，这是声音测试。我正在验证TTS功能是否正常工作。',
            'time_step': '20',
            'p_weight': '1.0',
            't_weight': '1.0'
        }
        
        response = requests.post(f"{base_url}/api/characters/{voice_id}/test", data=test_data)
        
        print(f"   状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ 声音合成成功")
            print(f"   音频URL: {result.get('audioUrl')}")
            print(f"   处理时间: {result.get('processingTime', 0):.2f}秒")
            print(f"   音频ID: {result.get('audioId')}")
            
            # 尝试验证音频文件是否可访问
            audio_url = result.get('audioUrl')
            if audio_url:
                try:
                    audio_response = requests.head(audio_url, timeout=5)
                    if audio_response.status_code == 200:
                        print("✅ 音频文件可访问")
                    else:
                        print(f"⚠️ 音频文件不可访问: HTTP {audio_response.status_code}")
                except Exception as e:
                    print(f"⚠️ 音频文件检查失败: {str(e)}")
            
        else:
            error_data = response.text
            print(f"❌ 声音合成失败: HTTP {response.status_code}")
            print(f"   错误响应: {error_data}")
            
            try:
                error_json = response.json()
                print(f"   错误详情: {error_json.get('detail', '未知错误')}")
            except:
                print("   无法解析错误响应")
                
    except Exception as e:
        print(f"❌ 测试异常: {str(e)}")

if __name__ == "__main__":
    test_voice_api() 