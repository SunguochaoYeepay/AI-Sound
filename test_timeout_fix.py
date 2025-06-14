#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试超时修复方案
验证Ollama AI在长文本下的表现
"""

import sys
import os
import time
sys.path.append(os.path.join(os.path.dirname(__file__), 'platform', 'backend'))

from app.api.v1.chapters import OllamaCharacterDetector

async def test_timeout_fix():
    """测试超时修复"""
    
    # 使用较长的测试文本（模拟真实章节）
    long_text = """
    话说唐僧师徒四人，行至白虎岭前，只见山势险峻，林木茂密。
    
    悟空用火眼金睛一看，说道："师父，此山有妖气！"
    
    唐僧听了，心中惊恐，问道："悟空，你可看清是何妖怪？"
    
    "师父放心，待俺老孙前去探看。"悟空说完，纵身一跃，飞上山头。
    
    这时，白骨精正在洞中修炼，忽然感到有人窥探，心中大怒。
    
    白骨精化作美貌女子，手提篮子，内装馒头，走向师徒四人。
    
    "各位师父，"白骨精柔声说道，"小女子家住前村，见师父们远道而来，特送些斋饭。"
    
    八戒见了美女，口水直流，说道："师父，这女子好生美貌，又有斋饭，何不收下？"
    
    沙僧在旁劝道："二师兄，我们是出家人，不可贪恋美色。"
    
    唐僧合掌道："女施主有心了，只是我等出家人，不便收受。"
    
    悟空从山上回来，一眼看出是妖怪变化，举棒就打。
    
    "妖怪！还不现出原形！"悟空大喝一声，金箍棒直击白骨精。
    
    白骨精见事不妙，化作一阵青烟逃走，留下一堆白骨。
    
    唐僧见悟空打死人，大怒道："悟空！你怎可滥杀无辜！"
    
    "师父，"悟空解释道，"她是妖怪，不是人！"
    
    但唐僧不信，念起紧箍咒，疼得悟空满地打滚。
    
    师徒四人继续前行，不知前方还有什么危险等待。
    """
    
    print("🧪 测试超时修复方案")
    print("=" * 50)
    print(f"📝 测试文本长度: {len(long_text)} 字符")
    print(f"⏰ 超时设置: 180秒 (3分钟)")
    print(f"📊 文本限制: 1500字符")
    
    ollama_detector = OllamaCharacterDetector()
    chapter_info = {
        'chapter_id': 1,
        'chapter_title': '白骨精三戏唐三藏',
        'chapter_number': 1
    }
    
    print("\n🚀 开始AI分析...")
    start_time = time.time()
    
    try:
        import asyncio
        result = await ollama_detector.analyze_text(long_text, chapter_info)
        end_time = time.time()
        
        print(f"✅ 分析完成！耗时: {end_time - start_time:.2f}秒")
        print(f"📊 分析方法: {result['processing_stats']['analysis_method']}")
        
        if result['processing_stats']['analysis_method'] == 'ollama_ai_primary':
            print("🎉 AI分析成功！")
            print(f"👥 识别角色数: {result['processing_stats']['characters_found']}")
            print(f"📄 文本段数: {result['processing_stats']['total_segments']}")
            print(f"💬 对话段数: {result['processing_stats']['dialogue_segments']}")
            print(f"📖 叙述段数: {result['processing_stats']['narration_segments']}")
            
            print("\n🎭 识别的角色:")
            for char in result['detected_characters']:
                print(f"  • {char['name']} (出现{char['frequency']}次)")
                print(f"    性别: {char['recommended_config']['gender']}")
                print(f"    性格: {char['recommended_config']['personality']}")
        
        elif result['processing_stats']['analysis_method'] == 'simple_fallback':
            print("⚠️  AI分析失败，使用了回退方案")
            print("可能原因：")
            print("  - Ollama服务未启动")
            print("  - 网络连接问题") 
            print("  - 模型加载问题")
        
    except Exception as e:
        end_time = time.time()
        print(f"❌ 分析失败！耗时: {end_time - start_time:.2f}秒")
        print(f"错误信息: {str(e)}")
    
    print("\n" + "=" * 50)
    print("🎯 优化总结:")
    print("✅ 超时时间: 60秒 → 180秒")
    print("✅ 文本限制: 2000字符 → 1500字符")
    print("✅ 提示词简化: 减少处理复杂度")
    print("✅ 回退机制: 确保系统稳定性")

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_timeout_fix()) 