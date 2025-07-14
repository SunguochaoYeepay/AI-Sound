#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试14B模型对穿越小说文本的分析效果
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import asyncio
import logging
from app.detectors.ollama_character_detector import OllamaCharacterDetector

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_crossover_novel():
    """测试穿越小说文本分析"""
    
    # 用户提供的穿越小说文本
    test_text = """物馆的空调发出轻微嗡鸣，林渊盯着展柜里的汉代青铜剑，指腹无意识摩挲着口袋里的玉佩。那是他在老宅阁楼发现的古物，温润的羊脂玉上刻着不知名的符文。
"叮 ——" 手机震动打断思绪，是导师发来的消息："新出土的未央宫残简，速来。" 他将玉佩塞回口袋，快步穿过走廊。就在经过汉代展区转角时，一道刺目的白光突然炸开，耳畔响起尖锐的蜂鸣。
再睁眼时，林渊发现自己躺在泥泞的官道上。远处传来马蹄声，他挣扎着起身，腰间玉佩突然发烫。抬头望去，一队汉军骑兵正朝他奔来，为首的将领身着玄甲，腰间悬挂的虎符与博物馆里的展品如出一辙。
"何人在此？" 将领勒马，长枪直指他咽喉。林渊喉结滚动，盯着对方胸甲上的 "汉" 字，突然意识到自己竟穿越到了楚汉相争的年代。"""
    
    try:
        # 初始化检测器
        logger.info("🚀 初始化14B模型检测器...")
        detector = OllamaCharacterDetector()
        
        # 构建测试章节信息
        chapter_info = {
            "chapter_id": 1,
            "chapter_title": "第一章 穿越",
            "chapter_number": 1,
            "book_title": "汉代穿越记",
            "session_id": "test_session_001"
        }
        
        # 执行分析
        logger.info("🔍 开始分析穿越小说文本...")
        logger.info(f"📝 文本长度: {len(test_text)}字符")
        
        result = await detector.analyze_text(test_text, chapter_info)
        
        # 输出分析结果
        logger.info("=" * 80)
        logger.info("📊 分析结果:")
        logger.info(f"✅ 识别角色数量: {len(result['characters'])}")
        logger.info(f"📄 分段数量: {len(result['segments'])}")
        logger.info(f"👑 主角: {result.get('main_character', 'N/A')}")
        
        # 详细角色信息
        logger.info("\n🎭 角色列表:")
        for char in result['characters']:
            logger.info(f"  - {char['name']}: 出现{char['count']}次")
        
        # 分段详情
        logger.info("\n📝 分段详情:")
        for i, segment in enumerate(result['segments'], 1):
            logger.info(f"  [{i}] {segment['speaker']}: {segment['text'][:50]}...")
        
        # 处理统计
        if 'processing_stats' in result:
            stats = result['processing_stats']
            logger.info(f"\n📈 处理统计:")
            logger.info(f"  - 总段落数: {stats.get('total_segments', 'N/A')}")
            logger.info(f"  - 是否使用二次检查: {stats.get('used_secondary_check', 'N/A')}")
            logger.info(f"  - 完整性校验: {stats.get('completeness_check', 'N/A')}")
        
        # 验证关键点
        logger.info("\n🔍 关键验证点:")
        
        # 1. 是否正确识别出现代通讯设备的消息
        found_message = False
        for segment in result['segments']:
            if '导师' in segment['text'] or '新出土' in segment['text']:
                found_message = True
                logger.info(f"✅ 正确识别导师消息: {segment['speaker']} - {segment['text']}")
                break
        
        if not found_message:
            logger.warning("❌ 未正确识别导师消息")
        
        # 2. 是否正确识别古代将领对话
        found_general = False
        for segment in result['segments']:
            if '何人在此' in segment['text']:
                found_general = True
                logger.info(f"✅ 正确识别将领对话: {segment['speaker']} - {segment['text']}")
                break
        
        if not found_general:
            logger.warning("❌ 未正确识别将领对话")
        
        # 3. 是否正确区分旁白和对话
        dialogue_count = sum(1 for s in result['segments'] if s['speaker'] != '旁白')
        narration_count = sum(1 for s in result['segments'] if s['speaker'] == '旁白')
        
        logger.info(f"✅ 对话段落: {dialogue_count}个")
        logger.info(f"✅ 旁白段落: {narration_count}个")
        
        return result
        
    except Exception as e:
        logger.error(f"❌ 分析失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    asyncio.run(test_crossover_novel()) 