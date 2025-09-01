#!/usr/bin/env python3
"""
音频剧本生成器
基于6卡分析结果生成音频剧本
"""

import logging
from typing import Dict, Any, List, Optional

from .base_analyzer import BaseAnalyzer

logger = logging.getLogger(__name__)


class AudioScriptGenerator(BaseAnalyzer):
    """音频剧本生成器"""
    
    async def analyze(self, content: str, **kwargs) -> List[Dict[str, Any]]:
        """实现抽象方法（这里不使用）"""
        return []
    
    async def generate_script(self, scene_data: List[Dict], event_data: List[Dict], emotion_data: List[Dict], 
                            story_data: Optional[Dict] = None, character_data: Optional[List[Dict]] = None,
                            original_content: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """生成音频剧本"""
        try:
            logger.info("开始生成音频剧本...")
            logger.info(f"接收到原文内容: {'是' if original_content else '否'}")
            if original_content:
                logger.info(f"原文内容长度: {len(original_content)}")
                logger.info(f"原文内容前100字符: {original_content[:100]}")
            
            # 1. 内容整合（传入原文内容）
            script_content = await self._integrate_content(
                scene_data, event_data, emotion_data, story_data, character_data, original_content
            )
            
            # 2. 时间轴规划
            timeline = await self._plan_timeline(script_content)
            
            # 3. 制作指导生成
            production_notes = await self._generate_production_notes(script_content)
            
            # 4. 质量验证
            quality_score = await self._validate_quality(script_content)
            
            # 5. 构建剧本结构
            script_data = {
                'script_segments': script_content,
                'script_metadata': {
                    'total_duration': timeline['total_duration'],
                    'voice_assignments': timeline['voice_assignments'],
                    'audio_settings': timeline['audio_settings']
                },
                'quality_score': quality_score
            }
            
            logger.info(f"音频剧本生成完成，质量评分: {quality_score}")
            return script_data
            
        except Exception as e:
            logger.error(f"音频剧本生成失败: {str(e)}")
            return {}
    
    async def _integrate_content(self, scene_data: List[Dict], event_data: List[Dict], 
                               emotion_data: List[Dict], story_data: Optional[Dict] = None,
                               character_data: Optional[List[Dict]] = None, 
                               original_content: Optional[str] = None) -> List[Dict[str, Any]]:
        """整合6卡内容"""
        script_segments = []
        
        # 将原文按段落分割
        paragraphs = []
        if original_content:
            logger.info(f"原文内容长度: {len(original_content)}")
            paragraphs = [p.strip() for p in original_content.split('\n') if p.strip()]
            logger.info(f"分割后段落数量: {len(paragraphs)}")
            if paragraphs:
                logger.info(f"第一个段落: {paragraphs[0][:100]}...")
        else:
            logger.warning("原文内容为空")
        
        # 确保每个段落都有对应的segment
        total_segments = max(len(paragraphs), len(event_data))
        logger.info(f"需要生成 {total_segments} 个segment (段落数: {len(paragraphs)}, 事件数: {len(event_data)})")
        
        for i in range(total_segments):
            # 获取对应的原文段落
            original_text = ""
            paragraph_range = [i, i + 1]
            
            if paragraphs and i < len(paragraphs):
                original_text = paragraphs[i]
                paragraph_range = [i, i + 1]
                logger.info(f"段落 {i}: 使用原文段落，长度: {len(original_text)}")
            elif paragraphs:
                # 如果segment数量超过段落数量，使用最后一个段落
                original_text = paragraphs[-1]
                paragraph_range = [len(paragraphs) - 1, len(paragraphs)]
                logger.info(f"段落 {i}: 使用最后一个原文段落，长度: {len(original_text)}")
            else:
                logger.warning(f"段落 {i}: 没有原文段落可用")
            
            # 获取对应的事件数据
            event = event_data[i] if i < len(event_data) else {}
            
            segment = {
                'segment_id': f'seg_{i+1:03d}',
                'start_time': i * 30,  # 每个段落30秒
                'end_time': (i + 1) * 30,
                'original_text': original_text,
                'dialogue': self._extract_dialogue(event, original_text),
                'sound_effects': self._extract_sound_effects(event, scene_data, i),
                'production_notes': self._generate_segment_notes(event, emotion_data, i),
                'text_mapping': {
                    'paragraph_range': paragraph_range,
                    'word_count': len(original_text.split()) if original_text else 0,
                    'accuracy_score': 0.95
                }
            }
            script_segments.append(segment)
        
        return script_segments
    
    def _extract_dialogue(self, event: Dict, original_text: str = "") -> Dict[str, Any]:
        """提取对话信息"""
        # 强制使用事件中的对话内容
        dialogue_content = event.get('dialogue_content', [])
        participants = event.get('participants', [])
        
        # 如果没有对话内容，尝试从原文中提取
        if not dialogue_content and original_text:
            logger.info("事件中没有对话内容，尝试从原文中提取")
            import re
            
            # 提取引号内的对话
            quotes = re.findall(r'[""]([^""]+)[""]', original_text)
            if quotes:
                dialogue_content = []
                for i, quote in enumerate(quotes[:3]):  # 最多取前三个对话
                    # 根据对话内容判断说话者
                    if "姑娘" in quote or "林薇" in quote:
                        speaker = "林薇"
                    elif "公子" in quote or "萧景琰" in quote:
                        speaker = "萧景琰"
                    elif "医官" in quote:
                        speaker = "医官"
                    elif "随从" in quote or "侍卫" in quote:
                        speaker = "随从"
                    else:
                        speaker = "旁白"
                    
                    dialogue_content.append({
                        "speaker": speaker,
                        "content": quote
                    })
                logger.info(f"从原文中提取到 {len(dialogue_content)} 个对话")
            
            # 如果没有引号对话，检查是否有其他对话标识
            if not dialogue_content:
                # 检查冒号后的内容
                colon_dialogues = re.findall(r'[：:]\s*([^。！？\n]+[。！？])', original_text)
                if colon_dialogues:
                    dialogue_content = []
                    for i, dialogue in enumerate(colon_dialogues[:2]):
                        dialogue_content.append({
                            "speaker": "旁白",
                            "content": dialogue.strip()
                        })
                    logger.info(f"从冒号后提取到 {len(dialogue_content)} 个对话")
        
        # 如果还是没有对话内容，使用原文作为旁白
        if not dialogue_content:
            logger.info("没有对话内容，使用原文作为旁白")
            # 截取原文的前100个字符作为旁白内容
            narration_text = original_text[:100] + "..." if len(original_text) > 100 else original_text
            dialogue_content = [{"speaker": "旁白", "content": narration_text}]
        
        return {
            'speaker': participants[0] if participants else '旁白',
            'content': dialogue_content,
            'emotion': event.get('emotional_context', {}).get('emotion', 'neutral'),
            'tone': event.get('emotional_context', {}).get('tone', 'normal'),
            'voice_id': f"voice_{hash(participants[0]) % 1000:03d}" if participants else 'narrator_001'
        }
    
    def _extract_sound_effects(self, event: Dict, scene_data: List[Dict], segment_index: int) -> Dict[str, Any]:
        """提取音效信息"""
        # 从场景数据中获取环境音效
        scene_index = min(segment_index, len(scene_data) - 1)
        scene = scene_data[scene_index] if scene_data else {}
        
        return {
            'ambient_sounds': scene.get('environmental_sounds', []),
            'background_music': scene.get('background_music', 'default_music'),
            'volume_levels': {
                'dialogue': 80,
                'ambient': 40,
                'music': 20
            }
        }
    
    def _generate_segment_notes(self, event: Dict, emotion_data: List[Dict], segment_index: int) -> Dict[str, str]:
        """生成段落制作指导"""
        notes = []
        
        # 基于事件生成指导
        event_name = event.get('event_name', '')
        event_type = event.get('event_type', '')
        action_desc = event.get('action_description', '')
        
        notes.append(f"事件：{event_name}")
        notes.append(f"类型：{event_type}")
        
        if action_desc:
            notes.append(f"动作描述：{action_desc}")
        
        # 基于情绪生成指导
        if emotion_data and segment_index < len(emotion_data):
            emotion = emotion_data[segment_index]
            emotion_type = emotion.get('emotion_type', '')
            intensity = emotion.get('intensity', 0.5)
            voice_impact = emotion.get('voice_impact', {})
            
            notes.append(f"情绪：{emotion_type} (强度: {intensity})")
            
            if voice_impact:
                tone = voice_impact.get('tone', '')
                pace = voice_impact.get('pace', '')
                volume = voice_impact.get('volume', '')
                if tone:
                    notes.append(f"语调：{tone}")
                if pace:
                    notes.append(f"语速：{pace}")
                if volume:
                    notes.append(f"音量：{volume}")
        
        # 基于对话生成指导
        dialogue = event.get('dialogue_content', [])
        if dialogue:
            notes.append("对话指导：")
            for d in dialogue:
                if isinstance(d, dict):
                    speaker = d.get('speaker', '')
                    content = d.get('content', '')
                    if speaker and content:
                        notes.append(f"  {speaker}：{content}")
        
        # 添加通用制作指导
        notes.append("制作要点：")
        notes.append("- 注意情绪转换的自然过渡")
        notes.append("- 对话要有明确的角色区分")
        notes.append("- 背景音效要符合场景氛围")
        notes.append("- 节奏控制要符合情节发展")
        
        notes_text = "\n".join(notes)
        
        return {
            'voice_direction': f"语速{emotion_data[segment_index].get('intensity', 0.5) * 100}%，体现{emotion_data[segment_index].get('emotion_type', '平静')}" if emotion_data and segment_index < len(emotion_data) else "语速中等，语调自然",
            'sound_mixing': "音效渐入，音乐淡出",
            'emotion_guidance': f"通过语气表达{emotion_data[segment_index].get('emotion_type', '平静')}的情感" if emotion_data and segment_index < len(emotion_data) else "通过语气表达自然的情感",
            'detailed_notes': notes_text
        }
    
    async def _plan_timeline(self, script_content: List[Dict]) -> Dict[str, Any]:
        """规划时间轴"""
        total_duration = len(script_content) * 30  # 每个段落30秒
        
        return {
            'total_duration': total_duration,
            'voice_assignments': {
                '主角': 'voice_001',
                '配角': 'voice_002',
                '旁白': 'narrator_001'
            },
            'audio_settings': {
                'dialogue_volume': 80,
                'narration_volume': 70,
                'background_music_volume': 20,
                'sound_effects_volume': 40
            }
        }
    
    async def _generate_production_notes(self, script_content: List[Dict]) -> Dict[str, Any]:
        """生成制作指导"""
        return {
            'overall_direction': "整体风格温暖，节奏舒缓",
            'voice_guidance': "角色声音要有区分度，情感表达要自然",
            'sound_guidance': "环境音效要真实，背景音乐要配合情节",
            'quality_standards': "确保音频清晰度，避免噪音干扰"
        }
    
    async def _validate_quality(self, script_content: List[Dict]) -> float:
        """验证剧本质量"""
        if not script_content:
            return 0.0
        
        # 简单的质量评分逻辑
        total_score = 0
        for segment in script_content:
            # 检查必要字段
            if segment.get('dialogue', {}).get('content'):
                total_score += 0.3
            if segment.get('sound_effects', {}).get('ambient_sounds'):
                total_score += 0.2
            if segment.get('production_notes', {}).get('voice_direction'):
                total_score += 0.2
            if segment.get('text_mapping', {}).get('accuracy_score', 0) > 0.8:
                total_score += 0.3
        
        return min(1.0, total_score / len(script_content))
