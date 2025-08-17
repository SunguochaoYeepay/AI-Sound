#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import aiohttp
import json
from datetime import datetime

async def test_real_chapter1():
    """测试真实的第三章API"""
    
    print("🌐 测试真实第三章API")
    print("=" * 50)
    
    # 调用正确的API路径，测试第三章（ID: 838）
    api_url = "http://localhost:4000/api/v1/environment-generation/chapters/analyze"
    
    # 构建请求数据
    request_data = {
        "chapter_ids": [838],  # 改为第三章ID
        "analysis_options": {
            "mode": "auto",
            "environment_types": ["nature", "urban", "indoor", "action"],
            "precision": "medium"
        }
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            print(f"📡 调用API: {api_url}")
            print(f"📡 请求数据: {json.dumps(request_data, ensure_ascii=False)}")
            
            async with session.post(api_url, json=request_data) as response:
                if response.status == 200:
                    data = await response.json()
                    print("✅ API调用成功")
                    
                    # 显示环境音轨道
                    if 'analysis_result' in data and 'environment_tracks' in data['analysis_result']:
                        tracks = data['analysis_result']['environment_tracks']
                        print(f"\n🎵 环境音轨道数量: {len(tracks)}")
                        print("=" * 50)
                        
                        for i, track in enumerate(tracks, 1):
                            print(f"\n🎵 轨道 {i}:")
                            print(f"   场景: {track.get('scene_description', 'N/A')}")
                            print(f"   关键词: {', '.join(track.get('environment_keywords', []))}")
                            print(f"   开始时间: {track.get('start_time', 0):.1f}s")
                            print(f"   持续时间: {track.get('duration', 0):.1f}s")
                            print(f"   置信度: {track.get('confidence', 0):.2f}")
                            print(f"   强度等级: {track.get('intensity_level', 'N/A')}")
                            
                            # 显示旁白内容
                            narration = track.get('narration_text', 'N/A')
                            if narration:
                                print(f"   旁白内容: {narration[:100]}...")
                    else:
                        print("❌ 未找到环境音轨道数据")
                        print(f"返回数据: {json.dumps(data, ensure_ascii=False, indent=2)}")
                        
                else:
                    print(f"❌ API调用失败: {response.status}")
                    error_text = await response.text()
                    print(f"错误信息: {error_text}")
                    
    except Exception as e:
        print(f"❌ 请求异常: {e}")

if __name__ == "__main__":
    asyncio.run(test_real_chapter1())
