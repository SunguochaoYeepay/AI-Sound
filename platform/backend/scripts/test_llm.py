#!/usr/bin/env python3
"""
简单LLM测试脚本
"""

import asyncio
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.llm_scene_analyzer import llm_scene_analyzer

async def test_llm():
    """简单测试LLM分析功能"""
    print("🎯 简单LLM测试")
    print("=" * 40)
    
    # 测试文本
    test_text = """请仔细分析以下小说章节的旁白内容，识别每个时间段中描述的环境声音及其时序特征。

⚠️ 重要原则：只识别文本中明确描述或暗示的实际发生的动作声音，不要基于场景进行联想！

需要识别的环境音类型包括但不限于：
• 自然环境：雨声、雷声、风声、鸟鸣、虫鸣、海浪声、流水声、叶子摩擦声
• 人为活动：脚步声、开门声、关门声、翻书声、写字声、敲击声、机械声
• 室内环境：时钟滴答声、空调声、火焰燃烧声、电器运转声、厨房声音
• 交通环境：汽车声、火车声、飞机声、轮船声、马蹄声
• 社交场景：人群喧哗、掌声、音乐声、乐器声、歌声

⚠️ 识别规则：
1. 只识别文本中明确提到的动作声音（如'脚步声'、'叮声'、'马蹄声'）
2. 不要因为场景是'御书房'就联想'翻书声'、'写字声'
3. 不要因为场景是'厨房'就联想'炒菜声'、'切菜声'
4. 如果文本中没有明确描述声音，标记为'无声段'
5. 区分动作描述和声音描述：'走路'≠'脚步声'，'说话'≠'说话声'

时序分析要求：
1. 分析声音的持续时间：瞬间声音（如'叮'、'砰'）通常1-2秒，持续声音（如'雨声'、'空调声'）持续整个段落
2. 分析声音的强度变化：高强度（如'雷声'、'爆炸声'）、中强度（如'脚步声'、'说话声'）、低强度（如'呼吸声'、'时钟声'）
3. 分析声音的时序关系：哪些声音同时发生，哪些声音先后发生
4. 识别无声段落：纯对话、心理描述、无声动作等
5. 考虑声音的因果关系：如'手机震动'→'叮'声，'看消息'→无声

以下是需要分析的旁白内容：

【段落1】时间轴：0.0-7.5s
内容：夜幕降临，城南古庙笼罩在一片神秘的氛围中。

【段落2】时间轴：7.5-12.9s
内容：李玄机独自一人来到古庙前，脚步声在寂静的夜晚格外清晰。

【段落3】时间轴：12.9-17.1s
内容：远处传来阵阵钟声，悠扬的钟声在夜空中回荡。

【段落4】时间轴：17.1-22.1s
内容：树叶沙沙作响，仿佛在诉说着古老的传说。

【段落5】时间轴：22.1-28.1s
内容：吱呀一声，门轴发出刺耳的摩擦声，李玄机推开了古庙的大门。

请为每个段落提供详细的时序分析结果，格式如下：
段落X：
- 声音事件1：[声音类型] [开始时间] [持续时间] [强度] [描述]
- 声音事件2：[声音类型] [开始时间] [持续时间] [强度] [描述]
- 无声段：[开始时间] [持续时间] [描述]

示例：
段落1：
- 声音事件1：空调声 0.0s 14.4s 低强度 持续的背景嗡鸣（文本明确提到'空调发出轻微嗡鸣'）
段落2：
- 声音事件1：手机震动声 0.0s 1.5s 高强度 叮的一声（文本明确提到'手机震动'和'叮'）
- 无声段：1.5s 6.5s 查看消息内容（文本没有描述其他声音）

错误示例：
❌ 不要因为'御书房'就联想'翻书声'、'写字声'
❌ 不要因为'厨房'就联想'炒菜声'、'切菜声'
❌ 不要因为'走路'就联想'脚步声'（除非文本明确提到）"""
    
    print("🔍 开始LLM分析...")
    
    try:
        # 执行LLM分析
        result = await llm_scene_analyzer.analyze_text_scenes_with_llm(test_text)
        
        print("✅ LLM分析完成!")
        print(f"📊 分析结果:")
        print(f"   - 场景数量: {len(result.analyzed_scenes)}")
        print(f"   - 置信度: {result.confidence_score:.2f}")
        print(f"   - 处理时间: {result.processing_time:.2f}秒")
        
        print(f"\n🎵 识别到的环境音:")
        print("-" * 40)
        
        for i, scene in enumerate(result.analyzed_scenes, 1):
            print(f"场景 {i}:")
            print(f"   - 位置: {scene.location}")
            print(f"   - 关键词: {scene.keywords}")
            print(f"   - 置信度: {scene.confidence:.2f}")
            print()
        
        print(f"📝 LLM原始响应:")
        print("-" * 40)
        print(result.raw_response[:500] + "..." if len(result.raw_response) > 500 else result.raw_response)
        
        # 评价结果
        print(f"\n🏆 评价:")
        print("-" * 40)
        
        if len(result.analyzed_scenes) >= 5:
            print("✅ 识别数量充足")
        elif len(result.analyzed_scenes) >= 3:
            print("⚠️ 识别数量一般")
        else:
            print("❌ 识别数量不足")
        
        if result.confidence_score >= 0.8:
            print("✅ 置信度优秀")
        elif result.confidence_score >= 0.6:
            print("⚠️ 置信度一般")
        else:
            print("❌ 置信度较低")
        
        if result.processing_time <= 20:
            print("✅ 处理速度优秀")
        elif result.processing_time <= 30:
            print("⚠️ 处理速度一般")
        else:
            print("❌ 处理速度较慢")
        
        print("✅ LLM分析功能正常")
        
    except Exception as e:
        print(f"❌ LLM分析失败: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_llm())
