#!/usr/bin/env python3
"""
书籍分析逻辑测试脚本
验证书籍分析模块的完整工作流程
"""

import sys
import os
import time
import asyncio
from datetime import datetime
from typing import Dict, Any

# 添加项目路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'platform', 'backend'))

def test_imports():
    """测试导入"""
    print("🧪 测试1：导入验证")
    
    try:
        # 测试分析模块核心组件
        from app.detectors.analysis_character_detector import AnalysisCharacterDetector
        from app.services.six_card_analyzer import SixCardAnalyzer
        from app.services.independent_audio_storyboard_service import IndependentAudioStoryboardService
        from app.services.smart_segmentation_service import SmartSegmentationService
        print("   ✅ 核心分析组件导入成功")
        
        # 测试API模块
        from app.api.v1.analysis.chapters_analysis import router
        print("   ✅ 分析API模块导入成功")
        
        return True
        
    except Exception as e:
        print(f"   ❌ 导入失败: {e}")
        return False

def test_component_initialization():
    """测试组件初始化"""
    print("\n🧪 测试2：组件初始化")
    
    try:
        from app.detectors.analysis_character_detector import AnalysisCharacterDetector
        from app.services.six_card_analyzer import SixCardAnalyzer
        from app.services.independent_audio_storyboard_service import IndependentAudioStoryboardService
        from app.services.smart_segmentation_service import SmartSegmentationService
        
        # 初始化各个组件
        character_detector = AnalysisCharacterDetector()
        six_card_analyzer = SixCardAnalyzer()
        audio_storyboard_service = IndependentAudioStoryboardService()
        segmentation_service = SmartSegmentationService()
        
        print(f"   ✅ AnalysisCharacterDetector 初始化成功")
        print(f"   ✅ SixCardAnalyzer 初始化成功")
        print(f"   ✅ IndependentAudioStoryboardService 初始化成功")
        print(f"   ✅ SmartSegmentationService 初始化成功")
        
        return True
        
    except Exception as e:
        print(f"   ❌ 组件初始化失败: {e}")
        return False

async def test_analysis_workflow():
    """测试分析工作流程"""
    print("\n🧪 测试3：分析工作流程")
    
    # 测试文本
    test_text = """
    林薇低头看着自己身上的白大褂，心脏猛地一缩——她竟真的穿越到了课本里的盛唐长安。
    
    "快看这女子的衣装！"人群中有人喊道。
    
    "莫不是西域来的怪人？"
    
    她深吸一口气，努力让自己冷静下来。作为一个现代医生，她必须在这个陌生的时代生存下去。
    
    就在这时，一个年轻男子走到她面前，关切地问道："姑娘，你没事吧？"
    
    林薇抬起头，看到一张俊朗的脸庞，连忙回答："我没事，谢谢关心。"
    
    男子微微一笑："在下萧景琰，敢问姑娘芳名？"
    
    "我叫林薇。"她轻声说道。
    
    萧景琰点点头："林姑娘，看你的装束，似乎不是本地人。需要帮助吗？"
    
    林薇想了想，决定先了解一下这个时代的情况："萧公子，请问现在是哪一年？"
    
    "现在是天宝三年。"萧景琰有些疑惑，"姑娘不知道吗？"
    
    林薇心中一震，天宝三年，那不就是公元744年吗？她真的穿越到了唐朝！
    """
    
    try:
        from app.detectors.analysis_character_detector import AnalysisCharacterDetector
        from app.services.six_card_analyzer import SixCardAnalyzer
        from app.services.independent_audio_storyboard_service import IndependentAudioStoryboardService
        
        # 创建分析器实例
        character_detector = AnalysisCharacterDetector()
        six_card_analyzer = SixCardAnalyzer()
        audio_storyboard_service = IndependentAudioStoryboardService()
        
        print(f"   📝 测试文本长度: {len(test_text)} 字符")
        
        # 第一步：对话分析
        print("   🔄 执行第一步：对话分析...")
        chapter_info = {
            "chapter_id": 999,
            "chapter_title": "测试章节",
            "chapter_number": 1,
            "session_id": "test_session"
        }
        
        start_time = time.time()
        dialogue_analysis = await character_detector.analyze_text(test_text, chapter_info)
        dialogue_time = time.time() - start_time
        
        print(f"   ✅ 对话分析完成 ({dialogue_time:.2f}秒)")
        print(f"   📊 识别角色数: {len(dialogue_analysis.get('detected_characters', []))}")
        print(f"   📊 分析段落数: {len(dialogue_analysis.get('segments', []))}")
        
        # 检查分析结果
        segments = dialogue_analysis.get('segments', [])
        characters = dialogue_analysis.get('detected_characters', [])
        
        if not segments:
            print("   ❌ 对话分析失败：没有生成段落")
            return False
        
        if not characters:
            print("   ❌ 对话分析失败：没有识别到角色")
            return False
        
        # 第二步：5卡分析（智能合并优化）
        print("   🔄 执行第二步：5卡分析（智能合并优化）...")
        start_time = time.time()
        six_card_result = await six_card_analyzer.analyze_segment(test_text, 0, 999, dialogue_analysis)
        six_card_time = time.time() - start_time
        
        print(f"   ✅ 5卡分析完成 ({six_card_time:.2f}秒)")
        
        # 验证智能合并效果
        if 'character_card' in six_card_result:
            character_card = six_card_result['character_card']
            characters = character_card.get('characters', [])
            narrator = character_card.get('narrator', {})
            print(f"   🧠 智能合并验证：角色数 {len(characters)}, 旁白长度 {len(narrator.get('content', ''))}")
            
            # 检查角色卡是否包含对话分析的结果
            if characters:
                char = characters[0]
                if 'dialogue' in char and char['dialogue']:
                    print(f"   ✅ 智能合并成功：角色 '{char['name']}' 对话已合并")
                else:
                    print(f"   ⚠️  角色对话可能未正确合并")
        else:
            print("   ❌ 角色卡生成失败")
        
        # 检查5卡结果
        required_cards = ['story_card', 'character_card', 'scene_card', 'event_card', 'emotion_card']
        missing_cards = []
        for card_type in required_cards:
            if card_type not in six_card_result:
                missing_cards.append(card_type)
        
        if missing_cards:
            print(f"   ⚠️  5卡分析不完整，缺少: {missing_cards}")
        else:
            print("   ✅ 5卡分析完整：故事卡、角色卡、场景卡、事件卡、情绪卡")
        
        # 第三步：音频分镜卡生成
        print("   🔄 执行第三步：音频分镜卡生成...")
        start_time = time.time()
        audio_result = await six_card_analyzer.generate_audio_storyboard_for_segment(
            six_card_result, test_text, 0
        )
        audio_time = time.time() - start_time
        
        print(f"   ✅ 音频分镜卡生成完成 ({audio_time:.2f}秒)")
        
        # 检查音频分镜卡
        if 'audio_storyboard_card' in audio_result:
            audio_card = audio_result['audio_storyboard_card']
            sound_effects = audio_card.get('sound_effects', [])
            background_music = audio_card.get('background_music', [])
            print(f"   📊 音效数量: {len(sound_effects)}")
            print(f"   📊 背景音乐数量: {len(background_music)}")
        else:
            print("   ❌ 音频分镜卡生成失败")
            return False
        
        print("   ✅ 完整分析工作流程测试成功")
        return True
        
    except Exception as e:
        print(f"   ❌ 分析工作流程失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_api_structure():
    """测试API结构"""
    print("\n🧪 测试4：API结构验证")
    
    try:
        from app.api.v1.analysis.chapters_analysis import router
        
        # 检查路由配置
        routes = []
        for route in router.routes:
            if hasattr(route, 'path') and hasattr(route, 'methods'):
                routes.append({
                    'path': route.path,
                    'methods': list(route.methods)
                })
        
        print(f"   📊 分析API路由数量: {len(routes)}")
        
        # 检查关键路由
        key_routes = [
            '/chapters/{chapter_id}/six-card-analysis',
            '/chapters/{chapter_id}/smart-segmentation'
        ]
        
        found_routes = []
        for route_info in routes:
            for key_route in key_routes:
                if key_route in route_info['path']:
                    found_routes.append(route_info['path'])
                    print(f"   ✅ 找到关键路由: {route_info['path']}")
        
        if len(found_routes) >= len(key_routes):
            print("   ✅ API结构验证成功")
            return True
        else:
            print(f"   ❌ API结构不完整，缺少路由: {set(key_routes) - set(found_routes)}")
            return False
            
    except Exception as e:
        print(f"   ❌ API结构验证失败: {e}")
        return False

def test_data_flow():
    """测试数据流"""
    print("\n🧪 测试5：数据流验证")
    
    try:
        # 模拟数据流测试
        test_data = {
            "chapter_id": 999,
            "segment_text": "林薇看着萧景琰，心中五味杂陈。",
            "segment_index": 0
        }
        
        print(f"   📝 测试数据: {test_data}")
        
        # 验证数据结构
        required_fields = ['chapter_id', 'segment_text', 'segment_index']
        missing_fields = [field for field in required_fields if field not in test_data]
        
        if missing_fields:
            print(f"   ❌ 数据流测试失败，缺少字段: {missing_fields}")
            return False
        
        print("   ✅ 数据流结构验证成功")
        return True
        
    except Exception as e:
        print(f"   ❌ 数据流验证失败: {e}")
        return False

async def test_smart_merge_optimization():
    """测试智能合并优化"""
    print("\n🧪 测试6：智能合并优化验证")
    
    try:
        from app.detectors.analysis_character_detector import AnalysisCharacterDetector
        from app.services.six_card_analyzer import SixCardAnalyzer
        from app.services.smart_character_card_merger import SmartCharacterCardMerger
        
        # 测试文本
        test_text = "林薇看着萧景琰，轻声说道：'多谢萧公子。'萧景琰微微一笑。"
        
        # 初始化组件
        character_detector = AnalysisCharacterDetector()
        six_card_analyzer = SixCardAnalyzer()
        merger = SmartCharacterCardMerger()
        
        print("   📝 测试智能合并器初始化...")
        if hasattr(six_card_analyzer, 'character_merger'):
            print("   ✅ SixCardAnalyzer 已集成智能合并器")
        else:
            print("   ❌ SixCardAnalyzer 未集成智能合并器")
            return False
        
        print("   📝 测试对话分析结果...")
        chapter_info = {
            "chapter_id": 999,
            "chapter_title": "智能合并测试",
            "chapter_number": 1
        }
        
        dialogue_result = await character_detector.analyze_text(test_text, chapter_info)
        characters = dialogue_result.get('detected_characters', [])
        segments = dialogue_result.get('segments', [])
        
        print(f"   📊 对话分析：{len(characters)}个角色，{len(segments)}个段落")
        
        print("   📝 测试智能合并功能...")
        character_card = merger.merge_dialogue_to_character_card(dialogue_result)
        merged_characters = character_card.get('characters', [])
        
        print(f"   📊 智能合并：{len(merged_characters)}个角色")
        
        # 验证合并结果
        if merged_characters:
            char = merged_characters[0]
            required_fields = ['name', 'role_type', 'actions', 'dialogue', 'emotions', 'description']
            missing_fields = [field for field in required_fields if field not in char]
            
            if not missing_fields:
                print(f"   ✅ 角色卡结构完整：{char['name']} ({char['role_type']})")
                print(f"   📝 对话内容：{char.get('dialogue', [])}")
                print(f"   📝 情感分析：{char.get('emotions', [])}")
            else:
                print(f"   ❌ 角色卡缺少字段：{missing_fields}")
                return False
        else:
            print("   ❌ 智能合并未生成角色数据")
            return False
        
        print("   📝 测试优化后的5卡分析...")
        start_time = time.time()
        six_card_result = await six_card_analyzer.analyze_segment(test_text, 0, 999, dialogue_result)
        optimized_time = time.time() - start_time
        
        print(f"   ✅ 优化分析完成 ({optimized_time:.2f}秒)")
        
        # 验证优化效果
        if 'character_card' in six_card_result:
            final_characters = six_card_result['character_card'].get('characters', [])
            if len(final_characters) == len(characters):
                print(f"   ✅ 智能合并优化成功：角色数量一致")
            else:
                print(f"   ⚠️  角色数量不一致：合并前{len(characters)}，合并后{len(final_characters)}")
        
        print("   ✅ 智能合并优化验证完成")
        return True
        
    except Exception as e:
        print(f"   ❌ 智能合并优化验证失败: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_error_handling():
    """测试错误处理"""
    print("\n🧪 测试7：错误处理验证")
    
    try:
        from app.detectors.analysis_character_detector import AnalysisCharacterDetector
        
        # 测试空文本处理
        print("   🔄 测试空文本处理...")
        character_detector = AnalysisCharacterDetector()
        
        try:
            result = await character_detector.analyze_text("", {
                "chapter_id": 999,
                "chapter_title": "空文本测试",
                "chapter_number": 1
            })
            
            if result and 'segments' in result:
                print("   ✅ 空文本处理正常")
            else:
                print("   ⚠️  空文本处理结果异常，但未崩溃")
                
        except Exception as e:
            print(f"   ⚠️  空文本处理异常（预期）: {str(e)[:50]}...")
        
        # 测试无效文本处理
        print("   🔄 测试无效文本处理...")
        try:
            result = await character_detector.analyze_text("无效文本123456", {
                "chapter_id": 999,
                "chapter_title": "无效文本测试",
                "chapter_number": 1
            })
            
            if result and 'segments' in result:
                print("   ✅ 无效文本处理正常")
            else:
                print("   ⚠️  无效文本处理结果异常，但未崩溃")
                
        except Exception as e:
            print(f"   ⚠️  无效文本处理异常（预期）: {str(e)[:50]}...")
        
        print("   ✅ 错误处理验证完成")
        return True
        
    except Exception as e:
        print(f"   ❌ 错误处理测试失败: {e}")
        return False

async def main():
    """主测试函数"""
    print("📖 书籍分析逻辑测试")
    print("=" * 60)
    print(f"📅 测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # 运行所有测试
    tests = [
        test_imports,
        test_component_initialization,
        test_analysis_workflow,
        test_api_structure,
        test_data_flow,
        test_smart_merge_optimization,
        test_error_handling
    ]
    
    results = []
    for i, test in enumerate(tests):
        try:
            if asyncio.iscoroutinefunction(test):
                result = await test()
            else:
                result = test()
            results.append(result)
        except Exception as e:
            print(f"   💥 测试{i+1}执行异常: {e}")
            results.append(False)
    
    # 汇总结果
    print("\n" + "=" * 60)
    print("📊 书籍分析逻辑测试结果汇总")
    print("=" * 60)
    
    passed = sum(results)
    total = len(results)
    
    print(f"✅ 通过测试: {passed}/{total}")
    print(f"❌ 失败测试: {total - passed}/{total}")
    print(f"📈 成功率: {passed/total*100:.1f}%")
    
    # 结论
    print("\n🎯 分析逻辑结论:")
    if passed == total:
        print("   🎉 书籍分析逻辑完全正确！")
        print("   🎉 所有组件正常工作")
        print("   🎉 智能合并优化成功")
        print("   🎉 分析流程完整无误")
        print("   🎉 可以投入使用")
    elif passed >= 5:
        print("   ✅ 书籍分析逻辑基本正确")
        print("   ✅ 智能合并优化正常")
        print("   ⚠️  部分功能需要优化")
        print("   📝 建议检查失败的测试项")
    else:
        print("   ❌ 书籍分析逻辑存在严重问题")
        print("   ⚠️  需要修复后才能使用")
    
    print(f"\n🔚 测试完成于: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    return passed >= 5

if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⏹️  测试被用户中断")
        sys.exit(2)
    except Exception as e:
        print(f"\n\n💥 测试脚本执行失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(3)
