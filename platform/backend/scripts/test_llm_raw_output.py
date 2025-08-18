#!/usr/bin/env python3
"""
测试LLM对第二章的原始输出
"""

import sys
import os
import asyncio

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import get_db
from app.models.book_chapter import BookChapter
from app.models.analysis_result import AnalysisResult
from app.services.llm_scene_analyzer import llm_scene_analyzer

async def test_llm_raw_output():
    """测试LLM对第二章的原始输出"""
    print("🔍 测试LLM对第二章的原始输出")
    print("=" * 60)
    
    db = next(get_db())
    
    try:
        # 获取第二章数据
        chapter = db.query(BookChapter).filter(BookChapter.id == 837).first()
        
        if not chapter:
            print("❌ 未找到章节 837")
            return
        
        print(f"✅ 找到章节 {chapter.id}: {chapter.chapter_title}")
        
        # 获取分析结果
        analysis_result = db.query(AnalysisResult).filter(
            AnalysisResult.chapter_id == chapter.id
        ).first()
        
        if not analysis_result:
            print("❌ 未找到章节 837 的分析结果")
            return
        
        synthesis_plan = analysis_result.synthesis_plan.get('synthesis_plan', [])
        
        if not synthesis_plan:
            print("❌ synthesis_plan为空")
            return
        
        print(f"📊 synthesis_plan长度: {len(synthesis_plan)}")
        
        # 提取旁白段落
        narration_segments = []
        for i, segment in enumerate(synthesis_plan, 1):
            speaker = segment.get('speaker', '')
            text = segment.get('text', '')
            
            if speaker == '旁白' and text.strip():
                narration_segments.append({
                    'id': i,
                    'text': text
                })
        
        print(f"🎵 旁白段落数: {len(narration_segments)}")
        
        # 构建LLM提示词
        prompt_text = "请分析以下文本中的环境音，严格按照以下要求：\n\n"
        prompt_text += "🎯 核心要求：\n"
        prompt_text += "1. 只识别文本中明确提到的声音\n"
        prompt_text += "2. 关键词要简洁，2-4个字符\n"
        prompt_text += "3. 不要包含时间、强度等描述性信息\n"
        prompt_text += "4. 不要包含分析过程或格式标记\n"
        prompt_text += "5. 不要进行任何联想\n"
        prompt_text += "6. 瞬间声音用简洁词汇：叮、砰、响、震动等\n"
        prompt_text += "7. 持续声音用标准词汇：脚步声、说话声、马蹄声等\n\n"
        
        for i, segment in enumerate(narration_segments, 1):
            prompt_text += f"段落{i}: {segment['text']}\n"
        
        prompt_text += "\n⚠️ 重要：必须为每个段落都返回结果，格式如下：\n"
        for i in range(1, len(narration_segments) + 1):
            prompt_text += f"段落{i}: [\"关键词1\", \"关键词2\"]\n"
        
        prompt_text += "\n要求：\n"
        prompt_text += "- 每个段落最多3个关键词\n"
        prompt_text += "- 关键词简洁准确\n"
        prompt_text += "- 无声音的段落必须返回[]\n"
        prompt_text += "- 不要解释，直接返回结果\n"
        prompt_text += "- 瞬间声音优先：叮、响、震动等\n"
        prompt_text += "- 持续声音标准：脚步声、说话声、马蹄声等\n"
        prompt_text += "- 必须按段落顺序返回，不能跳过任何段落\n"
        prompt_text += "- 必须分析完所有段落，不能提前结束"
        
        print(f"\n📝 构建的提示词长度: {len(prompt_text)}")
        print(f"📝 提示词前200字符: {prompt_text[:200]}...")
        
        # 调用LLM
        print(f"\n🤖 调用LLM分析...")
        result = await llm_scene_analyzer.analyze_text_scenes_with_llm(prompt_text)
        
        print(f"\n📊 LLM分析结果:")
        print(f"  - 处理时间: {result.processing_time:.2f}s")
        print(f"  - 置信度: {result.confidence_score:.2f}")
        print(f"  - 场景数量: {len(result.analyzed_scenes)}")
        
        print(f"\n🔍 LLM原始响应:")
        print(f"{result.raw_response}")
        
        print(f"\n📋 解析后的场景:")
        for i, scene in enumerate(result.analyzed_scenes, 1):
            print(f"  场景 {i}:")
            print(f"    - 位置: {scene.location}")
            print(f"    - 关键词: {scene.keywords}")
            print(f"    - 置信度: {scene.confidence}")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(test_llm_raw_output())
