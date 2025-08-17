#!/usr/bin/env python3
"""
通用环境音分析测试脚本
可以测试任意章节的环境音分析准确性
"""

import asyncio
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.narration_environment_analyzer import NarrationEnvironmentAnalyzer

# 预定义的测试数据
TEST_CHAPTERS = {
    "第一章": [
        {
            'segment_id': 'seg_1',
            'speaker': '旁白',
            'text': '夜幕降临，城南古庙笼罩在一片神秘的氛围中。',
            'estimated_duration': 7.5
        },
        {
            'segment_id': 'seg_2',
            'speaker': '旁白',
            'text': '李玄机独自一人来到古庙前，脚步声在寂静的夜晚格外清晰。',
            'estimated_duration': 5.4
        },
        {
            'segment_id': 'seg_3',
            'speaker': '旁白',
            'text': '远处传来阵阵钟声，悠扬的钟声在夜空中回荡。',
            'estimated_duration': 4.2
        },
        {
            'segment_id': 'seg_4',
            'speaker': '旁白',
            'text': '树叶沙沙作响，仿佛在诉说着古老的传说。',
            'estimated_duration': 5.0
        },
        {
            'segment_id': 'seg_5',
            'speaker': '旁白',
            'text': '吱呀一声，门轴发出刺耳的摩擦声，李玄机推开了古庙的大门。',
            'estimated_duration': 6.0
        }
    ],
    "第二章": [
        {
            'segment_id': 'seg_1',
            'speaker': '旁白',
            'text': '庙内一片漆黑，只有几盏油灯在微风中摇曳。',
            'estimated_duration': 4.2
        },
        {
            'segment_id': 'seg_2',
            'speaker': '旁白',
            'text': '油灯的火苗在微风中摇曳，发出轻微的噼啪声。',
            'estimated_duration': 4.2
        },
        {
            'segment_id': 'seg_3',
            'speaker': '旁白',
            'text': '李玄机小心翼翼地向前走去，脚步声在空旷的庙宇中回响。',
            'estimated_duration': 5.2
        },
        {
            'segment_id': 'seg_4',
            'speaker': '旁白',
            'text': '突然，身后传来一声轻响，李玄机猛地转身。',
            'estimated_duration': 4.0
        },
        {
            'segment_id': 'seg_5',
            'speaker': '旁白',
            'text': '一个黑影从暗处走出，脚步声在寂静的庙宇中格外清晰。',
            'estimated_duration': 5.0
        }
    ],
    "第三章": [
        {
            'segment_id': 'seg_1',
            'speaker': '旁白',
            'text': '手机突然震动，发出轻微的嗡鸣声。',
            'estimated_duration': 3.0
        },
        {
            'segment_id': 'seg_2',
            'speaker': '旁白',
            'text': '叮的一声，屏幕上显示了一条新消息。',
            'estimated_duration': 2.5
        },
        {
            'segment_id': 'seg_3',
            'speaker': '旁白',
            'text': '李玄机拿起手机，点击屏幕发出轻微的触控声。',
            'estimated_duration': 3.5
        },
        {
            'segment_id': 'seg_4',
            'speaker': '旁白',
            'text': '远处传来汽车引擎的轰鸣声，打破了夜晚的宁静。',
            'estimated_duration': 4.0
        },
        {
            'segment_id': 'seg_5',
            'speaker': '旁白',
            'text': '风声呼啸，吹动着窗外的树叶发出沙沙声。',
            'estimated_duration': 3.8
        }
    ]
}

async def test_chapter(chapter_name: str, synthesis_plan: list):
    """测试指定章节的环境音分析"""
    print(f"🎯 测试{chapter_name}环境音分析准确性")
    print("=" * 60)
    
    print("📖 章节内容概览:")
    print(f"   - 段落数量: {len(synthesis_plan)}")
    
    # 计算预估总时长
    estimated_total = sum(seg.get('estimated_duration', 0) for seg in synthesis_plan)
    print(f"   - 预估总时长: {estimated_total:.1f}秒")
    
    print("\n🔍 开始环境音分析...")
    print("-" * 40)
    
    try:
        # 创建分析器实例
        analyzer = NarrationEnvironmentAnalyzer()
        
        # 执行分析
        result = await analyzer.extract_and_analyze_narration(synthesis_plan)
        
        print("✅ 分析完成!")
        
        # 提取结果
        environment_tracks = result.get('environment_tracks', [])
        analysis_summary = result.get('analysis_summary', {})
        
        print(f"\n📊 分析统计:")
        print(f"   - 实际总时长: {analysis_summary.get('total_duration', 0):.1f}秒")
        print(f"   - 旁白段落: {analysis_summary.get('narration_segments', 0)}个")
        print(f"   - 环境音轨道: {len(environment_tracks)}个")
        print(f"   - 分析模式: {analysis_summary.get('analysis_mode', 'unknown')}")
        
        # 计算时长准确性
        actual_total = analysis_summary.get('total_duration', 0)
        if estimated_total > 0:
            accuracy = (1 - abs(estimated_total - actual_total) / estimated_total) * 100
            print(f"\n⏱️ 时长准确性: {accuracy:.1f}%")
            print(f"   - 预估时长: {estimated_total:.1f}秒")
            print(f"   - 实际时长: {actual_total:.1f}秒")
            print(f"   - 差异: {abs(estimated_total - actual_total):.1f}秒")
        
        print(f"\n🎵 环境音轨道详情:")
        print("-" * 40)
        
        for i, track in enumerate(environment_tracks, 1):
            keywords = track.get('environment_keywords', [])
            duration = track.get('duration', 0)
            start_time = track.get('start_time', 0)
            confidence = track.get('confidence', 0)
            mapping_strategy = track.get('mapping_strategy', 'unknown')
            text = track.get('narration_text', '')[:50] + '...'
            
            print(f"轨道 {i}:")
            print(f"   - 关键词: {keywords}")
            print(f"   - 时长: {duration:.1f}秒")
            print(f"   - 开始时间: {start_time:.1f}秒")
            print(f"   - 置信度: {confidence:.2f}")
            print(f"   - 映射策略: {mapping_strategy}")
            print(f"   - 文本: {text}")
            
            # 判断时长是否合理
            if any('叮' in kw or '砰' in kw or '响' in kw for kw in keywords):
                if duration <= 2.0:
                    print("   ✅ 正确: 瞬间声音分配了合理时长")
                else:
                    print("   ⚠️ 注意: 瞬间声音分配了过长时长")
            else:
                if duration > 2.0:
                    print("   ✅ 正确: 持续声音分配了合理时长")
                else:
                    print("   ⚠️ 注意: 持续声音分配了过短时长")
            print()
        
        # 关键词分布统计
        keyword_count = {}
        for track in environment_tracks:
            for keyword in track.get('environment_keywords', []):
                keyword_count[keyword] = keyword_count.get(keyword, 0) + 1
        
        if keyword_count:
            print("📈 关键词分布:")
            for keyword, count in sorted(keyword_count.items(), key=lambda x: x[1], reverse=True):
                print(f"   - {keyword}: {count}次")
        
        # 置信度分布
        confidence_ranges = {'高(>0.8)': 0, '中(0.5-0.8)': 0, '低(<0.5)': 0}
        for track in environment_tracks:
            confidence = track.get('confidence', 0.0)
            if confidence > 0.8:
                confidence_ranges['高(>0.8)'] += 1
            elif confidence > 0.5:
                confidence_ranges['中(0.5-0.8)'] += 1
            else:
                confidence_ranges['低(<0.5)'] += 1
        
        print(f"\n🎯 置信度分布:")
        for range_name, count in confidence_ranges.items():
            print(f"   - {range_name}: {count}个")
        
        print(f"\n🏆 总体评价:")
        print("-" * 40)
        
        # 评价标准
        if accuracy >= 80:
            print("✅ 时长准确性优秀")
        elif accuracy >= 60:
            print("⚠️ 时长准确性需要改进")
        else:
            print("❌ 时长准确性需要大幅改进")
        
        if len(environment_tracks) >= 3:
            print("✅ 识别数量充足")
        elif len(environment_tracks) >= 1:
            print("⚠️ 识别数量一般")
        else:
            print("❌ 识别数量不足")
        
        avg_confidence = sum(track.get('confidence', 0) for track in environment_tracks) / len(environment_tracks) if environment_tracks else 0
        if avg_confidence >= 0.8:
            print("✅ 识别置信度优秀")
        elif avg_confidence >= 0.6:
            print("⚠️ 识别置信度一般")
        else:
            print("❌ 识别置信度较低")
        
        print("✅ 系统运行正常")
        
        return {
            'chapter_name': chapter_name,
            'accuracy': accuracy,
            'track_count': len(environment_tracks),
            'avg_confidence': avg_confidence,
            'success': True
        }
        
    except Exception as e:
        print(f"❌ 分析失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            'chapter_name': chapter_name,
            'accuracy': 0,
            'track_count': 0,
            'avg_confidence': 0,
            'success': False,
            'error': str(e)
        }

async def test_all_chapters():
    """测试所有预定义章节"""
    print("🎯 通用环境音分析测试")
    print("=" * 60)
    
    results = []
    
    for chapter_name, synthesis_plan in TEST_CHAPTERS.items():
        result = await test_chapter(chapter_name, synthesis_plan)
        results.append(result)
        print("\n" + "="*60 + "\n")
    
    # 汇总结果
    print("📊 测试结果汇总:")
    print("-" * 40)
    
    successful_tests = [r for r in results if r['success']]
    failed_tests = [r for r in results if not r['success']]
    
    if successful_tests:
        avg_accuracy = sum(r['accuracy'] for r in successful_tests) / len(successful_tests)
        avg_track_count = sum(r['track_count'] for r in successful_tests) / len(successful_tests)
        avg_confidence = sum(r['avg_confidence'] for r in successful_tests) / len(successful_tests)
        
        print(f"✅ 成功测试: {len(successful_tests)}个")
        print(f"   - 平均时长准确性: {avg_accuracy:.1f}%")
        print(f"   - 平均识别数量: {avg_track_count:.1f}个")
        print(f"   - 平均置信度: {avg_confidence:.2f}")
    
    if failed_tests:
        print(f"❌ 失败测试: {len(failed_tests)}个")
        for test in failed_tests:
            print(f"   - {test['chapter_name']}: {test.get('error', '未知错误')}")
    
    print(f"\n🎯 总体评价:")
    if len(successful_tests) == len(results):
        print("✅ 所有测试通过")
    elif len(successful_tests) > len(failed_tests):
        print("⚠️ 大部分测试通过")
    else:
        print("❌ 大部分测试失败")

if __name__ == "__main__":
    # 检查命令行参数
    if len(sys.argv) > 1:
        chapter_name = sys.argv[1]
        if chapter_name in TEST_CHAPTERS:
            asyncio.run(test_chapter(chapter_name, TEST_CHAPTERS[chapter_name]))
        else:
            print(f"❌ 未知章节: {chapter_name}")
            print(f"可用章节: {list(TEST_CHAPTERS.keys())}")
    else:
        asyncio.run(test_all_chapters())
