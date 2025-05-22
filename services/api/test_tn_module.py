"""
测试tn文本规范化模块
"""

import sys
import os

# 添加MegaTTS3路径
megatts_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "MegaTTS3")
if megatts_path not in sys.path:
    sys.path.insert(0, megatts_path)

# 测试导入
print("测试tn模块导入:")
try:
    import tn
    print("✓ 成功导入tn包")
    
    from tn.chinese.normalizer import Normalizer as ZhNormalizer
    print("✓ 成功导入中文规范化器")
    
    from tn.english.normalizer import Normalizer as EnNormalizer
    print("✓ 成功导入英文规范化器")
    
    # 测试使用
    zh_normalizer = ZhNormalizer(overwrite_cache=False, remove_erhua=False, remove_interjections=False)
    en_normalizer = EnNormalizer(overwrite_cache=False)
    
    # 测试中文规范化
    zh_text = "今天是2025年5月21日，气温25度，北京。"
    normalized_zh = zh_normalizer.normalize(zh_text)
    print(f"\n中文规范化测试:")
    print(f"原文: {zh_text}")
    print(f"规范化后: {normalized_zh}")
    
    # 测试英文规范化
    en_text = "Today is May 21, 2025. It's 25 degrees in Beijing."
    normalized_en = en_normalizer.normalize(en_text)
    print(f"\n英文规范化测试:")
    print(f"原文: {en_text}")
    print(f"规范化后: {normalized_en}")
    
except ImportError as e:
    print(f"导入失败: {e}")
except Exception as e:
    print(f"测试过程中发生错误: {e}") 