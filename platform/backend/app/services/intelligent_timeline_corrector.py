#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能时间轴修正器
根据旁白文本中环境音关键词的具体位置，精确计算环境音的开始时间
解决环境音播放时间与旁白描述不同步的问题
"""

import re
import logging
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class KeywordPosition:
    """关键词位置信息"""
    keyword: str
    start_pos: int        # 在文本中的字符位置
    end_pos: int
    relative_time: float  # 在段落中的相对时间（秒）

@dataclass
class CorrectedTrack:
    """修正后的轨道时间信息"""
    original_start_time: float
    corrected_start_time: float
    duration: float
    keyword_position: KeywordPosition
    confidence: float

class IntelligentTimelineCorrector:
    """智能时间轴修正器"""
    
    def __init__(self):
        # 中文语音朗读速度 (字符/分钟)
        self.CHINESE_SPEECH_RATE = 300  # 每分钟300个汉字，适中语速
        
        # 环境音关键词的常见别名和变体
        self.keyword_variants = {
            '雷': ['雷声', '雷鸣', '电闪雷鸣', '轰雷', '炸雷'],
            '雨': ['雨声', '下雨', '雨水', '雨滴', '细雨', '暴雨'],
            '风': ['风声', '刮风', '微风', '狂风', '风吹'],
            '脚步': ['脚步声', '走路', '踏步', '行走', '脚步'],
            '鸟': ['鸟鸣', '鸟叫', '鸟声', '啁啾'],
            '水': ['水声', '流水', '溪水', '河水', '潺潺'],
            '马蹄': ['马蹄声', '马踏', '骏马', '马蹄踏地'],
            '蜂鸣': ['蜂鸣声', '嘟嘟声', '警报', '提示音']
        }
    
    def correct_environment_tracks_timeline(self, 
                                          environment_tracks: List[Dict], 
                                          narration_segments: List[Dict]) -> List[Dict]:
        """修正环境轨道的时间轴"""
        corrected_tracks = []
        
        # 建立段落ID到段落信息的映射
        segment_map = {seg.get('segment_id'): seg for seg in narration_segments}
        
        for track in environment_tracks:
            segment_id = track.get('segment_id')
            segment = segment_map.get(segment_id)
            
            if not segment:
                logger.warning(f"找不到段落 {segment_id}，保持原始时间")
                corrected_tracks.append(track)
                continue
            
            # 分析并修正时间轴
            corrected_track = self._correct_single_track_timeline(track, segment)
            corrected_tracks.append(corrected_track)
        
        return corrected_tracks
    
    def _correct_single_track_timeline(self, track: Dict, segment: Dict) -> Dict:
        """修正单个轨道的时间轴"""
        narration_text = segment.get('text', '') or segment.get('content', '')
        keywords = track.get('environment_keywords', [])
        
        if not narration_text or not keywords:
            logger.debug(f"段落 {track.get('segment_id')} 缺少文本或关键词，保持原始时间")
            return track
        
        # 查找关键词在文本中的位置
        keyword_positions = self._find_keywords_in_text(narration_text, keywords)
        
        if not keyword_positions:
            logger.debug(f"段落 {track.get('segment_id')} 未找到关键词位置，保持原始时间")
            return track
        
        # 选择最早出现的关键词作为环境音开始点
        earliest_position = min(keyword_positions, key=lambda x: x.start_pos)
        
        # 计算修正后的开始时间
        segment_start_time = track.get('start_time', 0.0)
        relative_time_offset = earliest_position.relative_time
        corrected_start_time = segment_start_time + relative_time_offset
        
        # 创建修正后的轨道
        corrected_track = track.copy()
        corrected_track.update({
            'original_start_time': segment_start_time,
            'start_time': corrected_start_time,
            'timeline_correction': {
                'applied': True,
                'offset_seconds': relative_time_offset,
                'keyword_found': earliest_position.keyword,
                'keyword_position': earliest_position.start_pos,
                'total_text_length': len(narration_text),
                'correction_confidence': earliest_position.relative_time / (track.get('duration', 10.0))
            }
        })
        
        logger.info(f"🕐 轨道时间修正: '{earliest_position.keyword}' "
                   f"从 {segment_start_time:.1f}s 调整为 {corrected_start_time:.1f}s "
                   f"(偏移 +{relative_time_offset:.1f}s)")
        
        return corrected_track
    
    def _find_keywords_in_text(self, text: str, keywords: List[str]) -> List[KeywordPosition]:
        """查找关键词在文本中的位置"""
        positions = []
        
        for keyword in keywords:
            # 获取关键词的所有变体
            variants = self._get_keyword_variants(keyword)
            
            for variant in variants:
                # 查找变体在文本中的所有出现位置
                matches = list(re.finditer(re.escape(variant), text))
                
                for match in matches:
                    start_pos = match.start()
                    end_pos = match.end()
                    
                    # 计算相对时间（基于字符位置和语速）
                    relative_time = self._calculate_relative_time_from_position(
                        start_pos, len(text)
                    )
                    
                    positions.append(KeywordPosition(
                        keyword=variant,
                        start_pos=start_pos,
                        end_pos=end_pos,
                        relative_time=relative_time
                    ))
        
        return positions
    
    def _get_keyword_variants(self, keyword: str) -> List[str]:
        """获取关键词的所有变体"""
        # 首先包含原关键词
        variants = [keyword]
        
        # 添加预定义的变体
        for base_keyword, variant_list in self.keyword_variants.items():
            if base_keyword in keyword or keyword in base_keyword:
                variants.extend(variant_list)
        
        # 去重并按长度排序（优先匹配更具体的词）
        variants = list(set(variants))
        variants.sort(key=len, reverse=True)
        
        return variants
    
    def _calculate_relative_time_from_position(self, char_position: int, total_length: int) -> float:
        """根据字符位置计算在段落中的相对时间"""
        if total_length == 0:
            return 0.0
        
        # 计算字符位置在文本中的比例
        position_ratio = char_position / total_length
        
        # 根据语速计算总段落时长
        total_duration_minutes = total_length / self.CHINESE_SPEECH_RATE
        total_duration_seconds = total_duration_minutes * 60.0
        
        # 计算相对时间
        relative_time = position_ratio * total_duration_seconds
        
        # 确保相对时间合理 (不超过段落总时长)
        max_duration = min(total_duration_seconds, 60.0)  # 最大60秒
        relative_time = min(relative_time, max_duration * 0.9)  # 最多90%的位置
        
        return relative_time
    
    def get_correction_summary(self, original_tracks: List[Dict], 
                             corrected_tracks: List[Dict]) -> Dict:
        """获取修正总结"""
        corrections_applied = 0
        total_offset = 0.0
        max_offset = 0.0
        
        for original, corrected in zip(original_tracks, corrected_tracks):
            if corrected.get('timeline_correction', {}).get('applied', False):
                corrections_applied += 1
                offset = corrected['timeline_correction']['offset_seconds']
                total_offset += offset
                max_offset = max(max_offset, offset)
        
        return {
            'total_tracks': len(original_tracks),
            'corrections_applied': corrections_applied,
            'correction_rate': corrections_applied / len(original_tracks) if original_tracks else 0,
            'average_offset': total_offset / corrections_applied if corrections_applied else 0,
            'max_offset': max_offset,
            'summary': f"修正了 {corrections_applied}/{len(original_tracks)} 个轨道的时间轴"
        } 