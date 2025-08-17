#!/usr/bin/env python3
"""
测试第三章环境音分析准确性
"""

import asyncio
import sys
import os

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.narration_environment_analyzer import NarrationEnvironmentAnalyzer

async def test_chapter3_accuracy():
    """测试第三章环境音分析准确性"""
    print("🎯 测试第三章环境音分析准确性")
    print("=" * 60)
    
    # 创建分析器
    analyzer = NarrationEnvironmentAnalyzer()
    
    # 第三章的synthesis_plan数据
    synthesis_plan = [
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
            'estimated_duration': 8.2
        },
        {
            'segment_id': 'seg_3',
            'speaker': '旁白', 
            'text': '远处传来阵阵钟声，悠扬的钟声在夜空中回荡。',
            'estimated_duration': 7.8
        },
        {
            'segment_id': 'seg_4',
            'speaker': '旁白',
            'text': '突然，一阵风吹过，树叶沙沙作响，打破了夜晚的宁静。',
            'estimated_duration': 8.5
        },
        {
            'segment_id': 'seg_5',
            'speaker': '旁白',
            'text': '李玄机推开古庙的大门，吱呀一声，门轴发出刺耳的摩擦声。',
            'estimated_duration': 9.0
        },
        {
            'segment_id': 'seg_6',
            'speaker': '旁白',
            'text': '庙内一片漆黑，只有几盏油灯发出微弱的光芒。',
            'estimated_duration': 6.8
        },
        {
            'segment_id': 'seg_7',
            'speaker': '旁白',
            'text': '油灯的火苗在微风中摇曳，发出轻微的噼啪声。',
            'estimated_duration': 7.2
        },
        {
            'segment_id': 'seg_8',
            'speaker': '旁白',
            'text': '李玄机小心翼翼地向前走去，脚步声在空旷的庙宇中回响。',
            'estimated_duration': 8.8
        },
        {
            'segment_id': 'seg_9',
            'speaker': '旁白',
            'text': '突然，身后传来一声轻响，李玄机猛地转身。',
            'estimated_duration': 6.5
        },
        {
            'segment_id': 'seg_10',
            'speaker': '旁白',
            'text': '一个黑影从暗处走出，脚步声在寂静的庙宇中格外清晰。',
            'estimated_duration': 8.0
        }
    ]
    
    print(f"📖 第三章内容概览:")
    print(f"   - 段落数量: {len(synthesis_plan)}")
    print(f"   - 预估总时长: {sum(seg['estimated_duration'] for seg in synthesis_plan):.1f}秒")
    print()
    
    # 计算预估时长
    estimated_total = sum(seg['estimated_duration'] for seg in synthesis_plan)
    
    print("🔍 开始环境音分析...")
    print("-" * 40)
    
    try:
        # 执行分析
        result = await analyzer.extract_and_analyze_narration(synthesis_plan)
        
        # 获取分析结果
        environment_tracks = result['environment_tracks']
        analysis_summary = result['analysis_summary']
        
        print("✅ 分析完成!")
        print()
        
        # 显示分析统计
        print("📊 分析统计:")
        print(f"   - 实际总时长: {analysis_summary['total_duration']:.1f}秒")
        print(f"   - 旁白段落: {analysis_summary['narration_segments']}个")
        print(f"   - 环境音轨道: {analysis_summary['environment_tracks_detected']}个")
        print(f"   - 分析模式: {analysis_summary['analysis_mode']}")
        print()
        
        # 计算时长准确性
        actual_total = analysis_summary['total_duration']
        accuracy = (1 - abs(estimated_total - actual_total) / estimated_total) * 100
        print(f"⏱️ 时长准确性: {accuracy:.1f}%")
        print(f"   - 预估时长: {estimated_total:.1f}秒")
        print(f"   - 实际时长: {actual_total:.1f}秒")
        print(f"   - 差异: {abs(estimated_total - actual_total):.1f}秒")
        print()
        
        # 显示环境音轨道详情
        if environment_tracks:
            print("🎵 环境音轨道详情:")
            print("-" * 40)
            
            for i, track in enumerate(environment_tracks, 1):
                keywords = track['environment_keywords']
                duration = track['duration']
                start_time = track['start_time']
                confidence = track['confidence']
                narration_text = track['narration_text']
                
                print(f"轨道 {i}:")
                print(f"   - 关键词: {keywords}")
                print(f"   - 时长: {duration:.1f}秒")
                print(f"   - 开始时间: {start_time:.1f}秒")
                print(f"   - 置信度: {confidence:.2f}")
                print(f"   - 映射策略: {track['mapping_strategy']}")
                print(f"   - 文本: {narration_text[:50]}...")
                print()
                
                # 检查时长合理性
                instant_sounds = ['叮', '砰', '啪', '咚', '响', '震动', '手机震动声', '吱呀声', '轻响']
                continuous_sounds = ['空调声', '雨声', '风声', '雷声', '脚步声', '马蹄声', '水声', '钟声', '树叶声', '火苗声', '噼啪声']
                
                has_instant = any(sound in str(keywords) for sound in instant_sounds)
                has_continuous = any(sound in str(keywords) for sound in continuous_sounds)
                
                if has_instant and duration > 3.0:
                    print(f"   ⚠️ 注意: 瞬间声音 '{keywords}' 分配了 {duration:.1f}s 时长")
                elif has_instant and duration <= 3.0:
                    print(f"   ✅ 正确: 瞬间声音 '{keywords}' 分配了 {duration:.1f}s 时长")
                elif has_continuous:
                    print(f"   ✅ 正确: 持续声音 '{keywords}' 分配了 {duration:.1f}s 时长")
                else:
                    print(f"   ✅ 正常: 未知类型声音 '{keywords}' 分配了 {duration:.1f}s 时长")
                print()
        else:
            print("❌ 未检测到任何环境音")
            print()
        
        # 关键词分布统计
        if environment_tracks:
            keyword_count = {}
            for track in environment_tracks:
                for keyword in track.get('environment_keywords', []):
                    keyword_count[keyword] = keyword_count.get(keyword, 0) + 1
            
            print("📈 关键词分布:")
            for keyword, count in sorted(keyword_count.items(), key=lambda x: x[1], reverse=True):
                print(f"   - {keyword}: {count}次")
            print()
        
        # 置信度分布
        if environment_tracks:
            confidence_ranges = {'高(>0.8)': 0, '中(0.5-0.8)': 0, '低(<0.5)': 0}
            for track in environment_tracks:
                confidence = track.get('confidence', 0.0)
                if confidence > 0.8:
                    confidence_ranges['高(>0.8)'] += 1
                elif confidence > 0.5:
                    confidence_ranges['中(0.5-0.8)'] += 1
                else:
                    confidence_ranges['低(<0.5)'] += 1
            
            print("🎯 置信度分布:")
            for range_name, count in confidence_ranges.items():
                print(f"   - {range_name}: {count}个")
            print()
        
        # 总体评价
        print("🏆 总体评价:")
        print("-" * 40)
        
        if accuracy >= 80:
            print(f"✅ 时长准确性优秀 ({accuracy:.1f}%)")
        elif accuracy >= 60:
            print(f"⚠️ 时长准确性良好 ({accuracy:.1f}%)")
        else:
            print(f"❌ 时长准确性需要改进 ({accuracy:.1f}%)")
        
        if environment_tracks:
            avg_confidence = sum(track['confidence'] for track in environment_tracks) / len(environment_tracks)
            if avg_confidence >= 0.7:
                print(f"✅ 识别置信度优秀 ({avg_confidence:.2f})")
            elif avg_confidence >= 0.5:
                print(f"⚠️ 识别置信度良好 ({avg_confidence:.2f})")
            else:
                print(f"❌ 识别置信度需要改进 ({avg_confidence:.2f})")
        
        print(f"✅ 系统运行正常")
        print()
        
    except Exception as e:
        print(f"❌ 分析失败: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_chapter3_accuracy())
