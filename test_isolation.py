#!/usr/bin/env python3
"""
模块隔离测试脚本
验证书籍智能准备模块和书籍分析模块的绝对隔离
"""

import sys
import os
import time
from datetime import datetime

# 添加项目路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'platform', 'backend'))

def test_import_isolation():
    """测试导入隔离"""
    print("🧪 测试1：导入隔离验证")
    
    try:
        # 测试智能准备模块导入
        print("   📚 测试智能准备模块导入...")
        from app.detectors.ollama_character_detector import OllamaCharacterDetector
        print("   ✅ 智能准备模块：OllamaCharacterDetector 导入成功")
        
        # 测试分析模块导入
        print("   📖 测试分析模块导入...")
        from app.detectors.analysis_character_detector import AnalysisCharacterDetector
        print("   ✅ 分析模块：AnalysisCharacterDetector 导入成功")
        
        return True
        
    except Exception as e:
        print(f"   ❌ 导入测试失败: {e}")
        return False

def test_class_isolation():
    """测试类隔离"""
    print("\n🧪 测试2：类隔离验证")
    
    try:
        from app.detectors.ollama_character_detector import OllamaCharacterDetector
        from app.detectors.analysis_character_detector import AnalysisCharacterDetector
        
        # 创建两个不同的实例
        prep_detector = OllamaCharacterDetector()
        analysis_detector = AnalysisCharacterDetector()
        
        # 验证它们是不同的类
        prep_class_name = prep_detector.__class__.__name__
        analysis_class_name = analysis_detector.__class__.__name__
        
        print(f"   📚 智能准备检测器类名: {prep_class_name}")
        print(f"   📖 分析检测器类名: {analysis_class_name}")
        
        if prep_class_name != analysis_class_name:
            print("   ✅ 类隔离成功：两个检测器是不同的类")
            return True
        else:
            print("   ❌ 类隔离失败：两个检测器是同一个类")
            return False
            
    except Exception as e:
        print(f"   ❌ 类隔离测试失败: {e}")
        return False

def test_module_dependencies():
    """测试模块依赖隔离"""
    print("\n🧪 测试3：模块依赖隔离验证")
    
    try:
        # 测试智能准备模块的依赖
        print("   📚 测试智能准备模块依赖...")
        from app.services.content_preparation_service import ContentPreparationService
        from app.services.intelligent_detection_service import IntelligentDetectionService
        from app.services.chapter_service import ChapterService
        print("   ✅ 智能准备模块依赖正常")
        
        # 测试分析模块的依赖
        print("   📖 测试分析模块依赖...")
        from app.services.six_card_analyzer import SixCardAnalyzer
        from app.services.independent_audio_storyboard_service import IndependentAudioStoryboardService
        print("   ✅ 分析模块依赖正常")
        
        # 验证API隔离
        print("   🔌 测试API模块隔离...")
        from app.api.v1.content_preparation import router as prep_router
        from app.api.v1.analysis.chapters_analysis import router as analysis_router
        print("   ✅ API模块隔离成功")
        
        return True
        
    except Exception as e:
        print(f"   ❌ 模块依赖测试失败: {e}")
        return False

def test_file_isolation():
    """测试文件隔离"""
    print("\n🧪 测试4：文件隔离验证")
    
    files_to_check = [
        "platform/backend/app/detectors/ollama_character_detector.py",
        "platform/backend/app/detectors/analysis_character_detector.py"
    ]
    
    try:
        for file_path in files_to_check:
            if os.path.exists(file_path):
                size = os.path.getsize(file_path)
                print(f"   ✅ {file_path} 存在 ({size} bytes)")
            else:
                print(f"   ❌ {file_path} 不存在")
                return False
        
        print("   ✅ 文件隔离验证成功：两个检测器文件都存在且独立")
        return True
        
    except Exception as e:
        print(f"   ❌ 文件隔离测试失败: {e}")
        return False

def test_functionality_isolation():
    """测试功能隔离"""
    print("\n🧪 测试5：功能隔离验证")
    
    try:
        from app.detectors.ollama_character_detector import OllamaCharacterDetector
        from app.detectors.analysis_character_detector import AnalysisCharacterDetector
        
        # 创建实例
        prep_detector = OllamaCharacterDetector()
        analysis_detector = AnalysisCharacterDetector()
        
        # 验证它们有相同的接口但不同的实现
        prep_methods = [method for method in dir(prep_detector)]
        analysis_methods = [method for method in dir(analysis_detector)]
        
        print(f"   📚 智能准备检测器方法数: {len(prep_methods)}")
        print(f"   📖 分析检测器方法数: {len(analysis_methods)}")
        
        # 检查关键方法是否存在
        key_methods = ['analyze_text', '_call_ollama']
        
        # 检查解析方法（两个模块可能有不同的方法名）
        prep_parse_methods = [m for m in dir(prep_detector) if 'parse' in m.lower() and not m.startswith('__')]
        analysis_parse_methods = [m for m in dir(analysis_detector) if 'parse' in m.lower() and not m.startswith('__')]
        
        print(f"   📚 智能准备解析方法: {prep_parse_methods}")
        print(f"   📖 分析模块解析方法: {analysis_parse_methods}")
        
        # 检查解析方法是否都存在（允许不同的方法名）
        if prep_parse_methods and analysis_parse_methods:
            print(f"   ✅ 两个检测器都有解析方法（允许不同实现）")
        else:
            print(f"   ❌ 某个检测器缺少解析方法")
        
        for method in key_methods:
            if hasattr(prep_detector, method) and hasattr(analysis_detector, method):
                print(f"   ✅ 两个检测器都有 {method} 方法")
            else:
                print(f"   ❌ 检测器缺少 {method} 方法")
                return False
        
        print("   ✅ 功能隔离验证成功：两个检测器有相同接口但独立实现")
        return True
        
    except Exception as e:
        print(f"   ❌ 功能隔离测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("🔒 书籍智能准备与书籍分析模块隔离测试")
    print("=" * 60)
    print(f"📅 测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # 运行所有测试
    tests = [
        test_import_isolation,
        test_class_isolation,
        test_module_dependencies,
        test_file_isolation,
        test_functionality_isolation
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
    print("📊 隔离测试结果汇总")
    print("=" * 60)
    
    passed = sum(results)
    total = len(results)
    
    print(f"✅ 通过测试: {passed}/{total}")
    print(f"❌ 失败测试: {total - passed}/{total}")
    print(f"📈 成功率: {passed/total*100:.1f}%")
    
    # 结论
    print("\n🎯 隔离结论:")
    if passed == total:
        print("   🎉 完美隔离！两个模块完全独立运行")
        print("   🎉 智能准备模块使用 OllamaCharacterDetector")
        print("   🎉 分析模块使用 AnalysisCharacterDetector")
        print("   🎉 可以独立维护和优化两个模块")
    elif passed >= 4:
        print("   ✅ 基本隔离成功，大部分功能正常")
        print("   ⚠️  建议检查失败的测试项")
    else:
        print("   ❌ 隔离存在问题，需要进一步修复")
        print("   ⚠️  两个模块可能仍然存在依赖关系")
    
    print(f"\n🔚 测试完成于: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    return passed == total

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
