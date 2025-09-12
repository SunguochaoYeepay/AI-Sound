#!/usr/bin/env python3
"""
3步分析流程性能测试
详细测量对话分析、5卡分析、音频分镜卡生成的时长
"""

import asyncio
import json
import sys
import os
import time
from datetime import datetime

# 添加项目路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'platform', 'backend'))

from app.services.six_card_analyzer import SixCardAnalyzer
from app.detectors.ollama_character_detector import OllamaCharacterDetector

async def performance_analysis_test():
    """性能分析测试"""
    print("⏱️ 3步分析流程性能测试")
    print("=" * 50)
    
    # 创建分析器
    character_detector = OllamaCharacterDetector()
    six_card_analyzer = SixCardAnalyzer()
    
    # 测试文本
    test_text = '"快看这女子的衣装！""莫不是西域来的怪人？"林薇低头看着自己身上的白大褂，又抬头望向四周鳞次栉比的飞檐斗拱，心脏猛地一缩——她竟真的穿越到了课本里的盛唐长安。还没等她理清思绪，一阵急促的马蹄声突然从巷口传来，伴随着惊惶的呼喊，人群瞬间四散奔逃。'
    
    print(f"📝 测试文本长度: {len(test_text)} 字符")
    print(f"📝 测试文本: {test_text[:80]}...")
    print()
    
    total_start_time = time.time()
    
    try:
        # 第一步：对话分析
        print("🎭 步骤1/3：对话分析")
        step1_start = time.time()
        
        chapter_info = {
            "chapter_id": 999,
            "chapter_title": "性能测试段落",
            "chapter_number": 1,
            "processing_mode": "single"
        }
        dialogue_analysis = await character_detector.analyze_text(test_text, chapter_info)
        
        step1_end = time.time()
        step1_duration = step1_end - step1_start
        
        segments_count = len(dialogue_analysis.get('segments', []))
        characters_count = len(dialogue_analysis.get('characters', []))
        
        print(f"   ✅ 对话分析完成: {step1_duration:.2f}s")
        print(f"   📊 结果: {segments_count}个片段，{characters_count}个角色")
        print()
        
        # 第二步：5卡分析
        print("🎯 步骤2/3：5卡分析")
        step2_start = time.time()
        
        six_card_result = await six_card_analyzer.analyze_segment(test_text, 0, 999)
        
        step2_end = time.time()
        step2_duration = step2_end - step2_start
        
        synthesis_segments = len(six_card_result.get('synthesis_json', {}).get('synthesis_plan', []))
        
        print(f"   ✅ 5卡分析完成: {step2_duration:.2f}s")
        print(f"   📊 结果: 生成{synthesis_segments}个合成片段")
        print(f"   🔧 包含字段: {', '.join(six_card_result.keys())}")
        print()
        
        # 第三步：音频分镜卡生成
        print("🎬 步骤3/3：音频分镜卡生成")
        step3_start = time.time()
        
        complete_result = await six_card_analyzer.generate_audio_storyboard_for_segment(
            six_card_result, test_text, 0
        )
        
        step3_end = time.time()
        step3_duration = step3_end - step3_start
        
        sound_effects_count = len(complete_result.get('audio_storyboard_card', {}).get('sound_effects', []))
        background_music = complete_result.get('audio_storyboard_card', {}).get('background_music', {})
        background_music_count = 1 if background_music else 0
        
        print(f"   ✅ 音频分镜卡完成: {step3_duration:.2f}s")
        print(f"   📊 结果: {sound_effects_count}个音效，{background_music_count}个背景音乐")
        print()
        
        # 性能总结
        total_end_time = time.time()
        total_duration = total_end_time - total_start_time
        
        print("⏱️ 性能总结")
        print("=" * 50)
        print(f"🎭 步骤1 - 对话分析:     {step1_duration:>8.2f}s ({step1_duration/total_duration*100:>5.1f}%)")
        print(f"🎯 步骤2 - 5卡分析:      {step2_duration:>8.2f}s ({step2_duration/total_duration*100:>5.1f}%)")
        print(f"🎬 步骤3 - 音频分镜卡:   {step3_duration:>8.2f}s ({step3_duration/total_duration*100:>5.1f}%)")
        print("-" * 50)
        print(f"📊 总耗时:             {total_duration:>8.2f}s (100.0%)")
        print(f"📈 平均每步:           {total_duration/3:>8.2f}s")
        print(f"⚡ 处理速度:           {len(test_text)/total_duration:>8.1f} 字符/秒")
        print()
        
        # 详细数据分析
        print("📋 详细结果分析")
        print("=" * 50)
        
        # 对话分析结果
        print("🎭 对话分析结果:")
        if dialogue_analysis.get('segments'):
            for i, seg in enumerate(dialogue_analysis['segments'][:3]):  # 只显示前3个
                print(f"   片段{i+1}: \"{seg.get('text', '')[:30]}...\" - {seg.get('speaker', '未知')}")
        
        # 5卡分析结果
        print("\n🎯 5卡分析结果:")
        for card_name in ['story_card', 'character_card', 'scene_card', 'event_card', 'emotion_card']:
            card_data = six_card_result.get(card_name, {})
            if card_data:
                key_count = len(card_data.keys())
                print(f"   {card_name}: {key_count}个字段")
        
        # 音频分镜卡结果
        print("\n🎬 音频分镜卡结果:")
        audio_card = complete_result.get('audio_storyboard_card', {})
        if audio_card:
            timeline = audio_card.get('timeline', {})
            print(f"   时间轴: {timeline.get('total_duration', 0)}秒，{len(timeline.get('segments', []))}个片段")
            print(f"   语音分配: {len(audio_card.get('voice_assignments', {}))}个角色")
            print(f"   音效配置: {len(audio_card.get('sound_effects', []))}个音效")
            print(f"   背景音乐: {'有' if audio_card.get('background_music') else '无'}")
        
        print("\n🎉 性能分析完成！")
        return True
        
    except Exception as e:
        print(f"❌ 性能测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

async def run_multiple_tests(count=3):
    """运行多次测试获取平均性能"""
    print(f"🔄 运行 {count} 次测试获取平均性能...")
    print("=" * 60)
    
    all_durations = []
    
    for i in range(count):
        print(f"\n🧪 第 {i+1}/{count} 次测试")
        print("-" * 30)
        
        start_time = time.time()
        success = await performance_analysis_test()
        end_time = time.time()
        
        if success:
            duration = end_time - start_time
            all_durations.append(duration)
            print(f"✅ 测试 {i+1} 完成: {duration:.2f}s")
        else:
            print(f"❌ 测试 {i+1} 失败")
    
    if all_durations:
        avg_duration = sum(all_durations) / len(all_durations)
        min_duration = min(all_durations)
        max_duration = max(all_durations)
        
        print("\n📊 多次测试性能总结")
        print("=" * 60)
        print(f"✅ 成功测试: {len(all_durations)}/{count} 次")
        print(f"⚡ 平均耗时: {avg_duration:.2f}s")
        print(f"🚀 最快耗时: {min_duration:.2f}s")
        print(f"🐌 最慢耗时: {max_duration:.2f}s")
        print(f"📈 性能稳定性: {(max_duration - min_duration)/avg_duration*100:.1f}% 波动")

if __name__ == "__main__":
    # 单次详细测试
    print("🎯 单次详细性能测试")
    asyncio.run(performance_analysis_test())
    
    print("\n" + "="*60)
    
    # 多次测试获取平均性能
    asyncio.run(run_multiple_tests(3))
