#!/usr/bin/env python3
"""
导入测试脚本
用于检查后端所有模块的导入是否正常
"""

import sys
import traceback

def test_import(module_name, description):
    """测试导入模块"""
    try:
        __import__(module_name)
        print(f"✅ {description}: {module_name}")
        return True
    except Exception as e:
        print(f"❌ {description}: {module_name} - {str(e)}")
        traceback.print_exc()
        return False

def main():
    print("🔍 AI-Sound Backend 导入测试")
    print("=" * 50)
    
    success_count = 0
    total_count = 0
    
    # 测试基础模块
    modules = [
        ("app.database", "数据库模块"),
        ("app.models", "数据模型"),
        ("app.utils", "工具函数"),
        ("app.tts_client", "TTS客户端"),
        ("app.voice_clone", "声音克隆"),
        ("app.characters", "角色管理"),
        ("app.books", "书籍管理"),
        ("app.novel_reader", "小说朗读"),
        ("app.audio_library", "音频库"),
        ("app.monitor", "监控模块"),
        ("app.api", "API路由"),
    ]
    
    for module_name, description in modules:
        total_count += 1
        if test_import(module_name, description):
            success_count += 1
    
    print("=" * 50)
    print(f"📊 测试结果: {success_count}/{total_count} 模块导入成功")
    
    if success_count == total_count:
        print("🎉 所有模块导入成功！")
        return 0
    else:
        print("⚠️ 部分模块导入失败，请检查错误信息")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 