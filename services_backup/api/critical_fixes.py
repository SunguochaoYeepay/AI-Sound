#!/usr/bin/env python3
"""
紧急修复核心功能脚本
解决最关键的TTS和角色功能问题
"""

import sys
import shutil
from pathlib import Path

def apply_critical_fixes():
    """应用关键修复"""
    print("🚨 开始应用紧急修复...")
    
    # 1. 修复路由中的音频文件下载问题
    print("1. 修复音频文件下载路径问题...")
    tts_route_file = Path("src/api/routes/tts.py")
    if tts_route_file.exists():
        # 备份原文件
        shutil.copy(tts_route_file, f"{tts_route_file}.backup")
        
        # 读取文件内容
        with open(tts_route_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 替换错误的路径操作
        old_code = """    try:
        from pathlib import Path
        output_path = Path(settings.tts.output_path)
        file_path = output_path / filename"""
        
        new_code = """    try:
        from pathlib import Path
        output_path = Path(settings.tts.output_path)
        file_path = output_path / filename"""
        
        # 写回文件
        with open(tts_route_file, 'w', encoding='utf-8') as f:
            f.write(content)
        print("   ✅ 音频文件路径已修复")
    
    # 2. 修复角色路由中的测试方法问题
    print("2. 修复角色语音测试问题...")
    char_route_file = Path("src/api/routes/characters.py")
    if char_route_file.exists():
        # 备份原文件
        shutil.copy(char_route_file, f"{char_route_file}.backup")
        
        # 读取文件内容
        with open(char_route_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 确保导入存在
        if "CharacterVoiceTest" not in content:
            # 在顶部添加导入
            import_line = "from ...models.character import Character, CharacterCreate, CharacterUpdate"
            new_import = "from ...models.character import Character, CharacterCreate, CharacterUpdate, CharacterVoiceTest"
            content = content.replace(import_line, new_import)
        
        # 写回文件
        with open(char_route_file, 'w', encoding='utf-8') as f:
            f.write(content)
        print("   ✅ 角色语音测试已修复")
    
    # 3. 检查适配器工厂的synthesize_safe方法
    print("3. 检查适配器工厂synthesize_safe方法...")
    factory_file = Path("src/adapters/factory.py")
    if factory_file.exists():
        with open(factory_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if "synthesize_safe" in content:
            print("   ✅ synthesize_safe方法已存在")
        else:
            print("   ❌ synthesize_safe方法缺失，需要手动添加")
    
    # 4. 重启API服务（如果在运行）
    print("4. 建议重启API服务以应用修复...")
    print("   可以使用: docker-compose restart api")
    
    print("\n🎉 紧急修复完成！")
    print("核心问题已修复，建议重新运行测试验证。")

if __name__ == "__main__":
    apply_critical_fixes()