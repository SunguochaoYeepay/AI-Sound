"""
章节环境分析器
增强版环境音分析引擎，支持精确时长计算、强度分析和时间轴生成
为新的环境音优化流程提供核心分析能力
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import asyncio
import re

from .narration_environment_analyzer import NarrationEnvironmentAnalyzer
from .llm_scene_analyzer import OllamaLLMSceneAnalyzer

logger = logging.getLogger(__name__)

class ChapterEnvironmentAnalyzer(NarrationEnvironmentAnalyzer):
    """章节环境分析器 - 增强版分析引擎"""
    
    def __init__(self):
        super().__init__()
        # 增强配置
        self.PRECISE_SPEECH_RATES = {
            '旁白': 280,  # 每分钟字符数 - 旁白语速较慢，更沉稳
            '对话': 400,  # 对话语速较快
            '独白': 320,  # 独白介于两者之间
        }
        
        # 环境音强度配置
        self.INTENSITY_KEYWORDS = {
            'high': ['暴雨', '雷鸣', '狂风', '巨响', '轰隆', '震耳欲聋'],
            'medium': ['雨声', '风声', '鸟鸣', '流水', '脚步'],
            'low': ['微风', '细雨', '虫鸣', '轻音', '低语']
        }
        
        # 环境音持续性分析
        self.CONTINUITY_KEYWORDS = {
            'ambient': ['天气', '背景', '环境', '氛围'],  # 持续性环境音
            'event': ['突然', '瞬间', '忽然', '一声'],    # 事件性声音
            'transition': ['渐渐', '慢慢', '逐渐']        # 渐变声音
        }
    
    async def analyze_chapter_environment(self, 
                                        chapter_content: str, 
                                        synthesis_plan: List[Dict],
                                        options: Dict = None) -> Dict[str, Any]:
        """
        章节级环境音分析 - 新流程的核心方法
        
        Args:
            chapter_content: 章节原始内容
            synthesis_plan: 智能准备生成的合成计划
            options: 分析选项
            
        Returns:
            完整的环境音分析结果，包含时间轴和配置建议
        """
        logger.info(f"[CHAPTER_ANALYZER] 开始章节环境音分析，合成段落数: {len(synthesis_plan)}")
        
        try:
            # 步骤1: 基础环境音分析（复用现有能力）
            base_analysis = await self.extract_and_analyze_narration(synthesis_plan)
            
            # 步骤2: 精确时长计算
            precise_timeline = self._calculate_precise_timeline(synthesis_plan, base_analysis)
            
            # 步骤3: 环境音强度分析
            intensity_analysis = self._analyze_environment_intensity(base_analysis['environment_tracks'])
            
            # 步骤4: 环境音连续性分析
            continuity_analysis = self._analyze_environment_continuity(
                base_analysis['environment_tracks'], 
                synthesis_plan
            )
            
            # 步骤5: 生成优化的环境音配置
            optimized_config = self._generate_optimized_environment_config(
                precise_timeline,
                intensity_analysis,
                continuity_analysis,
                base_analysis['environment_tracks']  # 传递原始环境轨道数据
            )
            
            # 步骤6: 生成视频编辑兼容的时间轴
            video_timeline = self._generate_video_timeline(optimized_config)
            
            logger.info(f"[CHAPTER_ANALYZER] 章节分析完成，生成{len(optimized_config)}个优化环境音轨道")
            
            return {
                'success': True,
                'analysis_result': {
                    'environment_tracks': optimized_config,
                    'video_timeline': video_timeline,
                    'analysis_metadata': {
                        'total_duration': precise_timeline.get('total_duration', 0),
                        'track_count': len(optimized_config),
                        'intensity_distribution': self._get_intensity_distribution(intensity_analysis),
                        'continuity_types': self._get_continuity_types(continuity_analysis),
                        'analysis_timestamp': datetime.now().isoformat(),
                        'analyzer_version': '2.0_enhanced'
                    }
                },
                'analysis_stats': self._generate_enhanced_stats(optimized_config, precise_timeline)
            }
            
        except Exception as e:
            logger.error(f"[CHAPTER_ANALYZER] 章节分析失败: {str(e)}")
            raise RuntimeError(f"章节环境音分析失败: {str(e)}")
    
    def _calculate_precise_timeline(self, synthesis_plan: List[Dict], base_analysis: Dict) -> Dict:
        """精确时长计算 - 考虑语速变化、停顿和情感"""
        logger.info("[TIMELINE] 开始精确时长计算")
        
        timeline = {
            'segments': [],
            'total_duration': 0.0,
            'calculation_method': 'precise'
        }
        
        cumulative_time = 0.0
        
        for segment in synthesis_plan:
            segment_id = segment.get('segment_id') or segment.get('id', 'unknown')
            text = segment.get('text', '') or segment.get('content', '')
            speaker = segment.get('speaker', '').strip()
            emotion = segment.get('emotion', 'neutral')
            
            # 根据说话人类型选择语速
            if speaker in ['旁白', 'narrator', '叙述者']:
                base_rate = self.PRECISE_SPEECH_RATES['旁白']
            elif speaker and speaker != '旁白':
                base_rate = self.PRECISE_SPEECH_RATES['对话']
            else:
                base_rate = self.PRECISE_SPEECH_RATES['独白']
            
            # 情感语速调整
            emotion_modifiers = {
                'excited': 1.2,    # 兴奋时语速加快
                'nervous': 1.1,    # 紧张时略快
                'sad': 0.8,        # 悲伤时放慢
                'contemplative': 0.9,  # 沉思时较慢
                'neutral': 1.0     # 中性
            }
            
            rate_modifier = emotion_modifiers.get(emotion, 1.0)
            adjusted_rate = base_rate * rate_modifier
            
            # 计算持续时间
            char_count = len(text.replace(' ', '').replace('\n', ''))
            duration_minutes = char_count / adjusted_rate
            duration_seconds = duration_minutes * 60.0
            
            # 添加标点停顿时间
            pause_time = self._calculate_pause_time(text)
            final_duration = max(1.0, duration_seconds + pause_time)
            
            timeline['segments'].append({
                'segment_id': segment_id,
                'start_time': cumulative_time,
                'duration': final_duration,
                'end_time': cumulative_time + final_duration,
                'speaker': speaker,
                'emotion': emotion,
                'text_length': char_count,
                'speech_rate': adjusted_rate,
                'pause_time': pause_time
            })
            
            cumulative_time += final_duration
        
        timeline['total_duration'] = cumulative_time
        logger.info(f"[TIMELINE] 精确时长计算完成，总时长: {cumulative_time:.1f}秒")
        
        return timeline
    
    def _calculate_pause_time(self, text: str) -> float:
        """计算标点符号带来的停顿时间"""
        pause_weights = {
            '。': 0.8,   # 句号
            '！': 0.6,   # 感叹号
            '？': 0.6,   # 问号
            '，': 0.3,   # 逗号
            '；': 0.5,   # 分号
            '：': 0.4,   # 冒号
            '…': 1.0,   # 省略号
            '——': 0.5   # 破折号
        }
        
        total_pause = 0.0
        for punctuation, weight in pause_weights.items():
            count = text.count(punctuation)
            total_pause += count * weight
        
        return total_pause
    
    def _analyze_environment_intensity(self, environment_tracks: List[Dict]) -> Dict:
        """环境音强度分析"""
        logger.info("[INTENSITY] 开始环境音强度分析")
        
        intensity_analysis = {}
        
        for track in environment_tracks:
            track_id = track['segment_id']
            keywords = track.get('environment_keywords', [])
            scene_description = track.get('scene_description', '')
            narration_text = track.get('narration_text', '')
            
            # 分析文本中的强度关键词
            combined_text = f"{scene_description} {narration_text}".lower()
            
            intensity_score = 0.5  # 默认中等强度
            intensity_level = 'medium'
            
            # 检查高强度关键词
            for keyword in self.INTENSITY_KEYWORDS['high']:
                if keyword in combined_text:
                    intensity_score = max(intensity_score, 0.9)
                    intensity_level = 'high'
                    break
            
            # 检查低强度关键词
            if intensity_level != 'high':
                for keyword in self.INTENSITY_KEYWORDS['low']:
                    if keyword in combined_text:
                        intensity_score = 0.3
                        intensity_level = 'low'
                        break
            
            # 根据环境音类型调整
            sound_type_modifiers = {
                '雷声': 0.9, '暴雨': 0.8, '狂风': 0.8,
                '鸟鸣': 0.4, '虫鸣': 0.3, '微风': 0.2
            }
            
            for keyword in keywords:
                if keyword in sound_type_modifiers:
                    intensity_score = max(intensity_score, sound_type_modifiers[keyword])
                    break
            
            intensity_analysis[track_id] = {
                'intensity_level': intensity_level,
                'intensity_score': intensity_score,
                'volume_recommendation': intensity_score * 0.8,  # 音量建议
                'fade_in_duration': 2.0 if intensity_level == 'low' else 1.0,
                'fade_out_duration': 2.0 if intensity_level == 'low' else 1.5
            }
        
        logger.info(f"[INTENSITY] 强度分析完成，分析{len(intensity_analysis)}个轨道")
        return intensity_analysis
    
    def _analyze_environment_continuity(self, environment_tracks: List[Dict], synthesis_plan: List[Dict]) -> Dict:
        """环境音连续性分析"""
        logger.info("[CONTINUITY] 开始环境音连续性分析")
        
        continuity_analysis = {}
        
        # 按时间顺序排序
        sorted_tracks = sorted(environment_tracks, key=lambda x: x['start_time'])
        
        for i, track in enumerate(sorted_tracks):
            track_id = track['segment_id']
            keywords = track.get('environment_keywords', [])
            narration_text = track.get('narration_text', '').lower()
            
            # 确定连续性类型
            continuity_type = 'event'  # 默认事件型
            
            # 检查是否为环境型（持续性）
            for keyword in self.CONTINUITY_KEYWORDS['ambient']:
                if keyword in narration_text:
                    continuity_type = 'ambient'
                    break
            
            # 检查是否为渐变型
            for keyword in self.CONTINUITY_KEYWORDS['transition']:
                if keyword in narration_text:
                    continuity_type = 'transition'
                    break
            
            # 检查与前后轨道的关联性
            prev_connection = None
            next_connection = None
            
            if i > 0:
                prev_track = sorted_tracks[i-1]
                prev_keywords = set(prev_track.get('environment_keywords', []))
                curr_keywords = set(keywords)
                if prev_keywords & curr_keywords:  # 有共同关键词
                    prev_connection = {
                        'track_id': prev_track['segment_id'],
                        'shared_keywords': list(prev_keywords & curr_keywords),
                        'connection_strength': len(prev_keywords & curr_keywords) / max(len(prev_keywords), len(curr_keywords))
                    }
            
            if i < len(sorted_tracks) - 1:
                next_track = sorted_tracks[i+1]
                next_keywords = set(next_track.get('environment_keywords', []))
                curr_keywords = set(keywords)
                if next_keywords & curr_keywords:
                    next_connection = {
                        'track_id': next_track['segment_id'],
                        'shared_keywords': list(next_keywords & curr_keywords),
                        'connection_strength': len(next_keywords & curr_keywords) / max(len(next_keywords), len(curr_keywords))
                    }
            
            continuity_analysis[track_id] = {
                'continuity_type': continuity_type,
                'prev_connection': prev_connection,
                'next_connection': next_connection,
                'loop_recommendation': continuity_type == 'ambient',
                'crossfade_recommendation': bool(prev_connection or next_connection)
            }
        
        logger.info(f"[CONTINUITY] 连续性分析完成，分析{len(continuity_analysis)}个轨道")
        return continuity_analysis
    
    def _generate_optimized_environment_config(self, 
                                             timeline: Dict, 
                                             intensity_analysis: Dict, 
                                             continuity_analysis: Dict,
                                             environment_tracks: List[Dict]) -> List[Dict]:
        """生成优化的环境音配置"""
        logger.info("[CONFIG] 开始生成优化环境音配置")
        
        # 创建segment_id到环境轨道的映射
        track_map = {}
        for track in environment_tracks:
            track_map[track['segment_id']] = track
        
        logger.info(f"[CONFIG] 原始环境轨道映射: {len(track_map)}个轨道")
        for seg_id, track in track_map.items():
            keywords = track.get('environment_keywords', [])
            logger.info(f"[CONFIG] 段落{seg_id}: 关键词{keywords}")
        
        optimized_tracks = []
        
        for segment in timeline['segments']:
            segment_id = segment['segment_id']
            
            # 检查是否有环境音数据
            if segment_id not in intensity_analysis:
                continue
            
            intensity_data = intensity_analysis[segment_id]
            continuity_data = continuity_analysis.get(segment_id, {})
            original_track = track_map.get(segment_id, {})
            
            # 生成优化配置
            track_config = {
                'segment_id': segment_id,
                'start_time': segment['start_time'],
                'duration': segment['duration'],
                'end_time': segment['end_time'],
                
                # 音频属性
                'volume': intensity_data['volume_recommendation'],
                'fade_in': intensity_data['fade_in_duration'],
                'fade_out': intensity_data['fade_out_duration'],
                'loop_enabled': continuity_data.get('loop_recommendation', False),
                
                # 环境音信息 - 从原始轨道获取
                'environment_keywords': original_track.get('environment_keywords', []),
                'scene_description': original_track.get('scene_description', ''),
                'narration_text': original_track.get('narration_text', ''),
                'confidence': original_track.get('confidence', 0.8),
                'intensity_level': intensity_data['intensity_level'],
                'continuity_type': continuity_data.get('continuity_type', 'event'),
                
                # 连接信息
                'crossfade_enabled': continuity_data.get('crossfade_recommendation', False),
                'prev_connection': continuity_data.get('prev_connection'),
                'next_connection': continuity_data.get('next_connection'),
                
                # 元数据
                'optimization_version': '2.0',
                'generated_at': datetime.now().isoformat()
            }
            
            optimized_tracks.append(track_config)
        
        logger.info(f"[CONFIG] 生成{len(optimized_tracks)}个优化环境音配置")
        return optimized_tracks
    
    def _generate_video_timeline(self, optimized_config: List[Dict]) -> Dict:
        """生成视频编辑兼容的时间轴"""
        video_timeline = {
            'timeline_version': '1.0',
            'generated_at': datetime.now().isoformat(),
            'total_tracks': len(optimized_config),
            'total_duration': max([track['end_time'] for track in optimized_config]) if optimized_config else 0,
            'tracks': []
        }
        
        for i, track in enumerate(optimized_config):
            video_track = {
                'track_id': i + 1,
                'segment_id': track['segment_id'],
                'start_time': track['start_time'],
                'duration': track['duration'],
                'volume': track['volume'],
                'fade_in': track['fade_in'],
                'fade_out': track['fade_out'],
                'loop': track['loop_enabled'],
                'environment_sound_id': None,  # 待匹配
                'sound_name': None,            # 待匹配
                'metadata': {
                    'intensity_level': track['intensity_level'],
                    'continuity_type': track['continuity_type'],
                    'keywords': track['environment_keywords']
                }
            }
            video_timeline['tracks'].append(video_track)
        
        return video_timeline
    
    def _get_intensity_distribution(self, intensity_analysis: Dict) -> Dict:
        """获取强度分布统计"""
        distribution = {'high': 0, 'medium': 0, 'low': 0}
        for data in intensity_analysis.values():
            level = data['intensity_level']
            distribution[level] += 1
        return distribution
    
    def _get_continuity_types(self, continuity_analysis: Dict) -> Dict:
        """获取连续性类型统计"""
        types = {'ambient': 0, 'event': 0, 'transition': 0}
        for data in continuity_analysis.values():
            ctype = data['continuity_type']
            types[ctype] += 1
        return types
    
    def _generate_enhanced_stats(self, optimized_config: List[Dict], timeline: Dict) -> Dict:
        """生成增强统计信息"""
        if not optimized_config:
            return {
                'total_tracks': 0,
                'total_duration': 0,
                'avg_duration': 0,
                'optimization_features': {}
            }
        
        total_duration = timeline['total_duration']
        avg_duration = total_duration / len(optimized_config)
        
        # 优化特性统计
        features = {
            'precise_timing': True,
            'intensity_analysis': True,
            'continuity_analysis': True,
            'crossfade_tracks': sum(1 for t in optimized_config if t.get('crossfade_enabled')),
            'loop_tracks': sum(1 for t in optimized_config if t.get('loop_enabled')),
            'high_intensity_tracks': sum(1 for t in optimized_config if t.get('intensity_level') == 'high'),
            'ambient_tracks': sum(1 for t in optimized_config if t.get('continuity_type') == 'ambient')
        }
        
        return {
            'total_tracks': len(optimized_config),
            'total_duration': round(total_duration, 1),
            'avg_duration': round(avg_duration, 1),
            'optimization_features': features,
            'enhancement_level': 'advanced'
        }
    
    async def analyze_batch_chapters_environment(self, chapters: List[Dict]) -> Dict[str, Any]:
        """批量章节环境音分析 - 简化版测试方法"""
        logger.info(f"[BATCH_ANALYZER] 开始批量分析{len(chapters)}个章节")
        
        # 模拟合成计划（实际应该从数据库或智能准备模块获取）
        mock_synthesis_plan = []
        segment_id = 1
        
        for chapter in chapters:
            content = chapter.get('content', '')
            
            # 简单分段：按句号分割
            sentences = [s.strip() for s in content.split('。') if s.strip()]
            
            for sentence in sentences:
                if sentence:
                    mock_synthesis_plan.append({
                        'segment_id': segment_id,
                        'text': sentence + '。',
                        'speaker': '旁白',
                        'emotion': 'neutral',
                        'chapter_id': chapter.get('chapter_id', 1)
                    })
                    segment_id += 1
        
        try:
            # 调用单章节分析方法
            result = await self.analyze_chapter_environment(
                chapters[0].get('content', ''),
                mock_synthesis_plan,
                {}
            )
            
            # 添加批量分析的元数据
            result['batch_info'] = {
                'chapters_analyzed': len(chapters),
                'total_segments': len(mock_synthesis_plan),
                'analysis_mode': 'batch_simplified'
            }
            
            logger.info(f"[BATCH_ANALYZER] 批量分析完成，处理{len(chapters)}个章节")
            return result
            
        except Exception as e:
            logger.error(f"[BATCH_ANALYZER] 批量分析失败: {str(e)}")
            # 返回基本错误信息
            return {
                'success': False,
                'error': str(e),
                'environment_tracks': [],
                'batch_info': {
                    'chapters_analyzed': 0,
                    'total_segments': 0,
                    'analysis_mode': 'batch_failed'
                }
            } 