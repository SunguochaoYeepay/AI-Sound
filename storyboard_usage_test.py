#!/usr/bin/env python3
"""
故事板分析服务使用情况验证脚本
测试 StoryboardAnalysisServiceV2 相关文件是否真的没有被使用
"""

import sys
import os
import time
import asyncio
from datetime import datetime

# 添加项目路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'platform', 'backend'))

def test_import_dependencies():
    """测试导入依赖是否正常"""
    print("🧪 测试1：检查核心分析组件导入")
    try:
        from app.services.six_card_analyzer import SixCardAnalyzer
        from app.detectors.ollama_character_detector import OllamaCharacterDetector
        print("   ✅ 核心分析组件导入正常")
        return True
    except Exception as e:
        print(f"   ❌ 核心分析组件导入失败: {e}")
        return False

def test_storyboard_service_import():
    """测试故事板服务导入"""
    print("\n🧪 测试2：检查故事板服务导入")
    try:
        from app.services.storyboard_analysis_service_v2 import StoryboardAnalysisServiceV2
        print("   ✅ StoryboardAnalysisServiceV2 可以导入")
        return True
    except Exception as e:
        print(f"   ❌ StoryboardAnalysisServiceV2 导入失败: {e}")
        return False

def test_api_imports():
    """测试API文件导入"""
    print("\n🧪 测试3：检查API文件导入")
    
    # 测试storyboard API
    try:
        from app.api.v1 import storyboard
        print("   ✅ storyboard API 可以导入")
        storyboard_import_ok = True
    except Exception as e:
        print(f"   ❌ storyboard API 导入失败: {e}")
        storyboard_import_ok = False
    
    # 测试audio_script API  
    try:
        from app.api.v1 import audio_script
        print("   ✅ audio_script API 可以导入")
        audio_script_import_ok = True
    except Exception as e:
        print(f"   ❌ audio_script API 导入失败: {e}")
        audio_script_import_ok = False
    
    return storyboard_import_ok and audio_script_import_ok

def test_route_registration():
    """测试路由注册情况"""
    print("\n🧪 测试4：检查路由注册情况")
    try:
        from app.api.v1 import api
        
        # 获取所有注册的路由
        routes = []
        for route in api.routes:
            if hasattr(route, 'path'):
                routes.append(route.path)
        
        # 检查storyboard路由
        storyboard_routes = [r for r in routes if 'storyboard' in r.lower()]
        audio_script_routes = [r for r in routes if 'audio-script' in r or 'audio_script' in r]
        
        print(f"   📊 总路由数: {len(routes)}")
        print(f"   📊 storyboard相关路由: {len(storyboard_routes)} 个")
        print(f"   📊 audio-script相关路由: {len(audio_script_routes)} 个")
        
        if storyboard_routes:
            print("   🔍 storyboard路由:")
            for route in storyboard_routes[:5]:  # 只显示前5个
                print(f"      - {route}")
        else:
            print("   ❌ 未找到storyboard相关路由")
            
        if audio_script_routes:
            print("   🔍 audio-script路由:")
            for route in audio_script_routes[:5]:  # 只显示前5个
                print(f"      - {route}")
        else:
            print("   ❌ 未找到audio-script相关路由")
        
        return len(storyboard_routes) > 0 or len(audio_script_routes) > 0
        
    except Exception as e:
        print(f"   ❌ 路由注册检查失败: {e}")
        return False

def test_database_models():
    """测试数据库模型依赖"""
    print("\n🧪 测试5：检查数据库模型依赖")
    try:
        from app.models.storyboard_cards import (
            StoryboardAnalysisSession, BaseStoryboardCard, StoryCard, 
            CharacterCard, SceneCard, EventCard, EmotionCard, 
            AudioStoryboardCard, AudioScriptCard
        )
        print("   ✅ 故事板相关数据库模型可以导入")
        return True
    except Exception as e:
        print(f"   ❌ 数据库模型导入失败: {e}")
        return False

def test_service_instantiation():
    """测试服务实例化（模拟）"""
    print("\n🧪 测试6：检查服务实例化")
    try:
        # 注意：这里不能真的创建数据库连接，只是测试类定义
        from app.services.storyboard_analysis_service_v2 import StoryboardAnalysisServiceV2
        
        # 检查类的方法
        methods = [method for method in dir(StoryboardAnalysisServiceV2) 
                  if not method.startswith('_')]
        
        print(f"   📊 StoryboardAnalysisServiceV2 公共方法数: {len(methods)}")
        print("   🔍 主要方法:")
        for method in methods[:10]:  # 只显示前10个方法
            print(f"      - {method}")
        
        return len(methods) > 0
        
    except Exception as e:
        print(f"   ❌ 服务实例化检查失败: {e}")
        return False

def test_file_deletion_simulation():
    """模拟文件删除测试"""
    print("\n🧪 测试7：模拟删除文件后的系统状态")
    
    # 记录要测试删除的文件
    files_to_test = [
        "platform/backend/app/services/storyboard_analysis_service_v2.py",
        "platform/backend/app/api/v1/storyboard.py", 
        "platform/backend/app/api/v1/audio_script.py"
    ]
    
    print("   📋 待测试删除的文件:")
    for file_path in files_to_test:
        if os.path.exists(file_path):
            size = os.path.getsize(file_path)
            print(f"      ✅ {file_path} ({size} bytes)")
        else:
            print(f"      ❌ {file_path} (不存在)")
    
    # 检查备份文件
    backup_files = [f + ".backup" for f in files_to_test] + [
        "platform/backend/app/services/storyboard_analysis_service_v2.py.full_backup"
    ]
    
    print("   📋 备份文件状态:")
    backup_count = 0
    for backup_file in backup_files:
        if os.path.exists(backup_file):
            size = os.path.getsize(backup_file)
            print(f"      ✅ {backup_file} ({size} bytes)")
            backup_count += 1
        else:
            print(f"      ❌ {backup_file} (不存在)")
    
    return backup_count >= 3  # 至少有3个备份文件

def main():
    """主测试函数"""
    print("🚀 故事板分析服务使用情况验证测试")
    print("=" * 60)
    print(f"📅 测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # 运行所有测试
    tests = [
        test_import_dependencies,
        test_storyboard_service_import,
        test_api_imports,
        test_route_registration,
        test_database_models,
        test_service_instantiation,
        test_file_deletion_simulation
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"   💥 测试执行异常: {e}")
            results.append(False)
    
    # 汇总结果
    print("\n" + "=" * 60)
    print("📊 测试结果汇总")
    print("=" * 60)
    
    passed = sum(results)
    total = len(results)
    
    print(f"✅ 通过测试: {passed}/{total}")
    print(f"❌ 失败测试: {total - passed}/{total}")
    print(f"📈 成功率: {passed/total*100:.1f}%")
    
    # 结论
    print("\n🎯 结论:")
    if passed >= 6:  # 大部分测试通过
        print("   ⚠️  故事板服务相关文件虽然可以导入和运行，")
        print("   ⚠️  但路由注册和实际使用情况需要进一步验证。")
        print("   ⚠️  建议：先临时删除文件，测试系统是否正常运行。")
    elif passed >= 4:
        print("   🤔 故事板服务存在部分问题，但基本功能可用。")
        print("   🤔 建议：谨慎删除，需要更详细的使用情况分析。")
    else:
        print("   💀 故事板服务存在严重问题，很可能是孤儿文件。")
        print("   💀 建议：可以安全删除这些文件。")
    
    print(f"\n🔚 测试完成于: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    return passed >= 4

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⏹️  测试被用户中断")
        sys.exit(2)
    except Exception as e:
        print(f"\n\n💥 测试脚本执行失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(3)
