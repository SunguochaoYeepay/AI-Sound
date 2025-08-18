"""
环境音分析器
核心逻辑：从synthesis_plan提取旁白 → LLM分析 → 生成环境音轨道
"""

import logging
import re
from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

class NarrationEnvironmentAnalyzer:
    """环境音分析器 - 简化版，只保留核心逻辑"""
    
    def __init__(self, db: Optional[Session] = None):
        # LLM分析器
        from app.services.llm_scene_analyzer import OllamaLLMSceneAnalyzer
        self.scene_analyzer = OllamaLLMSceneAnalyzer()
        self.db = db
        
    async def extract_and_analyze_narration(self, synthesis_plan: List[Dict]) -> Dict:
        """主入口：分析环境音"""
        logger.info(f"[ENV_ANALYZER] 开始分析，共{len(synthesis_plan)}个段落")
        
        # 1. 提取旁白段落
        narration_segments = self._extract_narration_segments(synthesis_plan)
        if not narration_segments:
            return self._empty_result()
        
        # 2. 构建LLM提示词
        prompt = self._build_analysis_prompt(narration_segments)
        
        # 3. LLM分析
        try:
            llm_result = await self.scene_analyzer.analyze_text_scenes_with_llm(prompt)
            if not llm_result.analyzed_scenes:
                return self._empty_result()
        except Exception as e:
            logger.error(f"[ENV_ANALYZER] LLM分析失败: {e}")
            return self._empty_result()
        
        # 4. 生成环境音轨道
        environment_tracks = self._generate_tracks(llm_result, narration_segments)
        
        return {
            'environment_tracks': environment_tracks,
            'analysis_summary': {
                'total_duration': sum(seg['duration'] for seg in narration_segments),
                'narration_segments': len(narration_segments),
                'environment_tracks_detected': len(environment_tracks),
                'analysis_timestamp': datetime.now().isoformat()
            }
        }
    
    def _extract_narration_segments(self, synthesis_plan: List[Dict]) -> List[Dict]:
        """提取旁白段落"""
        narration_segments = []
        current_time = 0.0
        
        for segment in synthesis_plan:
            # 识别旁白
            if self._is_narration(segment):
                text = segment.get('text', '') or segment.get('content', '')
                duration = self._calculate_duration(text)
                
                narration_segments.append({
                    'segment_id': segment.get('segment_id', f'seg_{len(narration_segments) + 1}'),
                    'text': text,
                    'start_time': current_time,
                    'duration': duration
                })
            
            current_time += self._calculate_duration(segment.get('text', '') or segment.get('content', ''))
        
        return narration_segments
    
    def _is_narration(self, segment: Dict) -> bool:
        """判断是否为旁白段落"""
        narration_speakers = ['旁白', 'narrator', '叙述者', 'narration']
        speaker = segment.get('speaker') or segment.get('character', '')
        return speaker in narration_speakers
    
    def _calculate_duration(self, text: str) -> float:
        """计算文本时长"""
        if not text:
            return 1.0
        char_count = len(text.replace(' ', '').replace('\n', ''))
        return max(1.0, char_count / 5.0)  # 5字符/秒
    
    def _build_analysis_prompt(self, narration_segments: List[Dict]) -> str:
        """构建LLM分析提示词"""
        prompt_parts = [
            "请分析以下小说段落中的环境声音，只识别文本中明确提到的声音。",
            "",
            "要求：",
            "1. 只提取声音词汇：如脚步声、说话声、雨声、风声等",
            "2. 不要联想：看到'御书房'不要联想'翻书声'",
            "3. 不要动作描述：如'走路'、'说话'等",
            "4. 最多3个关键词，没有声音返回[]",
            "",
            "段落内容："
        ]
        
        for i, seg in enumerate(narration_segments):
            prompt_parts.append(f"段落{i+1}: {seg['text']}")
        
        prompt_parts.extend([
            "",
            "请按段落顺序返回结果：",
            "段落1: [关键词1, 关键词2]",
            "段落2: []",
            "段落3: [关键词1]",
            "..."
        ])
        
        return "\n".join(prompt_parts)
    
    def _generate_tracks(self, llm_result, narration_segments: List[Dict]) -> List[Dict]:
        """生成环境音轨道"""
        tracks = []
        
        # 简单的一对一映射
        for i, segment in enumerate(narration_segments):
            if i < len(llm_result.analyzed_scenes):
                scene = llm_result.analyzed_scenes[i]
                keywords = self._clean_keywords(scene.keywords)
                
                if keywords:
                    tracks.append({
                        'segment_id': segment['segment_id'],
                        'start_time': segment['start_time'],
                        'duration': segment['duration'],
                        'narration_text': segment['text'],
                        'environment_keywords': keywords,
                        'confidence': scene.confidence,
                        'analysis_timestamp': datetime.now().isoformat()
                    })
        
        return tracks
    
    def _clean_keywords(self, keywords: List[str]) -> List[str]:
        """清理关键词"""
        if not keywords:
            return []
        
        cleaned = []
        for kw in keywords:
            if not kw or not isinstance(kw, str):
                continue
            
            # 基本清理
            kw = kw.strip()
            kw = re.sub(r'\d+\.?\d*s', '', kw)  # 移除时间
            kw = re.sub(r'[高中低]强度', '', kw)  # 移除强度
            kw = kw.strip()
            
            # 检查是否为声音词汇
            if self._is_sound_keyword(kw) and 2 <= len(kw) <= 8:
                cleaned.append(kw)
        
        return list(set(cleaned))[:3]  # 去重，最多3个
    
    def _is_sound_keyword(self, keyword: str) -> bool:
        """判断是否为声音关键词"""
        sound_indicators = ['声', '音', '响', '鸣', '叫', '吼', '啸', '嗡', '叮', '咚', '啪', '砰']
        return any(indicator in keyword for indicator in sound_indicators)
    
    def _empty_result(self) -> Dict:
        """返回空结果"""
        return {
            'environment_tracks': [],
            'analysis_summary': {
                'total_duration': 0.0,
                'narration_segments': 0,
                'environment_tracks_detected': 0,
                'analysis_timestamp': datetime.now().isoformat()
            }
        }
    
    # 保持向后兼容的方法
    async def extract_and_analyze_narration_batch(self, synthesis_plan: List[Dict]) -> Dict:
        """批量分析版本（向后兼容）"""
        return await self.extract_and_analyze_narration(synthesis_plan)
    
    async def extract_and_analyze_narration_individual(self, synthesis_plan: List[Dict]) -> Dict:
        """逐一分析版本（向后兼容）"""
        return await self.extract_and_analyze_narration(synthesis_plan)
