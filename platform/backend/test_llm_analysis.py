#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试LLM分析器的脚本
直接调用LLM分析相同的内容，看看分析结果（去掉过滤逻辑）
"""

import asyncio
import json
import sys
import os

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.llm_scene_analyzer import llm_scene_analyzer

async def test_llm_analysis():
    """测试LLM分析器（去掉过滤逻辑）"""
    print("🔍 测试LLM分析器（第二章）")
    print("=" * 50)
    
    # 测试文本 - 第二章的内容
    test_text = """请分析以下章节的旁白内容，识别环境声音：

段落1(0.0-12.3s): 林渊站在古老的城门前，远处传来钟声，悠扬的钟声在古城上空回荡。

段落2(12.3-24.6s): 城门缓缓打开，发出沉重的吱呀声，林渊迈步走进城内。

段落3(24.6-36.9s): 街道上传来小贩的吆喝声和行人的脚步声，热闹非凡。

段落4(36.9-49.2s): 突然，远处传来马蹄声，一队骑兵正从街道尽头疾驰而来。

段落5(49.2-61.5s): 林渊躲到一旁，听到马蹄声越来越近，地面都在微微震动。

段落6(61.5-73.8s): 骑兵队伍呼啸而过，马蹄声渐渐远去，街道重新恢复了平静。"""
    
    print("📝 测试文本:")
    print(test_text)
    print("\n" + "=" * 50)
    
    try:
        # 调用LLM分析器
        print("🤖 调用LLM分析器...")
        result = await llm_scene_analyzer.analyze_text_scenes_with_llm(test_text)
        
        print(f"✅ 分析完成")
        print(f"📊 处理时间: {result.processing_time:.2f}s")
        print(f"🎯 置信度: {result.confidence_score}")
        print(f"📋 场景数量: {len(result.analyzed_scenes)}")
        
        print("\n🔍 LLM原始响应:")
        print("-" * 30)
        print(result.raw_response)
        print("-" * 30)
        
        print("\n🎵 解析结果（无过滤）:")
        print("-" * 30)
        for i, scene in enumerate(result.analyzed_scenes, 1):
            print(f"场景 {i}:")
            print(f"  位置: {scene.location}")
            print(f"  关键词: {scene.keywords}")
            print(f"  置信度: {scene.confidence}")
            print()
            
        # 手动解析LLM响应，不进行过滤
        print("\n🔍 手动解析LLM响应（无过滤）:")
        print("-" * 30)
        lines = result.raw_response.strip().split('\n')
        for line in lines:
            line = line.strip()
            if line and ':' in line:
                print(f"  {line}")
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_llm_analysis())
