#!/usr/bin/env python3
"""
调试关键词清理函数
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_keyword_cleaning():
    """测试关键词清理函数"""
    print("🔍 调试关键词清理函数")
    print("=" * 60)
    
    # 导入分析器
    from app.services.narration_environment_analyzer import NarrationEnvironmentAnalyzer
    
    # 创建分析器实例
    analyzer = NarrationEnvironmentAnalyzer()
    
    # 测试用例
    test_cases = [
        {
            "name": "正确的关键词",
            "keywords": ["叮声", "震动声"],
            "expected": ["叮声", "震动声"]
        },
        {
            "name": "错误的关键词",
            "keywords": ["手机震动打声", "快步声", "耳畔响"],
            "expected": ["震动声", "脚步声", "响"]
        },
        {
            "name": "复杂的关键词",
            "keywords": ["发间珍珠步声", "摩擦", "蜂鸣声"],
            "expected": ["脚步声", "蜂鸣声"]
        }
    ]
    
    for test_case in test_cases:
        print(f"\n🧪 测试: {test_case['name']}")
        print(f"   输入: {test_case['keywords']}")
        
        # 调用清理函数
        cleaned = analyzer._clean_environment_keywords(test_case['keywords'])
        print(f"   输出: {cleaned}")
        print(f"   期望: {test_case['expected']}")
        
        # 检查结果
        if cleaned == test_case['expected']:
            print("   ✅ 通过")
        else:
            print("   ❌ 失败")

if __name__ == "__main__":
    test_keyword_cleaning()
