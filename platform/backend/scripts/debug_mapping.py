#!/usr/bin/env python3
"""
调试映射过程 - 查看LLM输出到最终结果的转换
"""

import sys
import os
import asyncio

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

async def debug_mapping():
    """调试映射过程"""
    print("🔍 调试映射过程")
    print("=" * 60)
    
    # 导入分析器
    from app.services.narration_environment_analyzer import NarrationEnvironmentAnalyzer
    from app.services.llm_scene_analyzer import OllamaLLMSceneAnalyzer
    
    # 创建分析器实例
    analyzer = NarrationEnvironmentAnalyzer()
    llm_analyzer = OllamaLLMSceneAnalyzer()
    
    # 测试文本（第一章的内容）
    test_text = """请分析以下文本中的环境音，严格按照以下要求：

🎯 核心要求：
1. 只识别文本中明确提到的声音
2. 关键词要简洁，2-4个字符
3. 不要包含时间、强度等描述性信息
4. 不要包含分析过程或格式标记
5. 不要进行任何联想
6. 瞬间声音用简洁词汇：叮、砰、响、震动等
7. 持续声音用标准词汇：脚步声、说话声、马蹄声等

✅ 正确示例：
- "空调发出轻微嗡鸣" → ["空调声"]
- "手机震动" → ["震动声"]
- "远处传来马蹄声" → ["马蹄声"]
- "叮 ——" → ["叮声"]
- "娇喝声带着怒意" → ["娇喝声"]
- "急促脚步声" → ["脚步声"]
- "耳畔响起尖锐的蜂鸣" → ["蜂鸣声"]

❌ 错误示例：
- 不要联想：看到"御书房"就联想"翻书声"
- 不要描述：不要包含"中强度"、"1.5秒"等描述
- 不要格式：不要包含"**段落**"、"声音事件"等标记
- 不要复杂：不要"手机震动打声"，应该是"震动声"
- 不要重复：不要"耳畔响"，应该是"响"或"蜂鸣声"

段落1: "叮 ——" 手机震动打断思绪，是导师发来的消息："新出土的未央宫残简，速来。"

段落2: 他将玉佩塞回口袋，快步穿过走廊。

段落3: 就在经过汉代展区转角时，一道刺目的白光突然炸开，耳畔响起尖锐的蜂鸣。

段落4: 远处传来马蹄声，他挣扎着起身，腰间玉佩突然发烫。

请按段落顺序返回结果，格式：
段落1: ["关键词1", "关键词2"]
段落2: []
段落3: ["关键词1"]

要求：
- 每个段落最多3个关键词
- 关键词简洁准确
- 无声音的段落返回[]
- 不要解释，直接返回结果
- 瞬间声音优先：叮、响、震动等
- 持续声音标准：脚步声、说话声、马蹄声等"""
    
    print("📝 测试文本:")
    print(test_text[:200] + "...")
    print()
    
    try:
        # 1. 调用LLM分析
        print("🤖 步骤1: 调用LLM分析...")
        llm_result = await llm_analyzer.analyze_text_scenes_with_llm(test_text)
        
        print(f"✅ LLM分析完成")
        print(f"📊 识别场景数: {len(llm_result.analyzed_scenes)}")
        print(f"🎯 置信度: {llm_result.confidence_score}")
        print()
        
        print("🔍 LLM原始响应:")
        print("-" * 40)
        print(llm_result.raw_response)
        print("-" * 40)
        print()
        
        print("📋 LLM解析后的场景:")
        for i, scene in enumerate(llm_result.analyzed_scenes, 1):
            print(f"场景 {i}:")
            print(f"  - 位置: {scene.location}")
            print(f"  - 关键词: {scene.keywords}")
            print(f"  - 置信度: {scene.confidence}")
            print()
        
        # 2. 测试关键词清理
        print("🧹 步骤2: 测试关键词清理...")
        for i, scene in enumerate(llm_result.analyzed_scenes, 1):
            print(f"场景 {i} 关键词清理:")
            print(f"  原始: {scene.keywords}")
            cleaned = analyzer._clean_environment_keywords(scene.keywords)
            print(f"  清理后: {cleaned}")
            print()
        
        # 3. 模拟映射过程
        print("🗺️ 步骤3: 模拟映射过程...")
        # 创建模拟的段落数据
        narration_segments = [
            {
                'segment_id': 'seg_1',
                'text': '"叮 ——" 手机震动打断思绪，是导师发来的消息："新出土的未央宫残简，速来。"',
                'start_time': 0.0,
                'duration': 10.2,
                'end_time': 10.2
            },
            {
                'segment_id': 'seg_2',
                'text': '他将玉佩塞回口袋，快步穿过走廊。',
                'start_time': 10.2,
                'duration': 4.7,
                'end_time': 14.9
            },
            {
                'segment_id': 'seg_3',
                'text': '就在经过汉代展区转角时，一道刺目的白光突然炸开，耳畔响起尖锐的蜂鸣。',
                'start_time': 14.9,
                'duration': 8.7,
                'end_time': 23.6
            },
            {
                'segment_id': 'seg_4',
                'text': '远处传来马蹄声，他挣扎着起身，腰间玉佩突然发烫。',
                'start_time': 23.6,
                'duration': 6.5,
                'end_time': 30.1
            }
        ]
        
        print(f"段落数量: {len(narration_segments)}")
        print(f"场景数量: {len(llm_result.analyzed_scenes)}")
        
        # 调用映射函数
        environment_tracks = analyzer._map_scenes_to_segments(llm_result, narration_segments)
        
        print(f"✅ 映射完成，生成 {len(environment_tracks)} 个轨道")
        print()
        
        print("📊 最终结果:")
        for i, track in enumerate(environment_tracks, 1):
            print(f"轨道 {i}:")
            print(f"  - 段落ID: {track['segment_id']}")
            print(f"  - 关键词: {track['environment_keywords']}")
            print(f"  - 时长: {track['duration']:.1f}秒")
            print(f"  - 开始时间: {track['start_time']:.1f}秒")
            print(f"  - 置信度: {track['confidence']:.2f}")
            print(f"  - 映射策略: {track['mapping_strategy']}")
            print()
            
    except Exception as e:
        print(f"❌ 调试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_mapping())
