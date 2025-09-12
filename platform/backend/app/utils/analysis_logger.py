#!/usr/bin/env python3
"""
分析流程日志工具
提供简洁的3步分析流程日志输出
"""

import logging
from typing import Dict, Any, List
from datetime import datetime

logger = logging.getLogger(__name__)

class AnalysisLogger:
    """分析流程日志记录器"""
    
    @staticmethod
    def log_analysis_start(chapter_id: int, segment_count: int):
        """记录分析开始"""
        logger.info(f"🚀 开始3步分析流程 - 章节 {chapter_id}，共 {segment_count} 个段落")
    
    @staticmethod
    def log_segment_start(segment_index: int, total_segments: int):
        """记录段落分析开始"""
        logger.info(f"📝 段落 {segment_index + 1}/{total_segments} - 开始3步分析")
    
    @staticmethod
    def log_step1_dialogue(segment_index: int, segments_count: int, characters_count: int):
        """记录第1步：对话分析"""
        logger.info(f"🎭 步骤1/3：对话分析完成 (段落{segment_index + 1}) - {segments_count}个片段，{characters_count}个角色")
    
    @staticmethod
    def log_step2_five_cards(segment_index: int, synthesis_segments: int):
        """记录第2步：5卡分析"""
        logger.info(f"🎯 步骤2/3：5卡分析完成 (段落{segment_index + 1}) - 生成{synthesis_segments}个合成片段")
    
    @staticmethod
    def log_step3_audio_storyboard(segment_index: int, sound_effects_count: int, background_music_count: int):
        """记录第3步：音频分镜卡"""
        logger.info(f"🎬 步骤3/3：音频分镜卡完成 (段落{segment_index + 1}) - {sound_effects_count}个音效，{background_music_count}个背景音乐")
    
    @staticmethod
    def log_segment_complete(segment_index: int):
        """记录段落分析完成"""
        logger.info(f"✅ 段落 {segment_index + 1} 三步分析完成")
    
    @staticmethod
    def log_analysis_complete(chapter_id: int, segment_count: int):
        """记录分析完成"""
        logger.info(f"🎉 章节 {chapter_id} 三步分析流程完成，共分析 {segment_count} 个段落")
    
    @staticmethod
    def log_analysis_error(segment_index: int, error_msg: str):
        """记录分析错误"""
        logger.error(f"❌ 段落 {segment_index + 1} 分析失败: {error_msg}")
    
    @staticmethod
    def log_performance_summary(chapter_id: int, total_time: float, segment_times: List[float]):
        """记录性能总结"""
        avg_time = sum(segment_times) / len(segment_times) if segment_times else 0
        logger.info(f"⏱️ 章节 {chapter_id} 性能总结: 总时间{total_time:.1f}s，平均每段{avg_time:.1f}s")
