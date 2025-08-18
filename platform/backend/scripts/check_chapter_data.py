#!/usr/bin/env python3
"""
检查数据库中的章节数据
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import get_db
from app.models.book_chapter import BookChapter
from app.models.analysis_result import AnalysisResult

def check_chapter_data():
    """检查数据库中的章节数据"""
    print("🔍 查看数据库中的章节数据")
    print("=" * 60)
    
    db = next(get_db())
    
    try:
        # 检查第二章
        chapter = db.query(BookChapter).filter(BookChapter.id == 837).first()
        
        if not chapter:
            print("❌ 未找到章节 837")
            return
        
        print(f"✅ 找到章节 {chapter.id}: {chapter.chapter_title}")
        print(f"📖 内容长度: {len(chapter.content) if chapter.content else 0}")
        
        # 查找对应的分析结果
        analysis_result = db.query(AnalysisResult).filter(
            AnalysisResult.chapter_id == chapter.id
        ).first()
        
        if not analysis_result:
            print("❌ 未找到章节 837 的分析结果")
            return
        
        synthesis_plan = analysis_result.synthesis_plan.get('synthesis_plan', [])
        
        print(f"\n📊 synthesis_plan长度: {len(synthesis_plan)}")
        
        if not synthesis_plan:
            print("❌ synthesis_plan为空")
            return
        
        print(f"\n📋 synthesis_plan结构分析:")
        print(f"  - 总段落数: {len(synthesis_plan)}")
        
        # 分析每个段落
        narration_segments = []
        for i, segment in enumerate(synthesis_plan, 1):
            speaker = segment.get('speaker', '')
            character = segment.get('character', '')
            text = segment.get('text', '')
            
            print(f"\n段落 {i}:")
            print(f"  - Speaker: {speaker}")
            print(f"  - Character: {character}")
            print(f"  - 文本: {text[:50]}...")
            
            # 只处理旁白段落
            if speaker == '旁白' and text.strip():
                narration_segments.append({
                    'id': i,
                    'text': text,
                    'speaker': speaker
                })
                print(f"  - 类型: 旁白段落")
            else:
                print(f"  - 类型: 对话段落")
        
        print(f"\n📊 统计信息:")
        print(f"  - 总段落数: {len(synthesis_plan)}")
        print(f"  - 旁白段落数: {len(narration_segments)}")
        print(f"  - 对话段落数: {len(synthesis_plan) - len(narration_segments)}")
        
        if narration_segments:
            print(f"\n🎵 旁白段落详情:")
            for segment in narration_segments:
                print(f"  段落 {segment['id']} (ID: {segment['id']}):")
                print(f"    - 文本: {segment['text'][:50]}...")
                print(f"    - Speaker: {segment['speaker']}")
                print(f"    - Character: {segment.get('character', '')}")
                print()
        
        # 检查是否有环境音关键词
        print("🔍 环境音关键词检查:")
        for segment in narration_segments:
            text = segment['text']
            # 简单关键词检查
            sound_keywords = ['声', '音', '响', '鸣', '叫', '吼', '啸', '嗡', '叮', '咚', '啪', '砰', '步', '走', '跑', '跳', '敲', '打', '拍', '击', '撞', '摩擦']
            found_keywords = []
            for keyword in sound_keywords:
                if keyword in text:
                    found_keywords.append(keyword)
            
            if found_keywords:
                print(f"  段落 {segment['id']}: 发现声音关键词: {found_keywords}")
                print(f"    原文: {text}")
        
    except Exception as e:
        print(f"❌ 检查失败: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    check_chapter_data()
