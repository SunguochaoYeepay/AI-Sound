#!/usr/bin/env python3
"""
测试角色分析功能
"""

import sys
import os
sys.path.append('platform/backend')

from app.api.v1.chapters import ProgrammaticCharacterDetector

def test_character_analysis():
    """测试编程规则角色分析"""
    
    # 测试文本
    test_text = '''
一天，唐僧师徒四人来到一座高山前，只见山势险峻，峰岩重叠。
悟空刚走，唐僧就被妖怪白骨精发现了。
白骨精不胜欢喜，自言自语道："造化！都说吃了唐僧肉可以长生不老。今天机会来了！"
唐僧喝道："你为何不听劝说，把人打死一个，又打死一个？"
悟空说："师父，这妖怪变化多端，不可轻信。"
师徒们吃了桃子继续赶路。
'''
    
    print("=== 测试编程规则角色分析 ===")
    
    # 创建检测器
    detector = ProgrammaticCharacterDetector()
    
    # 分析文本
    result = detector.analyze_text_segments(test_text)
    
    # 输出结果
    print(f"总段落数: {result['processing_stats']['total_segments']}")
    print(f"对话段落数: {result['processing_stats']['dialogue_segments']}")
    print(f"旁白段落数: {result['processing_stats']['narration_segments']}")
    print(f"识别角色数: {result['processing_stats']['characters_found']}")
    print()
    
    print("识别的角色:")
    for char in result['detected_characters']:
        print(f"- {char['name']}: {char['frequency']}次, 类型: {char['recommended_config']['voice_type']}")
    print()
    
    print("文本分段:")
    for i, seg in enumerate(result['segments']):
        print(f"{i+1}. [{seg['speaker']}] ({seg['text_type']}) {seg['text'][:40]}...")
    
    print("\n=== 验证关键问题 ===")
    
    # 验证问题1: 是否有旁白
    narrator_chars = [c for c in result['detected_characters'] if c['name'] == '旁白']
    print(f"✓ 问题1 - 旁白识别: {'成功' if narrator_chars else '失败'}")
    if narrator_chars:
        print(f"  旁白出现 {narrator_chars[0]['frequency']} 次")
    
    # 验证问题2: 只有说话的角色进入声音库
    dialogue_chars = [c for c in result['detected_characters'] if c['name'] != '旁白']
    print(f"✓ 问题2 - 对话角色识别: 发现 {len(dialogue_chars)} 个对话角色")
    for char in dialogue_chars:
        print(f"  - {char['name']}: {char['frequency']}次对话")
    
    # 验证问题3: 功能复用
    print(f"✓ 问题3 - 功能复用: 使用 ProgrammaticCharacterDetector 类")
    print(f"  分析方法: {result['processing_stats']['analysis_method']}")

if __name__ == "__main__":
    test_character_analysis() 