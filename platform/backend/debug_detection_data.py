#!/usr/bin/env python3
"""
调试智能检测数据读取问题
"""
import sys
import os
import json

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import get_db
from app.models import AnalysisResult, BookChapter

def debug_detection_data(chapter_id=339):
    """调试章节339的检测数据"""
    db = next(get_db())
    
    print(f"=== 调试章节 {chapter_id} 的智能检测数据 ===")
    
    try:
        # 1. 获取章节信息
        chapter = db.query(BookChapter).filter(BookChapter.id == chapter_id).first()
        if not chapter:
            print(f"❌ 章节 {chapter_id} 不存在")
            return
        
        print(f"📖 章节信息:")
        print(f"   ID: {chapter.id}")
        print(f"   标题: {chapter.chapter_title}")
        print(f"   书籍ID: {chapter.book_id}")
        
        # 2. 获取分析结果
        analysis_result = db.query(AnalysisResult).filter(
            AnalysisResult.chapter_id == chapter_id
        ).order_by(AnalysisResult.created_at.desc()).first()
        
        if not analysis_result:
            print(f"❌ 章节 {chapter_id} 没有分析结果")
            return
        
        print(f"\n🧠 分析结果:")
        print(f"   结果ID: {analysis_result.id}")
        print(f"   状态: {analysis_result.status}")
        print(f"   创建时间: {analysis_result.created_at}")
        print(f"   更新时间: {analysis_result.updated_at}")
        
        # 3. 检查synthesis_plan数据
        segments_from_synthesis_plan = []
        if analysis_result.synthesis_plan and 'synthesis_plan' in analysis_result.synthesis_plan:
            segments_from_synthesis_plan = analysis_result.synthesis_plan['synthesis_plan']
        
        print(f"\n📊 synthesis_plan数据:")
        print(f"   段落数量: {len(segments_from_synthesis_plan)}")
        
        if segments_from_synthesis_plan:
            # 检查前3个段落的speaker信息
            for i, segment in enumerate(segments_from_synthesis_plan[:3]):
                speaker = segment.get('speaker', '未知')
                text_type = segment.get('text_type', '未知')
                text = segment.get('text', '')[:50]
                print(f"   段落{i}: speaker='{speaker}', type='{text_type}', text='{text}...'")
        
        # 4. 检查final_config数据
        segments_from_final_config = []
        if analysis_result.final_config:
            try:
                final_config_data = json.loads(analysis_result.final_config)
                if 'synthesis_json' in final_config_data and 'synthesis_plan' in final_config_data['synthesis_json']:
                    segments_from_final_config = final_config_data['synthesis_json']['synthesis_plan']
            except Exception as e:
                print(f"   ❌ 解析final_config失败: {str(e)}")
        
        print(f"\n💾 final_config数据:")
        print(f"   段落数量: {len(segments_from_final_config)}")
        
        if segments_from_final_config:
            # 检查所有段落的speaker信息，特别是有问题的段落
            for i, segment in enumerate(segments_from_final_config):
                speaker = segment.get('speaker', '未知')
                character = segment.get('character', '未知')  # 检测服务使用的字段
                text_type = segment.get('text_type', '未知')
                text = segment.get('text', '')[:50]
                # 特别标记可能有问题的段落
                if text_type == 'dialogue' and not character:  # 使用检测服务的逻辑
                    print(f"   ❌ 段落{i}: speaker='{speaker}', character='{character}', type='{text_type}', text='{text}...' [问题段落]")
                elif i < 5:  # 显示前5个段落
                    print(f"   段落{i}: speaker='{speaker}', character='{character}', type='{text_type}', text='{text}...'")
            
            # 统计有问题的段落 - 使用检测服务的逻辑
            problem_segments = [i for i, seg in enumerate(segments_from_final_config) 
                              if seg.get('text_type') == 'dialogue' and not seg.get('character')]
            print(f"   🚨 final_config中有问题的段落索引(按character字段): {problem_segments}")
            
            problem_segments_speaker = [i for i, seg in enumerate(segments_from_final_config) 
                              if seg.get('text_type') == 'dialogue' and not seg.get('speaker')]
            print(f"   🚨 final_config中有问题的段落索引(按speaker字段): {problem_segments_speaker}")
        
        # 5. 比较两个数据源
        print(f"\n🔍 数据对比:")
        if len(segments_from_synthesis_plan) != len(segments_from_final_config):
            print(f"   ❌ 段落数量不一致: synthesis_plan={len(segments_from_synthesis_plan)}, final_config={len(segments_from_final_config)}")
        else:
            print(f"   ✅ 段落数量一致: {len(segments_from_synthesis_plan)}")
        
        # 检查speaker差异
        speaker_diff_count = 0
        for i in range(min(len(segments_from_synthesis_plan), len(segments_from_final_config))):
            original_speaker = segments_from_synthesis_plan[i].get('speaker', '')
            final_speaker = segments_from_final_config[i].get('speaker', '')
            if original_speaker != final_speaker:
                speaker_diff_count += 1
                print(f"   段落{i}: speaker变化 '{original_speaker}' → '{final_speaker}'")
        
        if speaker_diff_count == 0:
            print(f"   ❌ 没有发现speaker变化，这可能是问题所在！")
        else:
            print(f"   ✅ 发现{speaker_diff_count}个段落的speaker有变化")
        
        # 6. 模拟智能检测逻辑
        print(f"\n🔍 模拟智能检测:")
        
        # 使用final_config数据（如果有）
        segments_to_check = segments_from_final_config if segments_from_final_config else segments_from_synthesis_plan
        
        character_mismatch_count = 0
        for i, segment in enumerate(segments_to_check):
            text_type = segment.get('text_type', 'dialogue')
            speaker = segment.get('speaker', '')
            
            if text_type == 'dialogue' and not speaker:
                character_mismatch_count += 1
                print(f"   问题段落{i}: text_type='{text_type}', speaker='{speaker}'")
        
        print(f"   检测到{character_mismatch_count}个character_mismatch问题")
        
        if character_mismatch_count > 0:
            print(f"   💡 建议: 数据可能没有正确保存修复结果")
        else:
            print(f"   ✅ 没有检测到问题，修复可能已生效")
            
    except Exception as e:
        print(f"❌ 调试过程中出错: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    debug_detection_data() 