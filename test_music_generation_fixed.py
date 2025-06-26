#!/usr/bin/env python3
"""
测试修复后的音乐生成功能
"""

import asyncio
import sys
import os
import requests
import json

async def test_song_generation_service():
    """测试SongGeneration服务"""
    print("🔍 测试SongGeneration服务连接...")
    
    try:
        response = requests.get("http://localhost:7863/health", timeout=10)
        if response.status_code == 200:
            print("✅ SongGeneration服务连接正常")
            print(f"响应: {response.json()}")
            return True
        else:
            print(f"❌ SongGeneration服务响应异常: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ SongGeneration服务连接失败: {e}")
        return False

async def test_music_generation_api():
    """测试音乐生成API"""
    print("\n🎵 测试音乐生成API...")
    
    # 测试数据
    test_data = {
        "scene_description": "peaceful countryside morning",
        "duration": 30,
        "style": "acoustic folk"
    }
    
    try:
        response = requests.post(
            "http://localhost:8000/api/v1/music-generation/generate-direct",
            json=test_data,
            timeout=120  # 2分钟超时
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ 音乐生成API调用成功")
            print(f"响应数据: {json.dumps(result, indent=2, ensure_ascii=False)}")
            
            if result.get('success') and result.get('data', {}).get('audio_url'):
                print(f"🎶 生成音频URL: {result['data']['audio_url']}")
                return True
            else:
                print("❌ API响应格式异常")
                return False
        else:
            print(f"❌ 音乐生成API调用失败: {response.status_code}")
            print(f"错误信息: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 音乐生成API调用异常: {e}")
        return False

async def main():
    """主测试函数"""
    print("🎼 开始测试修复后的音乐生成功能\n")
    
    # 测试1：SongGeneration服务连接
    service_ok = await test_song_generation_service()
    
    if not service_ok:
        print("\n❌ SongGeneration服务不可用，跳过API测试")
        return
    
    # 测试2：音乐生成API
    api_ok = await test_music_generation_api()
    
    if api_ok:
        print("\n🎉 所有测试通过！音乐生成功能修复成功！")
    else:
        print("\n❌ 音乐生成API测试失败")

if __name__ == "__main__":
    asyncio.run(main()) 