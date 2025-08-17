#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import aiohttp
import json
from datetime import datetime

async def force_filter_test():
    """强制过滤测试"""
    
    print("🔧 强制过滤测试")
    print("=" * 50)
    
    # 调用API
    api_url = "http://localhost:4000/api/v1/environment-generation/chapters/analyze"
    
    request_data = {
        "chapter_ids": [838],
        "analysis_options": {
            "mode": "auto",
            "environment_types": ["nature", "urban", "indoor", "action"],
            "precision": "medium"
        }
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(api_url, json=request_data) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # 强制过滤错误的关键词
                    if 'analysis_result' in data and 'environment_tracks' in data['analysis_result']:
                        tracks = data['analysis_result']['environment_tracks']
                        
                        for track in tracks:
                            # 强制过滤错误的关键词
                            original_keywords = track.get('environment_keywords', [])
                            filtered_keywords = []
                            
                            for keyword in original_keywords:
                                keyword_lower = keyword.lower()
                                if '翻书声' not in keyword_lower and '写字声' not in keyword_lower and '水声' not in keyword_lower:
                                    filtered_keywords.append(keyword)
                                else:
                                    print(f"🔧 强制过滤: {keyword}")
                            
                            # 更新关键词
                            track['environment_keywords'] = filtered_keywords
                            track['scene_description'] = "、".join(filtered_keywords[:3]) if filtered_keywords else "无声段"
                        
                        # 显示过滤后的结果
                        print(f"\n🎵 过滤后环境音轨道数量: {len(tracks)}")
                        print("=" * 50)
                        
                        for i, track in enumerate(tracks, 1):
                            print(f"\n🎵 轨道 {i}:")
                            print(f"   场景: {track.get('scene_description', 'N/A')}")
                            print(f"   关键词: {', '.join(track.get('environment_keywords', []))}")
                            print(f"   开始时间: {track.get('start_time', 0):.1f}s")
                            print(f"   持续时间: {track.get('duration', 0):.1f}s")
                            print(f"   置信度: {track.get('confidence', 0):.2f}")
                            
                            # 显示旁白内容
                            narration = track.get('narration_text', 'N/A')
                            if narration:
                                print(f"   旁白内容: {narration[:100]}...")
                        
                else:
                    print(f"❌ API调用失败: {response.status}")
                    
    except Exception as e:
        print(f"❌ 请求异常: {e}")

if __name__ == "__main__":
    asyncio.run(force_filter_test())
