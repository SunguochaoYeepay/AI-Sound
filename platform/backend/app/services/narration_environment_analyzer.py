"""
旁白环境分析器
从synthesis_plan提取旁白内容并分析环境关键词与时长
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class NarrationEnvironmentAnalyzer:
    """旁白环境分析器 - 从synthesis_plan提取旁白内容并分析环境"""
    
    def __init__(self):
        # 复用现有LLM分析器的分析能力
        from app.services.llm_scene_analyzer import OllamaLLMSceneAnalyzer
        self.scene_analyzer = OllamaLLMSceneAnalyzer()
        
        # 旁白语速配置 (每分钟字数)
        self.NARRATION_SPEED_CHARS_PER_MINUTE = 300
        
    async def extract_and_analyze_narration(self, synthesis_plan: List[Dict]) -> Dict:
        """从synthesis_plan提取旁白内容并分析环境关键词与时长"""
        logger.info(f"[NARRATION_ANALYZER] 开始分析synthesis_plan，共{len(synthesis_plan)}个段落")
        
        environment_tracks = []
        cumulative_time = 0.0
        narration_count = 0
        
        for segment in synthesis_plan:
            # 只处理旁白segments (旁白才会说环境内容)
            if segment.get('speaker') == '旁白' or segment.get('character') == '旁白':
                narration_count += 1
                
                # 计算旁白时长 (旁白语速固定，内容已在JSON)
                narration_text = segment.get('text', '') or segment.get('content', '')
                estimated_duration = self._calculate_narration_duration(narration_text)
                
                segment_id = segment.get('segment_id') or segment.get('id', f'seg_{narration_count}')
                logger.info(f"[NARRATION_ANALYZER] 处理旁白段落 {segment_id}: "
                           f"时长{estimated_duration:.1f}s，内容: {narration_text[:50]}...")
                
                # LLM分析环境关键词
                try:
                    # 使用LLM分析器的文本场景分析方法
                    # 首先检查LLM服务是否可用
                    llm_available = await self.scene_analyzer.check_ollama_status()
                    
                    if llm_available:
                        llm_result = await self.scene_analyzer.analyze_text_scenes_with_llm(narration_text)
                    else:
                        # LLM不可用时，使用简单的关键词匹配作为后备
                        logger.warning("[NARRATION_ANALYZER] LLM服务不可用，使用关键词匹配后备方案")
                        llm_result = self._fallback_keyword_analysis(narration_text)
                    
                    # 转换为我们需要的格式
                    environment_analysis = {
                        'environment_detected': len(llm_result.analyzed_scenes) > 0,
                        'scene_keywords': [],
                        'scene_description': '',
                        'confidence': llm_result.confidence_score
                    }
                    
                    # 提取关键词和场景描述
                    if llm_result.analyzed_scenes:
                        for scene in llm_result.analyzed_scenes:
                            environment_analysis['scene_keywords'].extend(scene.keywords)
                            if scene.location:
                                environment_analysis['scene_description'] += f"{scene.location} "
                            if scene.atmosphere:
                                environment_analysis['scene_description'] += f"{scene.atmosphere} "
                        
                        # 去重关键词
                        environment_analysis['scene_keywords'] = list(set(environment_analysis['scene_keywords']))
                        environment_analysis['scene_description'] = environment_analysis['scene_description'].strip()
                    
                    if environment_analysis.get('environment_detected'):
                        environment_tracks.append({
                            'segment_id': segment_id,
                            'start_time': cumulative_time,
                            'duration': estimated_duration,
                            'narration_text': narration_text,
                            'environment_keywords': environment_analysis.get('scene_keywords', []),
                            'scene_description': environment_analysis.get('scene_description', ''),
                            'confidence': environment_analysis.get('confidence', 0.0),
                            'analysis_timestamp': datetime.now().isoformat()
                        })
                        
                        logger.info(f"[NARRATION_ANALYZER] 检测到环境: {environment_analysis.get('scene_keywords', [])}")
                    else:
                        logger.info(f"[NARRATION_ANALYZER] 段落无环境描述，跳过")
                        
                except Exception as e:
                    logger.error(f"[NARRATION_ANALYZER] LLM分析失败: {str(e)}")
                    # 分析失败时，仍记录基础信息但标记为未分析
                    environment_tracks.append({
                        'segment_id': segment_id,
                        'start_time': cumulative_time,
                        'duration': estimated_duration,
                        'narration_text': narration_text,
                        'environment_keywords': [],
                        'scene_description': '分析失败',
                        'confidence': 0.0,
                        'analysis_error': str(e),
                        'analysis_timestamp': datetime.now().isoformat()
                    })
                
                cumulative_time += estimated_duration
            else:
                # 非旁白段落，累加时长但不分析环境
                segment_duration = self._calculate_segment_duration(segment)
                cumulative_time += segment_duration
                
        logger.info(f"[NARRATION_ANALYZER] 分析完成: 总时长{cumulative_time:.1f}s，"
                   f"旁白段落{narration_count}个，环境音轨道{len(environment_tracks)}个")
                
        return {
            'environment_tracks': environment_tracks,
            'analysis_summary': {
                'total_duration': cumulative_time,
                'narration_segments': narration_count,
                'environment_tracks_detected': len(environment_tracks),
                'analysis_timestamp': datetime.now().isoformat()
            }
        }
        
    def _calculate_narration_duration(self, text: str) -> float:
        """计算旁白时长 (语速固定)"""
        if not text or not text.strip():
            return 0.0
            
        # 去除空白字符，计算有效字符数
        char_count = len(text.replace(' ', '').replace('\n', '').replace('\t', ''))
        
        # 根据固定语速计算时长
        duration_minutes = char_count / self.NARRATION_SPEED_CHARS_PER_MINUTE
        duration_seconds = duration_minutes * 60.0
        
        # 最少1秒，最多60秒
        return max(1.0, min(duration_seconds, 60.0))
        
    def _calculate_segment_duration(self, segment: Dict) -> float:
        """计算其他段落时长"""
        # 尝试从segment中获取预估时长
        if 'estimated_duration' in segment:
            return float(segment['estimated_duration'])
            
        # 如果没有预估时长，根据文本长度计算
        text = segment.get('text', '') or segment.get('content', '')
        if text:
            # 对话通常比旁白语速快一些
            char_count = len(text.replace(' ', '').replace('\n', ''))
            duration_minutes = char_count / 400  # 对话语速更快
            return max(0.5, duration_minutes * 60.0)
            
        return 1.0  # 默认1秒
        
    def get_analysis_stats(self, analysis_result: Dict) -> Dict:
        """获取分析统计信息"""
        environment_tracks = analysis_result.get('environment_tracks', [])
        
        if not environment_tracks:
            return {
                'total_tracks': 0,
                'total_duration': 0.0,
                'avg_duration': 0.0,
                'keyword_distribution': {},
                'confidence_distribution': {}
            }
            
        total_duration = sum(track['duration'] for track in environment_tracks)
        avg_duration = total_duration / len(environment_tracks)
        
        # 关键词分布统计
        keyword_count = {}
        for track in environment_tracks:
            for keyword in track.get('environment_keywords', []):
                keyword_count[keyword] = keyword_count.get(keyword, 0) + 1
                
        # 置信度分布统计
        confidence_ranges = {'高(>0.8)': 0, '中(0.5-0.8)': 0, '低(<0.5)': 0}
        for track in environment_tracks:
            confidence = track.get('confidence', 0.0)
            if confidence > 0.8:
                confidence_ranges['高(>0.8)'] += 1
            elif confidence > 0.5:
                confidence_ranges['中(0.5-0.8)'] += 1
            else:
                confidence_ranges['低(<0.5)'] += 1
                
        return {
            'total_tracks': len(environment_tracks),
            'total_duration': round(total_duration, 1),
            'avg_duration': round(avg_duration, 1),
            'keyword_distribution': dict(sorted(keyword_count.items(), key=lambda x: x[1], reverse=True)),
            'confidence_distribution': confidence_ranges
        }
        
    def _fallback_keyword_analysis(self, text: str):
        """LLM不可用时的关键词匹配后备方案"""
        from app.services.sequential_timeline_generator import SceneInfo
        from dataclasses import dataclass
        
        # 模拟LLMSceneAnalysisResult结构
        @dataclass
        class MockLLMResult:
            analyzed_scenes: List[SceneInfo]
            confidence_score: float
            
        # 简单的关键词匹配
        environment_keywords = []
        scene_description = ""
        
        # 环境关键词字典
        keyword_mapping = {
            '森林': ['forest', 'trees', 'nature'],
            '夜晚': ['night', 'dark', 'evening'],
            '风声': ['wind', 'breeze'],
            '狼嚎': ['wolf', 'howl'],
            '木屋': ['cabin', 'house', 'indoor'],
            '脚步声': ['footsteps', 'walking'],
            '回声': ['echo', 'reverb'],
            '安静': ['quiet', 'silence'],
            '时钟': ['clock', 'ticking'],
            '房间': ['room', 'indoor']
        }
        
        text_lower = text.lower()
        for keyword, tags in keyword_mapping.items():
            if keyword in text:
                environment_keywords.extend(tags)
                scene_description += f"{keyword} "
                
        # 创建模拟场景
        if environment_keywords:
            scene = SceneInfo(
                location=scene_description.strip(),
                atmosphere="ambient",
                keywords=environment_keywords,
                confidence=0.6  # 后备方案置信度较低
            )
            return MockLLMResult(
                analyzed_scenes=[scene],
                confidence_score=0.6
            )
        else:
            return MockLLMResult(
                analyzed_scenes=[],
                confidence_score=0.0
            ) 