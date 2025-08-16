#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
环境音分析快速测试脚本
用于日常调试和快速验证环境音分析功能
"""

import asyncio
import sys
import os
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.narration_environment_analyzer import NarrationEnvironmentAnalyzer


async def quick_test():
    """快速测试环境音分析"""
    
    # 测试用的synthesis_plan（项目72第一章）
    synthesis_plan = [
        {
            "segment_id": 1,
            "text": "夜深人静，大雨如注。林雨推开古宅沉重的木门，门轴发出吱呀的声响。",
            "speaker": "旁白",
            "emotion": "neutral"
        },
        {
            "segment_id": 2,
            "text": "闪电划过天空，照亮了客厅里积满灰尘的家具。雷声轰鸣，让人心跳加速。",
            "speaker": "旁白",
            "emotion": "dramatic"
        },
        {
            "segment_id": 3,
            "text": "突然，楼上传来脚步声。林雨紧张地握紧手电筒，'谁在那里？'",
            "speaker": "旁白",
            "emotion": "nervous"
        },
        {
            "segment_id": 4,
            "text": "是一位白发苍苍的老人，慢慢走下楼梯。每一步都让木板嘎吱作响。",
            "speaker": "旁白",
            "emotion": "contemplative"
        },
        {
            "segment_id": 5,
            "text": "窗外雨声渐急，偶尔夹杂着猫头鹰的叫声，为这个诡异的夜晚增添了更多的悬疑气氛。",
            "speaker": "旁白",
            "emotion": "mysterious"
        }
    ]
    
    print("🚀 快速测试环境音分析")
    print("=" * 50)
    print(f"📝 测试内容: 项目72第一章 - 雨夜古宅")
    print(f"📊 段落数量: {len(synthesis_plan)}")
    print()
    
    try:
        # 初始化分析器
        analyzer = NarrationEnvironmentAnalyzer()
        
        # 执行分析
        start_time = datetime.now()
        result = await analyzer.extract_and_analyze_narration(synthesis_plan)
        end_time = datetime.now()
        
        analysis_duration = (end_time - start_time).total_seconds()
        
        print(f"✅ 分析完成！耗时: {analysis_duration:.2f}秒")
        print()
        
        # 输出详细结果
        if "environment_tracks" in result:
            tracks = result["environment_tracks"]
            print(f"🎵 识别到 {len(tracks)} 个环境音轨道:")
            print()
            
            for i, track in enumerate(tracks, 1):
                print(f"轨道 {i}:")
                print(f"  场景: {track.get('scene_description', '未知')}")
                print(f"  关键词: {', '.join(track.get('environment_keywords', []))}")
                print(f"  时长: {track.get('duration', 0):.1f}秒")
                print(f"  强度: {track.get('intensity', 'unknown')}")
                print(f"  类型: {track.get('continuity_type', 'unknown')}")
                print(f"  置信度: {track.get('confidence', 0):.2f}")
                print()
        
        if "analysis_summary" in result:
            summary = result["analysis_summary"]
            print("📊 分析统计:")
            print(f"  总时长: {summary.get('total_duration', 0):.1f}秒")
            print(f"  旁白段落: {summary.get('narration_segments', 0)}个")
            print(f"  环境轨道: {summary.get('environment_tracks_detected', 0)}个")
            print(f"  分析模式: {summary.get('analysis_mode', 'unknown')}")
        
        return result
        
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


async def test_custom_content():
    """测试自定义内容"""
    print("\n" + "=" * 50)
    print("🎯 测试自定义内容")
    print("=" * 50)
    
    # 可以在这里修改测试内容
    custom_synthesis_plan = [
        {
            "segment_id": 1,
            "text": "海浪轻柔地拍打着沙滩，海鸥在空中盘旋。",
            "speaker": "旁白",
            "emotion": "peaceful"
        },
        {
            "segment_id": 2,
            "text": "远处传来渔船的汽笛声，海风轻抚着椰子树。",
            "speaker": "旁白",
            "emotion": "contemplative"
        }
    ]
    
    try:
        analyzer = NarrationEnvironmentAnalyzer()
        result = await analyzer.extract_and_analyze_narration(custom_synthesis_plan)
        
        print("✅ 自定义内容分析完成！")
        print(f"🎵 识别到 {len(result.get('environment_tracks', []))} 个环境音轨道")
        
        return result
        
    except Exception as e:
        print(f"❌ 自定义内容测试失败: {str(e)}")
        return None


if __name__ == "__main__":
    # 运行快速测试
    asyncio.run(quick_test())
    
    # 运行自定义内容测试
    asyncio.run(test_custom_content())
