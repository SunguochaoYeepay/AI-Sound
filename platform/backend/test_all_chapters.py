#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
综合测试脚本
测试所有三个章节的环境音分析
"""

import asyncio
import json
import sys
import os

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.llm_scene_analyzer import llm_scene_analyzer

async def test_all_chapters():
    """测试所有章节"""
    print("🔍 综合测试：所有章节环境音分析")
    print("=" * 60)
    
    # 测试数据
    test_cases = [
        {
            "name": "第一章（现代场景）",
            "text": """请分析以下章节的旁白内容，识别环境声音：

段落1(0.0-10.4s): 博物馆的空调发出轻微嗡鸣，林渊盯着展柜里的汉代青铜剑，心中五味杂陈。

段落2(10.4-16.9s): 突然，口袋里的手机震动起来，他掏出一看，是一条陌生号码发来的短信。

段落3(16.9-27.3s): 林渊快步走向博物馆出口，脚步声在空旷的大厅里回荡。

段落4(27.3-38.7s): 走出博物馆，远处传来马蹄声，一辆马车正缓缓驶来。

段落5(38.7-50.1s): 林渊沿着石板路走去，脚步声在古老的街道上回响。

段落6(50.1-61.5s): 远处传来马蹄声和马儿的嘶鸣声，马车越来越近。"""
        },
        {
            "name": "第二章（古代场景）",
            "text": """请分析以下章节的旁白内容，识别环境声音：

段落1(0.0-12.3s): 林渊站在古老的城门前，远处传来钟声，悠扬的钟声在古城上空回荡。

段落2(12.3-24.6s): 城门缓缓打开，发出沉重的吱呀声，林渊迈步走进城内。

段落3(24.6-36.9s): 街道上传来小贩的吆喝声和行人的脚步声，热闹非凡。

段落4(36.9-49.2s): 突然，远处传来马蹄声，一队骑兵正从街道尽头疾驰而来。

段落5(49.2-61.5s): 林渊躲到一旁，听到马蹄声越来越近，地面都在微微震动。

段落6(61.5-73.8s): 骑兵队伍呼啸而过，马蹄声渐渐远去，街道重新恢复了平静。"""
        },
        {
            "name": "第三章（复杂场景）",
            "text": """请分析以下章节的旁白内容，识别环境声音：

段落1(0.0-21.1s): 御书房内，刘邦把玩着林渊递上的钢笔，目光锐利："你说你来自千年之后？" 林渊咽了咽口水，指着窗外明月："陛下可知'人有悲欢离合，月有阴晴圆缺'？此乃后世苏轼所作。

段落2(21.1-27.6s): 刘邦挑眉，还未及说话，殿外突然传来急促脚步声。

段落3(42.0-65.7s): 鲁元公主突然上前，裙摆扫过青砖："父皇，此人或许能助我等！" 她转头看向林渊，眼神中带着期待，"半月前你说知晓楚军布防……" "不错！" 林渊握紧拳头，玉佩在怀中再次发烫。

段落4(73.1-83.8s): 而暗处，太监假嘴角勾起冷笑，袖中藏着的密信早已被汗水浸湿 —— 那是写给项羽的投诚书。"""
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📖 测试 {i}: {test_case['name']}")
        print("-" * 40)
        
        try:
            # 调用LLM分析器
            print("🤖 调用LLM分析器...")
            result = await llm_scene_analyzer.analyze_text_scenes_with_llm(test_case['text'])
            
            print(f"✅ 分析完成")
            print(f"📊 处理时间: {result.processing_time:.2f}s")
            print(f"🎯 置信度: {result.confidence_score}")
            print(f"📋 场景数量: {len(result.analyzed_scenes)}")
            
            print("\n🔍 LLM原始响应:")
            print("-" * 20)
            print(result.raw_response)
            
            print("\n🎵 解析结果:")
            print("-" * 20)
            for j, scene in enumerate(result.analyzed_scenes, 1):
                print(f"场景 {j}: {scene.keywords} (置信度: {scene.confidence})")
            
            print("\n" + "=" * 60)
            
        except Exception as e:
            print(f"❌ 测试失败: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_all_chapters())
