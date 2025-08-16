#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import sys
import os
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.narration_environment_analyzer import NarrationEnvironmentAnalyzer

async def test_real_chapter_1():
    """测试古玉2第一章的真实内容"""
    
    print("🚀 测试古玉2第一章：穿越")
    print("=" * 60)
    
    # 古玉2第一章的真实内容
    synthesis_plan = [
        {
            "segment_id": 1,
            "text": "博物馆的空调发出轻微嗡鸣，林渊盯着展柜里的汉代青铜剑，指腹无意识摩挲着口袋里的玉佩。那是他在老宅阁楼发现的古物，温润的羊脂玉上刻着不知名的符文。",
            "speaker": "旁白",
            "emotion": "neutral"
        },
        {
            "segment_id": 2,
            "text": "\"叮 ——\" 手机震动打断思绪，是导师发来的消息：\"新出土的文物需要你立即去现场。\"",
            "speaker": "旁白",
            "emotion": "urgent"
        }
    ]
    
    print(f"📝 测试内容: 古玉2第一章 - 穿越")
    print(f"📊 段落数量: {len(synthesis_plan)}")
    print()
    
    # 创建分析器
    analyzer = NarrationEnvironmentAnalyzer()
    
    try:
        start_time = datetime.now()
        
        # 执行分析
        result = await analyzer.extract_and_analyze_narration_batch(synthesis_plan)
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        print(f"✅ 分析完成！耗时: {duration:.2f}秒")
        print()
        
        # 显示结果
        if result and result.environment_tracks:
            print(f"🎵 识别到 {len(result.environment_tracks)} 个环境音轨道:")
            print()
            
            for i, track in enumerate(result.environment_tracks, 1):
                print(f"轨道 {i}:")
                print(f"  场景: {track.scene_description}")
                print(f"  关键词: {', '.join(track.environment_keywords)}")
                print(f"  时长: {track.duration}秒")
                print(f"  强度: {track.intensity}")
                print(f"  类型: {track.track_type}")
                print(f"  置信度: {track.confidence_score}")
                print()
        else:
            print("❌ 没有识别到环境音轨道")
            
    except Exception as e:
        print(f"❌ 分析失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_real_chapter_1())
