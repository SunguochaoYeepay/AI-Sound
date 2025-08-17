#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import aiohttp
import json
from datetime import datetime

async def debug_llm_response():
    """调试LLM的原始响应"""
    
    print("🔍 调试LLM原始响应")
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
                    
                    # 显示原始分析结果
                    if 'analysis_result' in data and 'environment_tracks' in data['analysis_result']:
                        tracks = data['analysis_result']['environment_tracks']
                        
                        for i, track in enumerate(tracks, 1):
                            print(f"\n🎵 轨道 {i} 原始数据:")
                            print(f"   关键词: {track.get('environment_keywords', [])}")
                            print(f"   场景描述: {track.get('scene_description', 'N/A')}")
                            print(f"   旁白内容: {track.get('narration_text', 'N/A')[:100]}...")
                            
                            # 检查关键词类型
                            keywords = track.get('environment_keywords', [])
                            for j, keyword in enumerate(keywords):
                                print(f"     关键词{j+1}: '{keyword}' (类型: {type(keyword)})")
                    
                    # 显示LLM原始响应（如果有的话）
                    if 'analysis_result' in data and 'raw_llm_response' in data['analysis_result']:
                        print(f"\n🤖 LLM原始响应:")
                        print(data['analysis_result']['raw_llm_response'])
                        
                else:
                    print(f"❌ API调用失败: {response.status}")
                    
    except Exception as e:
        print(f"❌ 请求异常: {e}")

if __name__ == "__main__":
    asyncio.run(debug_llm_response())
