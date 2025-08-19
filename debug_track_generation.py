#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), 'platform', 'backend'))

from app.services.narration_environment_analyzer import NarrationEnvironmentAnalyzer

async def debug_track_generation():
    print("=== 调试轨道生成逻辑 ===")
    
    analyzer = NarrationEnvironmentAnalyzer()
    
    # 模拟segment数据
    synthesis_plan = [
        {"segment_id": 6, "content": "打雷了！！都打的雨点打到了地上，形成一条滚滚大河。", "character": "旁白"}
    ]
    
    print("开始完整分析...")
    
    try:
        # 调用完整分析
        result = await analyzer.extract_and_analyze_narration(synthesis_plan)
        
        print(f"最终结果: {result}")
        
        # 检查结果中的轨道
        tracks = result.get('environment_tracks', [])
        print(f"\n生成的轨道数量: {len(tracks)}")
        
        for i, track in enumerate(tracks):
            print(f"\n轨道 {i+1}:")
            print(f"  segment_id: {track.get('segment_id')}")
            print(f"  environment_keywords: {track.get('environment_keywords')}")
            print(f"  english_prompt: '{track.get('english_prompt')}'")
            print(f"  chinese_description: '{track.get('chinese_description')}'")
            print(f"  has_environment: {track.get('has_environment')}")
            
        # 检查LLM结果
        print("\n=== 检查LLM结果 ===")
        # 直接调用LLM
        llm_result = await analyzer._analyze_with_llm(synthesis_plan)
        print(f"LLM结果类型: {type(llm_result)}")
        print(f"analyzed_scenes数量: {len(llm_result.analyzed_scenes)}")
        
        for i, scene in enumerate(llm_result.analyzed_scenes):
            print(f"\n场景 {i+1}:")
            print(f"  keywords: {scene.keywords}")
            print(f"  metadata: {scene.metadata}")
            
            # 检查提示词数据
            prompts = scene.metadata.get('prompts', [])
            print(f"  提示词数量: {len(prompts)}")
            
            for j, prompt in enumerate(prompts):
                print(f"    提示词 {j+1}:")
                print(f"      keyword: {prompt.get('keyword')}")
                print(f"      english_prompt: '{prompt.get('english_prompt', '')}'")
                print(f"      chinese_description: '{prompt.get('chinese_description', '')}'")
            
    except Exception as e:
        print(f"调试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_track_generation())
