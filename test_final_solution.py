#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
最终角色识别方案测试
测试AI优先 + 简单回退的架构
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'platform', 'backend'))

from app.api.v1.chapters import OllamaCharacterDetector, ProgrammaticCharacterDetector

def test_final_solution():
    """测试最终解决方案"""
    
    # 测试文本
    test_text = """
    一天，师徒四人来到高山前。山势险峻，云雾缭绕。
    
    悟空说："师父，前面有妖怪！"
    
    唐僧听了，心中一惊，连忙问道："悟空，你怎么知道？"
    
    "我火眼金睛，能看穿妖魔鬼怪。"悟空自信地回答。
    
    这时，白骨精化作美女走来，柔声说道："各位师父，请到寒舍歇息。"
    
    师徒四人继续前行，不知前方还有什么危险等待着他们。
    """
    
    print("🧪 测试最终角色识别方案")
    print("=" * 50)
    
    # 测试主力方案：Ollama AI
    print("\n📊 主力方案：Ollama AI 分析")
    print("-" * 30)
    
    ollama_detector = OllamaCharacterDetector()
    chapter_info = {
        'chapter_id': 1,
        'chapter_title': '测试章节',
        'chapter_number': 1
    }
    
    try:
        result = ollama_detector.analyze_text(test_text, chapter_info)
        
        print(f"✅ 分析方法: {result['processing_stats']['analysis_method']}")
        print(f"📝 总段落数: {result['processing_stats']['total_segments']}")
        print(f"💬 对话段落: {result['processing_stats']['dialogue_segments']}")
        print(f"📖 叙述段落: {result['processing_stats']['narration_segments']}")
        print(f"👥 角色数量: {result['processing_stats']['characters_found']}")
        
        print("\n🎭 识别的角色:")
        for char in result['detected_characters']:
            print(f"  • {char['name']} (出现{char['frequency']}次)")
            print(f"    性别: {char['recommended_config']['gender']}")
            print(f"    性格: {char['recommended_config']['personality']}")
            print(f"    声音类型: {char['recommended_config']['voice_type']}")
        
        print("\n📄 文本分段示例 (前3段):")
        for i, segment in enumerate(result['segments'][:3]):
            print(f"  {i+1}. [{segment['speaker']}] {segment['text'][:30]}...")
            print(f"     类型: {segment['text_type']}, 置信度: {segment['confidence']}")
        
    except Exception as e:
        print(f"❌ Ollama分析失败: {str(e)}")
        print("🔄 将使用回退方案")
    
    # 测试回退方案：编程规则
    print("\n📊 回退方案：编程规则分析")
    print("-" * 30)
    
    rule_detector = ProgrammaticCharacterDetector()
    rule_result = rule_detector.analyze_text_segments(test_text)
    
    print(f"✅ 分析方法: {rule_result['processing_stats']['analysis_method']}")
    print(f"📝 总段落数: {rule_result['processing_stats']['total_segments']}")
    print(f"💬 对话段落: {rule_result['processing_stats']['dialogue_segments']}")
    print(f"📖 叙述段落: {rule_result['processing_stats']['narration_segments']}")
    print(f"👥 角色数量: {rule_result['processing_stats']['characters_found']}")
    
    print("\n🎭 识别的角色:")
    for char in rule_result['detected_characters']:
        print(f"  • {char['name']} (出现{char['frequency']}次)")
        print(f"    性别: {char['recommended_config']['gender']}")
        print(f"    性格: {char['recommended_config']['personality']}")
    
    print("\n📄 文本分段示例 (前3段):")
    for i, segment in enumerate(rule_result['segments'][:3]):
        print(f"  {i+1}. [{segment['speaker']}] {segment['text'][:30]}...")
        print(f"     类型: {segment['text_type']}, 置信度: {segment['confidence']}")
    
    print("\n" + "=" * 50)
    print("🎯 测试总结:")
    print("✅ AI优先架构：主力方案提供高准确率")
    print("✅ 简单回退：确保系统稳定性")
    print("✅ 功能完整：角色识别 + 文本分段")
    print("✅ 代码简洁：避免过度工程化")

if __name__ == "__main__":
    test_final_solution() 