#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试14B模型优化后的角色检测性能
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

async def test_14b_model_performance():
    """测试14B模型性能"""
    
    # 测试文本：包含复杂对话场景
    test_text = """
    小明看到小红走过来，连忙说："早上好，小红！"
    小红微笑着回答："早上好，小明！今天天气真不错。"
    这时，老师走进教室，对大家说："同学们，今天我们来学习新的课程。"
    小明心想：这堂课应该会很有趣。
    """
    
    try:
        # 初始化检测器
        logger.info("🚀 初始化14B模型检测器...")
        detector = OllamaCharacterDetector()
        
        # 构建测试章节信息
        chapter_info = {
            "chapter_id": "test_001",
            "chapter_title": "测试章节",
            "chapter_number": 1,
            "session_id": "test_session"
        }
        
        logger.info("📝 开始分析测试文本...")
        result = await detector.analyze_text(test_text, chapter_info)
        
        logger.info("✅ 分析完成，结果如下：")
        logger.info(f"检测到角色数量: {len(result.get('detected_characters', []))}")
        logger.info(f"分段数量: {len(result.get('segments', []))}")
        logger.info(f"使用模型: {result.get('processing_stats', {}).get('model_version', 'unknown')}")
        
        # 打印角色信息
        for char in result.get('detected_characters', []):
            logger.info(f"角色: {char['name']}, 出现次数: {char.get('frequency', 0)}, 是否主角: {char.get('is_main_character', False)}")
        
        # 打印分段信息
        for segment in result.get('segments', [])[:5]:  # 只显示前5段
            logger.info(f"段落 {segment['order']}: [{segment['speaker']}] {segment['text'][:50]}...")
        
        logger.info("🎯 14B模型测试完成")
        
    except Exception as e:
        logger.error(f"❌ 测试失败: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(test_14b_model_performance()) 