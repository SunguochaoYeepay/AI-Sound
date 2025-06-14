#!/usr/bin/env python3
"""
调试角色名提取过程
"""

import re
from typing import Optional

def debug_character_extraction():
    """调试角色名提取"""
    
    test_text = "白骨精不胜欢喜，自言自语道："造化！都说吃了唐僧肉可以长生不老。"
    
    print(f"测试文本: {test_text}")
    print()
    
    # 测试混合文本检测
    action_patterns = [
        r'([一-龯]{2,6})[^，。！？]*?[说道讲叫喊问答回复表示][:：]\s*[""''「」『』]',
        r'([一-龯]{2,6})[^，。！？]*?自言自语道[:：]\s*[""''「」『』]'
    ]
    
    print("=== 测试动作模式匹配 ===")
    for i, pattern in enumerate(action_patterns):
        match = re.search(pattern, test_text)
        print(f"模式 {i+1}: {pattern}")
        if match:
            print(f"  匹配成功: '{match.group(1)}'")
            potential_speaker = match.group(1)
            
            # 测试角色名提取
            print(f"  提取角色名...")
            extracted_name = extract_character_name_from_action(potential_speaker)
            print(f"  提取结果: '{extracted_name}'")
            
            if extracted_name:
                print(f"  验证角色名: {is_valid_character_name(extracted_name)}")
        else:
            print(f"  匹配失败")
        print()

def extract_character_name_from_action(action_text: str) -> Optional[str]:
    """从说话动作文本中提取角色名"""
    print(f"    输入文本: '{action_text}'")
    
    # 常见的角色名模式
    character_patterns = [
        # 直接匹配常见角色名
        r'(孙悟空|唐僧|猪八戒|沙僧|白骨精|观音|如来|玉帝)',
        # 匹配以特定字开头的角色名
        r'(白[一-龯]{1,2})',  # 白骨精、白娘子等
        r'(孙[一-龯]{1,2})',  # 孙悟空等
        r'(唐[一-龯]{0,2})',  # 唐僧等
        # 通用模式：去掉修饰词后的2-4字角色名
        r'(?:不胜|十分|非常|很是|颇为|甚是|极其)?([一-龯]{2,4})(?:不胜|十分|非常|很是|颇为|甚是|极其|欢喜|愤怒|高兴|悲伤|惊讶|害怕|着急|焦急)?'
    ]
    
    for i, pattern in enumerate(character_patterns):
        match = re.search(pattern, action_text)
        print(f"    模式 {i+1}: {pattern}")
        if match:
            candidate = match.group(1)
            print(f"      匹配: '{candidate}'")
            # 验证候选角色名
            if is_valid_character_name(candidate):
                print(f"      验证通过，返回: '{candidate}'")
                return candidate
            else:
                print(f"      验证失败")
        else:
            print(f"      无匹配")
    
    print(f"    无有效角色名")
    return None

def is_valid_character_name(name: str) -> bool:
    """验证角色名是否有效"""
    if not name or len(name) < 2 or len(name) > 6:
        print(f"      长度验证失败: {len(name)}")
        return False
    
    excluded_words = [
        '这个', '那个', '什么', '哪里', '为什么', '怎么',
        '可是', '但是', '所以', '因为', '如果', '虽然',
        '遇到', '慢慢', '而这', '这一', '那一', '当他', '当她',
        '此时', '此后', '然后', '接着', '最后', '从那', '经过',
        '神奇', '在一', '正发', '无奈', '尽管'
    ]
    
    if name in excluded_words:
        print(f"      排除词验证失败: '{name}'")
        return False
    
    # 检查是否包含标点符号
    if any(punct in name for punct in ['。', '，', '！', '？', '；']):
        print(f"      标点符号验证失败")
        return False
    
    # 检查是否为中文姓名
    if not re.match(r'^[一-龯]{2,6}$', name):
        print(f"      中文姓名验证失败")
        return False
    
    print(f"      验证通过")
    return True

if __name__ == "__main__":
    debug_character_extraction() 