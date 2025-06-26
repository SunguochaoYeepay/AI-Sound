#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试LLM场景分析器JSON解析修复
"""

import asyncio
import sys
import os

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.llm_scene_analyzer import llm_scene_analyzer

async def test_llm_analyzer():
    """测试LLM分析器"""
    test_text = """一天，唐僧师徒四人来到一座高山前，只见山势险峻，峰岩重叠。走了一天的路，唐僧感觉饥饿，就让孙悟空去找些吃的。悟空抡起金箍棒，一棒打死了妖精。妖精化作一堆骷髅，脊梁上有一行字，写着"白骨夫人"。"""
    
    print("开始测试LLM场景分析器...")
    print(f"测试文本: {test_text[:50]}...")
    
    try:
        # 检查Ollama状态
        ollama_available = await llm_scene_analyzer.check_ollama_status()
        print(f"Ollama服务状态: {'可用' if ollama_available else '不可用'}")
        
        if not ollama_available:
            print("Ollama服务不可用，无法进行完整测试")
            return
        
        # 检查模型可用性
        model_available = await llm_scene_analyzer.check_model_available(
            llm_scene_analyzer.model_name
        )
        print(f"模型 {llm_scene_analyzer.model_name} 状态: {'可用' if model_available else '不可用'}")
        
        if not model_available:
            print("模型不可用，无法进行完整测试")
            return
        
        # 进行场景分析
        print("开始进行场景分析...")
        result = await llm_scene_analyzer.analyze_text_scenes_with_llm(test_text)
        
        print(f"分析完成！")
        print(f"- 处理时间: {result.processing_time:.2f}秒")
        print(f"- 置信度: {result.confidence_score:.2f}")
        print(f"- 场景数量: {len(result.analyzed_scenes)}")
        print(f"- LLM提供商: {result.llm_provider}")
        
        for i, scene in enumerate(result.analyzed_scenes):
            print(f"  场景{i+1}: {scene.location} - {scene.atmosphere}")
        
        print("测试成功完成！✅")
        
    except Exception as e:
        print(f"测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_llm_analyzer()) 