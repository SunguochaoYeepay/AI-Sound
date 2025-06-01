#!/usr/bin/env python3
"""
直接测试MegaTTS3 TTS功能
"""

import requests
import json
import os
from pathlib import Path

def test_megatts3_tts():
    """测试MegaTTS3文字转语音功能"""
    
    print("🎯 开始测试MegaTTS3核心TTS功能...")
    
    # MegaTTS3服务地址
    base_url = "http://127.0.0.1:7929"
    
    # 1. 健康检查
    print("1️⃣ 检查MegaTTS3服务健康状态...")
    try:
        health_response = requests.get(f"{base_url}/health", timeout=10)
        print(f"   健康检查响应码: {health_response.status_code}")
        if health_response.status_code == 200:
            print(f"   ✅ 健康检查通过: {health_response.text}")
        else:
            print(f"   ❌ 健康检查失败: {health_response.text}")
            return False
    except Exception as e:
        print(f"   ❌ 健康检查连接失败: {e}")
        return False
    
    # 2. 尝试获取API信息（新版接口）
    print("2️⃣ 获取MegaTTS3 API信息...")
    try:
        api_info_response = requests.get(f"{base_url}/api/info", timeout=10)
        print(f"   API信息响应码: {api_info_response.status_code}")
        if api_info_response.status_code == 200:
            api_info = api_info_response.json()
            print(f"   ✅ API版本: {api_info.get('version', 'unknown')}")
            print(f"   📋 可用端点: {api_info.get('endpoints', {})}")
        else:
            print(f"   ⚠️ 无法获取API信息: {api_info_response.text}")
    except Exception as e:
        print(f"   ⚠️ 获取API信息失败: {e}")
    
    # 3. 尝试获取声音对列表（新版接口）
    print("3️⃣ 获取MegaTTS3声音对列表...")
    try:
        voice_pairs_response = requests.get(f"{base_url}/api/voice-pairs", timeout=10)
        print(f"   声音对列表响应码: {voice_pairs_response.status_code}")
        if voice_pairs_response.status_code == 200:
            voice_pairs = voice_pairs_response.json()
            print(f"   ✅ 可用声音对数量: {len(voice_pairs)}")
            # 显示前几个声音对
            for i, pair in enumerate(voice_pairs[:3]):
                print(f"      - {pair.get('name', 'unknown')}: {pair.get('description', 'no description')}")
        else:
            print(f"   ❌ 获取声音对列表失败: {voice_pairs_response.text}")
    except Exception as e:
        print(f"   ❌ 获取声音对列表连接失败: {e}")
    
    # 4. 测试语音合成 - 尝试多个端点
    print("4️⃣ 测试语音合成（尝试多个端点）...")
    test_text = "你好，这是AI-Sound系统的测试。"
    
    # 尝试的端点列表
    synthesis_endpoints = [
        "/api/synthesize",          # 新版主要接口
        "/synthesize",              # 旧版接口
        "/api/synthesis/by-pairs"   # 增强版接口
    ]
    
    # 不同的请求格式
    request_formats = [
        {
            "text": test_text,
            "voice_id": "default",
            "emotion_type": "neutral",
            "emotion_intensity": 0.5,
            "speed_scale": 1.0,
            "pitch_scale": 1.0
        },
        {
            "text": test_text,
            "voice_id": "female_001",
            "infer_timestep": 16,
            "p_w": 1.4,
            "t_w": 3.0
        },
        {
            "text": test_text,
            "speaker": "default"
        }
    ]
    
    for endpoint in synthesis_endpoints:
        print(f"   🔄 尝试端点: {endpoint}")
        
        for i, payload in enumerate(request_formats):
            try:
                print(f"      格式{i+1}: {json.dumps(payload, ensure_ascii=False)}")
                
                synthesis_response = requests.post(
                    f"{base_url}{endpoint}",
                    json=payload,
                    timeout=30,
                    headers={"Content-Type": "application/json"}
                )
                
                print(f"      响应码: {synthesis_response.status_code}")
                print(f"      响应头: {dict(synthesis_response.headers)}")
                
                if synthesis_response.status_code == 200:
                    # 检查响应内容
                    content_type = synthesis_response.headers.get('content-type', '').lower()
                    if 'audio' in content_type or content_type.startswith('application/octet-stream'):
                        print(f"      ✅ 音频合成成功！音频大小: {len(synthesis_response.content)} 字节")
                        
                        # 保存音频文件
                        output_file = f"test_megatts3_output_{endpoint.replace('/', '_')}_format{i+1}.wav"
                        with open(output_file, 'wb') as f:
                            f.write(synthesis_response.content)
                        print(f"      💾 音频已保存到: {output_file}")
                        print(f"      🎉 成功端点: {endpoint}, 格式: {i+1}")
                        return True
                    else:
                        print(f"      ❌ 响应不是音频格式: {content_type}")
                        print(f"      响应内容: {synthesis_response.text[:200]}")
                else:
                    print(f"      ❌ 请求失败: {synthesis_response.text[:200]}")
                    
            except Exception as e:
                print(f"      ❌ 请求异常: {e}")
            
            print(f"      ---")
    
    return False

def test_api_endpoints():
    """测试API服务端点"""
    print("🔍 测试API服务端点...")
    
    api_base = "http://127.0.0.1:9930"
    endpoints = [
        "/health",
        "/api/engines",
        "/api/voices", 
        "/api/tts/megatts3/health"
    ]
    
    for endpoint in endpoints:
        try:
            response = requests.get(f"{api_base}{endpoint}", timeout=5)
            print(f"   {endpoint}: {response.status_code}")
            if response.status_code == 200:
                print(f"      ✅ 正常")
            else:
                print(f"      ❌ 失败: {response.text[:100]}")
        except Exception as e:
            print(f"   {endpoint}: ❌ 连接失败 - {e}")

if __name__ == "__main__":
    print("=" * 60)
    print("🚀 AI-Sound MegaTTS3 核心功能测试")
    print("=" * 60)
    
    # 测试MegaTTS3直接TTS功能
    tts_success = test_megatts3_tts()
    
    print()
    print("=" * 60)
    
    # 测试API服务端点
    test_api_endpoints()
    
    print()
    print("=" * 60)
    if tts_success:
        print("🎉 结论: MegaTTS3核心TTS功能正常！")
    else:
        print("💥 结论: MegaTTS3核心TTS功能存在问题！")
    print("=" * 60) 