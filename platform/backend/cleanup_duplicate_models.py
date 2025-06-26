#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
清理重复模型定义脚本
统一AI-Sound项目的数据模型
"""

import os
import shutil
from pathlib import Path

def backup_file(file_path):
    """备份文件"""
    backup_path = f"{file_path}.backup"
    shutil.copy2(file_path, backup_path)
    print(f"✅ 备份文件: {backup_path}")

def cleanup_duplicate_audio_models():
    """清理重复的音频模型"""
    print("🔧 清理重复的音频模型定义")
    
    # 移除重复的audio_file.py（保留audio.py）
    duplicate_file = "app/models/audio_file.py"
    if os.path.exists(duplicate_file):
        backup_file(duplicate_file)
        os.remove(duplicate_file)
        print(f"✅ 移除重复文件: {duplicate_file}")
    
    # 移除重复的analysis.py（保留analysis_result.py和analysis_session.py）
    duplicate_analysis = "app/models/analysis.py"
    if os.path.exists(duplicate_analysis):
        backup_file(duplicate_analysis)
        os.remove(duplicate_analysis)
        print(f"✅ 移除重复文件: {duplicate_analysis}")

def update_model_imports():
    """更新模型导入"""
    print("🔧 更新模型导入文件")
    
    init_file = "app/models/__init__.py"
    if os.path.exists(init_file):
        backup_file(init_file)
        
        # 读取当前内容
        with open(init_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 移除重复导入
        content = content.replace('from .audio_file import AudioFile', '')
        content = content.replace('from .analysis import AnalysisSession, AnalysisResult', '')
        
        # 确保正确的导入存在
        imports_to_ensure = [
            "from .audio import AudioFile",
            "from .analysis_session import AnalysisSession", 
            "from .analysis_result import AnalysisResult",
        ]
        
        for import_line in imports_to_ensure:
            if import_line not in content:
                # 在合适位置添加导入
                lines = content.split('\n')
                for i, line in enumerate(lines):
                    if line.startswith('from .audio import'):
                        lines.insert(i + 1, import_line)
                        break
                content = '\n'.join(lines)
        
        # 写回文件
        with open(init_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"✅ 更新导入文件: {init_file}")

def unify_base_classes():
    """统一基类使用"""
    print("🔧 检查基类使用情况")
    
    models_dir = Path("app/models")
    base_model_files = []
    base_files = []
    
    for py_file in models_dir.glob("*.py"):
        if py_file.name in ['__init__.py', 'base.py']:
            continue
            
        with open(py_file, 'r', encoding='utf-8') as f:
            content = f.read()
            
        if 'from .base import BaseModel' in content or 'BaseModel' in content:
            base_model_files.append(py_file.name)
        elif 'from .base import Base' in content or 'class.*Base' in content:
            base_files.append(py_file.name)
    
    print(f"  使用BaseModel的文件: {base_model_files}")
    print(f"  使用Base的文件: {base_files}")
    
    if base_model_files and base_files:
        print("⚠️  发现混合使用BaseModel和Base，建议统一")
    else:
        print("✅ 基类使用统一")

def enable_commented_fields():
    """启用被注释的字段"""
    print("🔧 检查被注释的字段")
    
    files_to_check = [
        ("app/models/chapter.py", "character_count"),
        ("app/models/book_chapter.py", "character_count"),
        ("app/models/environment_sound.py", "tags"),
    ]
    
    for file_path, field_name in files_to_check:
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 查找被注释的字段
            if f"# {field_name}" in content or f"#{field_name}" in content:
                print(f"  ⚠️  发现被注释字段 {field_name} 在 {file_path}")
                print(f"     提示: 数据库修复后可以启用此字段")
            else:
                print(f"  ✅ {field_name} 字段在 {file_path} 中正常")

def main():
    """主清理流程"""
    print("🚀 开始清理重复模型定义")
    print("=" * 50)
    
    # 切换到正确目录
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    try:
        # 1. 清理重复模型
        cleanup_duplicate_audio_models()
        
        # 2. 更新导入
        update_model_imports()
        
        # 3. 检查基类统一性
        unify_base_classes()
        
        # 4. 检查被注释字段
        enable_commented_fields()
        
        print("\n" + "=" * 50)
        print("🎉 模型清理完成！")
        print("📝 备份文件已创建，如有问题可以恢复")
        
    except Exception as e:
        print(f"❌ 清理过程出错: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 