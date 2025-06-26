#!/usr/bin/env python3
"""
测试AI驱动的角色识别改进
验证新的角色名验证和性别推断功能
"""

import sys
import os
sys.path.insert(0, os.path.abspath('.'))

from app.api.v1.chapters import ProgrammaticCharacterDetector, OllamaCharacterDetector


def test_character_name_validation():
    """测试AI驱动的角色名验证"""
    print("🤖 测试AI驱动的角色名验证功能")
    print("=" * 50)
    
    detector = ProgrammaticCharacterDetector()
    
    # 测试用例
    test_cases = [
        # 应该有效的角色名
        ("林渊", "should be valid"),
        ("导师", "should be valid"),
        ("将领", "should be valid"),
        ("孙悟空", "should be valid"),
        ("白骨精", "should be valid"),
        ("旁白", "should be valid"),
        ("叙述者", "should be valid"),
        
        # 应该无效的
        ("什么", "should be invalid"),
        ("但是", "should be invalid"),
        ("所以", "should be invalid"),
        ("怎么", "should be invalid"),
        ("这个", "should be invalid"),
        ("那个", "should be invalid"),
    ]
    
    print("角色名验证测试结果：")
    for name, expected in test_cases:
        is_valid = detector.is_valid_character_name(name)
        status = "✅ PASS" if (is_valid and "valid" in expected) or (not is_valid and "invalid" in expected) else "❌ FAIL"
        print(f"{status} '{name}' -> {is_valid} ({expected})")


def test_gender_inference():
    """测试AI驱动的性别推断"""
    print("\n🤖 测试AI驱动的性别推断功能")
    print("=" * 50)
    
    detector = OllamaCharacterDetector()
    
    # 测试用例
    test_cases = [
        ("林渊", "应该推断为男性或未知"),
        ("孙悟空", "应该推断为男性"),
        ("白骨精", "应该推断为女性"),
        ("观音菩萨", "应该推断为中性或女性"),
        ("旁白", "应该推断为中性"),
        ("导师", "应该推断为未知或男性"),
        ("将领", "应该推断为男性或未知"),
    ]
    
    print("性别推断测试结果：")
    for name, description in test_cases:
        try:
            gender = detector._ai_infer_gender(name)
            print(f"'{name}' -> {gender} ({description})")
        except Exception as e:
            print(f"❌ '{name}' -> 错误: {str(e)}")


def test_comprehensive_analysis():
    """测试综合分析"""
    print("\n🧠 测试综合AI角色分析")
    print("=" * 50)
    
    test_text = """
    林渊冷笑一声："你又是何人？"
    导师缓缓说道："我是来指导你的。"
    将领怒声道："放肆！"
    只见山势险峻，峰岩陡峭。
    """
    
    detector = ProgrammaticCharacterDetector()
    result = detector.analyze_text_segments(test_text)
    
    print(f"识别到 {len(result['detected_characters'])} 个角色：")
    for char in result['detected_characters']:
        print(f"- {char['name']}: 出现{char['frequency']}次, 性别:{char['recommended_config']['gender']}")


if __name__ == "__main__":
    print("🚀 开始测试AI驱动的角色识别改进")
    print("注意：需要Ollama服务运行并可用")
    print()
    
    try:
        test_character_name_validation()
        test_gender_inference()
        test_comprehensive_analysis()
        
        print("\n✅ 测试完成！")
        print("💡 现在角色识别系统使用AI进行智能判断，不再依赖硬编码规则")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {str(e)}")
        print("💡 请确保Ollama服务正在运行并可访问") 