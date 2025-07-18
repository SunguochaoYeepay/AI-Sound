#!/usr/bin/env python3
"""
测试segment_id 2和4的具体分析问题
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.detectors.ollama_character_detector import OllamaCharacterDetector
import re

def test_segment_2():
    """测试segment_id 2的问题"""
    print("=" * 60)
    print("测试 Segment 2: 导师识别问题")
    print("=" * 60)
    
    text = '叮 ——" 手机震动打断思绪，是导师发来的消息："新出土的未央宫残简，速来。'
    
    print(f"原始文本: {text}")
    
    # 创建检测器
    detector = OllamaCharacterDetector()
    
    # 测试模式4的正则表达式
    pattern4 = r'^(.+?发来的消息)[:：]\s*([\'\"](.*?)[\'\"]\s*)$'
    match4 = re.match(pattern4, text)
    
    print(f"\n模式4正则匹配: {match4}")
    if match4:
        print(f"  匹配组1 (消息介绍): {match4.group(1)}")
        print(f"  匹配组2 (完整引号): {match4.group(2)}")
        print(f"  匹配组3 (消息内容): {match4.group(3)}")
    
    # 测试模式5的正则表达式
    pattern5 = r'^(.+?)(手机.+?消息[:：]\s*)?([\'\"](.*?)[\'\"]\s*)(.*)$'
    match5 = re.match(pattern5, text)
    
    print(f"\n模式5正则匹配: {match5}")
    if match5:
        print(f"  匹配组1 (前缀): {match5.group(1)}")
        print(f"  匹配组2 (消息部分): {match5.group(2)}")
        print(f"  匹配组3 (完整引号): {match5.group(3)}")
        print(f"  匹配组4 (对话内容): {match5.group(4)}")
        print(f"  匹配组5 (后缀): {match5.group(5)}")
    
    # 测试人工提取发送者
    print(f"\n人工提取发送者:")
    role_patterns = ['导师', '老师', '教授', '同学', '朋友', '同事', '助手', '上司', '下属']
    sender = '未知'
    for role in role_patterns:
        if role in text:
            sender = role
            break
    
    print(f"  识别的发送者: {sender}")
    
    # 人工分割建议
    print(f"\n建议分割:")
    print(f"  旁白: '叮 ——\" 手机震动打断思绪，是导师发来的消息：'")
    print(f"  导师: '新出土的未央宫残简，速来。'")

def test_segment_4():
    """测试segment_id 4的问题"""
    print("\n\n" + "=" * 60)
    print("测试 Segment 4: 将领对话分离问题")
    print("=" * 60)
    
    text = '"何人在此？" 将领勒马，长枪直指他咽喉。'
    
    print(f"原始文本: {text}")
    
    # 测试对话+动作分离的正则表达式
    pattern = r'^([\'\"](.*?)[\'\"]\s*)(.+)$'
    match = re.match(pattern, text)
    
    print(f"\n对话+动作分离正则匹配: {match}")
    if match:
        print(f"  匹配组1 (完整对话): {match.group(1)}")
        print(f"  匹配组2 (对话内容): {match.group(2)}")
        print(f"  匹配组3 (动作描述): {match.group(3)}")
    
    # 人工分割建议
    print(f"\n建议分割:")
    print(f"  将领: '何人在此？'")
    print(f"  旁白: '将领勒马，长枪直指他咽喉。'")

def test_mixed_detection():
    """测试混合句子检测功能"""
    print("\n\n" + "=" * 60)
    print("测试混合句子检测功能")
    print("=" * 60)
    
    # 创建检测器
    detector = OllamaCharacterDetector()
    
    # 模拟一个segment数据
    test_segments = [
        {
            'order': 1,
            'text': '叮 ——" 手机震动打断思绪，是导师发来的消息："新出土的未央宫残简，速来。',
            'speaker': '手机/林渊(内心)',
            'confidence': 0.9,
            'detection_rule': 'ollama_ai',
            'text_type': 'dialogue'
        },
        {
            'order': 2,
            'text': '"何人在此？" 将领勒马，长枪直指他咽喉。',
            'speaker': '将领',
            'confidence': 0.9,
            'detection_rule': 'ollama_ai',
            'text_type': 'dialogue'
        }
    ]
    
    print("原始segments:")
    for i, seg in enumerate(test_segments):
        print(f"  {i+1}. {seg['text']}")
        print(f"     speaker: {seg['speaker']}")
        print(f"     text_type: {seg['text_type']}")
    
    # 应用混合句子检测
    refined_segments = detector._detect_and_refine_mixed_sentences(test_segments)
    
    print(f"\n精细化后的segments (共{len(refined_segments)}个):")
    for i, seg in enumerate(refined_segments):
        print(f"  {i+1}. {seg['text']}")
        print(f"     speaker: {seg['speaker']}")
        print(f"     text_type: {seg['text_type']}")
        print(f"     detection_rule: {seg['detection_rule']}")

if __name__ == "__main__":
    test_segment_2()
    test_segment_4()
    test_mixed_detection() 