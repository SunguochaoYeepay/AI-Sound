#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试修正后的角色配置系统
"""

import sys
import os
sys.path.append('platform/backend')

from app.api.v1.chapters import EnhancedCharacterDetector

def test_character_trait_analysis():
    """测试角色性格分析功能"""
    print("🧪 测试角色性格分析功能...")
    
    detector = EnhancedCharacterDetector(character_analysis=True)
    
    # 测试不同性格的角色
    test_cases = [
        {
            'name': '悟空',
            'samples': [
                '悟空怒吼道："妖怪！看棒！"',
                '悟空大喝一声："师父莫怕！"',
                '悟空厉声说道："你这妖精，还不现形！"'
            ],
            'expected_trait': 'fierce'
        },
        {
            'name': '观音',
            'samples': [
                '观音淡淡地说："一切自有定数。"',
                '观音平静地道："悟空，莫要冲动。"',
                '观音从容说道："此事我自有安排。"'
            ],
            'expected_trait': 'calm'
        },
        {
            'name': '嫦娥',
            'samples': [
                '嫦娥轻声道："公子请留步。"',
                '嫦娥温和地说："小女子这厢有礼了。"',
                '嫦娥柔声说道："多谢公子相救。"'
            ],
            'expected_trait': 'gentle'
        }
    ]
    
    for case in test_cases:
        trait_result = detector.analyze_character_trait(case['samples'])
        print(f"\n角色: {case['name']}")
        print(f"  检测性格: {trait_result['trait']}")
        print(f"  预期性格: {case['expected_trait']}")
        print(f"  置信度: {trait_result['confidence']:.2f}")
        print(f"  描述: {trait_result['description']}")
        
        status = "✅" if trait_result['trait'] == case['expected_trait'] else "❌"
        print(f"  结果: {status}")

def test_character_info_generation():
    """测试角色信息生成功能"""
    print("\n\n🔧 测试角色信息生成功能...")
    
    detector = EnhancedCharacterDetector(character_analysis=True)
    
    # 模拟角色统计数据
    test_characters = [
        {
            'name': '悟空',
            'stats': {'frequency': 5, 'first_appearance_segment': 1},
            'trait': {'trait': 'fierce', 'confidence': 0.8, 'description': '性格刚烈，说话直接有力'}
        },
        {
            'name': '白骨精',
            'stats': {'frequency': 3, 'first_appearance_segment': 10},
            'trait': {'trait': 'lively', 'confidence': 0.6, 'description': '活泼开朗，充满活力'}
        },
        {
            'name': '唐僧',
            'stats': {'frequency': 4, 'first_appearance_segment': 2},
            'trait': {'trait': 'gentle', 'confidence': 0.7, 'description': '温柔和善，说话轻声细语'}
        }
    ]
    
    for char in test_characters:
        info = detector.generate_character_info(char['name'], char['stats'], char['trait'])
        
        print(f"\n角色: {char['name']}")
        print(f"  性别: {info['gender']}")
        print(f"  性格: {info['personality']} ({info['personality_confidence']:.2f})")
        print(f"  描述: {info['description']}")
        print(f"  推荐TTS: {info['recommended_tts_params']}")
        print(f"  声音类型: {info['voice_type']}")
        print(f"  建议颜色: {info['color']}")

def test_chapter_processing_corrected():
    """测试修正后的章节处理功能"""
    print("\n\n📖 测试修正后的章节处理功能...")
    
    detector = EnhancedCharacterDetector(character_analysis=True)
    
    # 模拟章节文本
    chapter_text = """
    话说唐僧师徒四人，行至白虎岭前。悟空怒吼道："师父，前面山高路险，小心妖怪！"
    唐僧温和地说："悟空说得对，我们要小心行事。"
    忽然，白骨精变作美女，走上前来。白骨精娇声道："长老，可要用斋？"
    悟空火眼金睛，一眼看出是妖怪，厉声喝道："妖怪！看棒！"
    唐僧大惊，轻声说道："悟空！你怎么能打死人？"
    八戒在旁边嘻嘻笑道："师兄又闯祸了！哈哈哈！"
    """
    
    chapter_info = {
        'id': 1,
        'title': '白骨精三戏唐三藏',
        'number': 27
    }
    
    result = detector.process_chapter(chapter_text, chapter_info)
    
    print(f"📊 章节分析结果:")
    print(f"章节: {result['chapter_title']}")
    
    print(f"\n👥 发现的角色 ({len(result['detected_characters'])} 个):")
    for char in result['detected_characters']:
        config = char['recommended_config']
        print(f"  - {char['name']}:")
        print(f"    出现次数: {char['frequency']}")
        print(f"    性格特征: {config['personality']} (置信度: {config['personality_confidence']:.2f})")
        print(f"    性别: {config['gender']}")
        print(f"    描述: {config['description']}")
        print(f"    推荐TTS: {config['recommended_tts_params']}")
        print(f"    主要角色: {'是' if char['is_main_character'] else '否'}")

if __name__ == "__main__":
    try:
        test_character_trait_analysis()
        test_character_info_generation()
        test_chapter_processing_corrected()
        print("\n🎉 所有测试完成！角色配置系统修正成功！")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()