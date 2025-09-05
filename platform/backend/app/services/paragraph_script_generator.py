"""
段落剧本生成器服务
基于6卡分析结果，生成符合智能准备标准的synthesis_json格式
专注人声合成，确保输出JSON完全兼容现有系统
"""

import logging
import json
from typing import Dict, List, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class ParagraphScriptGenerator:
    """段落剧本生成器 - 基于6卡分析生成synthesis_json"""
    
    def __init__(self):
        # TTS参数映射规则
        self.character_tts_rules = {
            "主角": {
                "timeStep": 35,
                "pWeight": 1.6,
                "tWeight": 3.2,
                "dur_alpha": 1.0,
                "dur_disturb": 0.05
            },
            "重要配角": {
                "timeStep": 32,
                "pWeight": 1.5,
                "tWeight": 3.0,
                "dur_alpha": 1.0,
                "dur_disturb": 0.08
            },
            "一般配角": {
                "timeStep": 28,
                "pWeight": 1.3,
                "tWeight": 2.8,
                "dur_alpha": 0.95,
                "dur_disturb": 0.1
            },
            "背景角色": {
                "timeStep": 25,
                "pWeight": 1.2,
                "tWeight": 2.5,
                "dur_alpha": 0.9,
                "dur_disturb": 0.15
            },
            "群众": {
                "timeStep": 25,
                "pWeight": 1.2,
                "tWeight": 2.5,
                "dur_alpha": 0.9,
                "dur_disturb": 0.15
            },
            "旁白": {
                "timeStep": 30,
                "pWeight": 1.3,
                "tWeight": 2.8,
                "dur_alpha": 1.0,
                "dur_disturb": 0.05
            }
        }
        
        self.emotion_tts_rules = {
            "紧张": {
                "dur_alpha": 0.85,
                "pWeight": 1.7,
                "dur_disturb": 0.12
            },
            "悲伤": {
                "dur_alpha": 1.3,
                "pWeight": 1.2,
                "dur_disturb": 0.05
            },
            "兴奋": {
                "dur_alpha": 0.9,
                "pWeight": 1.6,
                "dur_disturb": 0.1
            },
            "愤怒": {
                "dur_alpha": 0.8,
                "pWeight": 1.8,
                "dur_disturb": 0.15
            },
            "平静": {
                "dur_alpha": 1.0,
                "pWeight": 1.4,
                "dur_disturb": 0.08
            }
        }
        
        self.event_tts_rules = {
            "关键转折": {
                "timeStep": 40,
                "pWeight": 1.8,
                "tWeight": 3.4,
                "dur_alpha": 0.9,
                "dur_disturb": 0.08
            },
            "日常对话": {
                "timeStep": 30,
                "pWeight": 1.4,
                "tWeight": 3.0,
                "dur_alpha": 1.0,
                "dur_disturb": 0.1
            },
            "战斗场景": {
                "timeStep": 35,
                "pWeight": 1.7,
                "tWeight": 3.1,
                "dur_alpha": 0.85,
                "dur_disturb": 0.12
            }
        }
        
        self.scene_tts_rules = {
            "紧张激烈": {
                "pWeight": 1.7,
                "dur_alpha": 0.9,
                "dur_disturb": 0.1
            },
            "安静祥和": {
                "pWeight": 1.3,
                "dur_alpha": 1.1,
                "dur_disturb": 0.05
            },
            "神秘诡异": {
                "pWeight": 1.5,
                "dur_alpha": 0.95,
                "dur_disturb": 0.08
            }
        }
        
        # 导入音频分镜卡生成器
        try:
            from app.services.audio_storyboard_generator import AudioStoryboardGenerator
            self.storyboard_generator = AudioStoryboardGenerator()
            logger.info("音频分镜卡生成器初始化成功")
        except ImportError as e:
            logger.warning(f"音频分镜卡生成器导入失败: {e}")
            self.storyboard_generator = None
    
    def generate_paragraph_script(self, 
                                 paragraph_text: str, 
                                 six_card_analysis: Dict[str, Any],
                                 paragraph_id: str) -> Dict[str, Any]:
        """
        基于6卡分析生成段落剧本
        
        Args:
            paragraph_text: 原始段落文本
            six_card_analysis: 6卡分析结果
            paragraph_id: 段落ID
            
        Returns:
            包含synthesis_json和audio_storyboard_card的完整段落数据
        """
        try:
            logger.info(f"开始生成段落 {paragraph_id} 的剧本")
            
            # 1. 生成synthesis_json（段落剧本核心）
            synthesis_json = self._generate_synthesis_json(
                paragraph_text, six_card_analysis, paragraph_id
            )
            
            # 2. 生成音频分镜卡
            audio_storyboard_card = {}
            if self.storyboard_generator:
                try:
                    # 构建段落剧本数据
                    paragraph_script_data = {
                        "synthesis_json": synthesis_json,
                        "story_card": six_card_analysis.get("story_card", {}),
                        "character_card": six_card_analysis.get("character_card", {}),
                        "scene_card": six_card_analysis.get("scene_card", {}),
                        "event_card": six_card_analysis.get("event_card", {}),
                        "emotion_card": six_card_analysis.get("emotion_card", {}),
                        "audio_script_card": six_card_analysis.get("audio_script_card", {})
                    }
                    
                    # 生成音频分镜卡
                    audio_storyboard_card = self.storyboard_generator.generate_paragraph_storyboard(
                        paragraph_script_data, paragraph_id
                    )
                    
                    logger.info(f"段落 {paragraph_id} 音频分镜卡生成成功")
                except Exception as e:
                    logger.error(f"生成段落 {paragraph_id} 音频分镜卡失败: {str(e)}")
                    audio_storyboard_card = self._create_fallback_audio_storyboard(paragraph_id)
            else:
                logger.warning("音频分镜卡生成器未初始化，使用fallback")
                audio_storyboard_card = self._create_fallback_audio_storyboard(paragraph_id)
            
            # 3. 构建完整的段落数据结构
            paragraph_data = {
                "paragraph_id": paragraph_id,
                "synthesis_json": synthesis_json,
                "story_card": six_card_analysis.get("story_card", {}),
                "character_card": six_card_analysis.get("character_card", {}),
                "scene_card": six_card_analysis.get("scene_card", {}),
                "event_card": six_card_analysis.get("event_card", {}),
                "emotion_card": six_card_analysis.get("emotion_card", {}),
                "audio_script_card": six_card_analysis.get("audio_script_card", {}),
                "audio_storyboard_card": audio_storyboard_card
            }
            
            logger.info(f"段落 {paragraph_id} 剧本生成完成")
            return paragraph_data
            
        except Exception as e:
            logger.error(f"生成段落 {paragraph_id} 剧本失败: {str(e)}")
            # 返回基础结构，确保系统可用
            return self._create_fallback_paragraph_data(paragraph_text, paragraph_id)
    
    def _generate_synthesis_json(self, 
                                paragraph_text: str, 
                                six_card_analysis: Dict[str, Any],
                                paragraph_id: str) -> Dict[str, Any]:
        """生成synthesis_json，与智能准备格式完全兼容"""
        
        # 1. 从6卡分析中提取角色信息
        characters = self._extract_characters_from_analysis(six_card_analysis)
        
        # 2. 生成synthesis_plan
        synthesis_plan = self._generate_synthesis_plan(
            paragraph_text, six_card_analysis, characters
        )
        
        # 3. 构建synthesis_json
        synthesis_json = {
            "project_info": {
                "novel_type": "智能检测",
                "total_segments": len(synthesis_plan),
                "ai_model": "paragraph-6card-analysis",
                "paragraph_id": paragraph_id,
                "analysis_time": datetime.now().isoformat()
            },
            "synthesis_plan": synthesis_plan,
            "characters": characters
        }
        
        return synthesis_json
    
    def _extract_characters_from_analysis(self, six_card_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """从6卡分析中提取角色信息"""
        characters = []
        
        # 从角色卡提取
        character_card = six_card_analysis.get("character_card", {})
        characters_involved = character_card.get("characters", [])
        
        for char in characters_involved:
            char_name = char.get("name", "")
            if char_name and char_name not in [c.get("name") for c in characters]:
                # 从角色分析中获取情感状态，如果没有则从情感卡中推断
                char_emotions = char.get("emotions", [])
                if char_emotions:
                    # 使用角色的第一个情感状态
                    current_emotion = char_emotions[0]
                else:
                    # 从情感卡中推断角色情感
                    current_emotion = self._infer_character_emotion(char_name, six_card_analysis)
                
                characters.append({
                    "name": char_name,
                    "character_id": f"char_{len(characters) + 1}",  # 临时ID，后续需要映射到角色配音库
                    "voice_name": "未分配",  # 需要用户手动分配
                    "role_type": char.get("role_type", "一般配角"),
                    "personality": char.get("personality", ""),
                    "current_emotion": current_emotion
                })
        
        # 确保旁白角色存在
        if not any(c.get("name") == "旁白" for c in characters):
            characters.append({
                "name": "旁白",
                "character_id": "narrator_001",
                "voice_name": "旁白语音",
                "role_type": "旁白",
                "personality": "叙述者",
                "current_emotion": "平静"
            })
        
        return characters
    
    def _infer_character_emotion(self, character_name: str, six_card_analysis: Dict[str, Any]) -> str:
        """从情感卡中推断角色的情感状态"""
        emotion_card = six_card_analysis.get("emotion_card", {})
        primary_emotion = emotion_card.get("primary_emotion", "平静")
        
        # 根据角色类型和主要情感推断
        if character_name == "旁白":
            return primary_emotion
        elif "主角" in character_name or "林薇" in character_name:
            # 主角通常反映主要情感
            return primary_emotion
        else:
            # 其他角色根据情感变化推断
            emotion_changes = emotion_card.get("emotion_changes", [])
            if emotion_changes:
                return emotion_changes[0].get("to", "平静")
            return "平静"
    
    def _generate_synthesis_plan(self, 
                                paragraph_text: str, 
                                six_card_analysis: Dict[str, Any],
                                characters: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """生成synthesis_plan，包含对话和旁白"""
        
        synthesis_plan = []
        current_time = 0
        
        # 1. 处理对话内容
        character_card = six_card_analysis.get("character_card", {})
        characters_involved = character_card.get("characters", [])
        
        for char in characters_involved:
            char_name = char.get("name", "")
            dialogues = char.get("dialogue", [])
            
            for i, dialogue in enumerate(dialogues):
                if dialogue and dialogue.strip():
                    # 验证对话内容是否为具体文本（不是描述性总结）
                    if self._is_valid_dialogue_text(dialogue):
                        # 计算时长
                        word_count = len(dialogue.strip())
                        duration_seconds = self._calculate_duration(word_count, char.get("current_emotion", "平静"))
                        
                        # 生成TTS参数
                        tts_params = self._generate_tts_params(char, six_card_analysis)
                        
                        synthesis_plan.append({
                            "segment_id": len(synthesis_plan) + 1,
                            "text": dialogue.strip(),
                            "speaker": char_name,
                            "character_id": next((c.get("character_id") for c in characters if c.get("name") == char_name), "unknown"),
                            "voice_name": next((c.get("voice_name") for c in characters if c.get("name") == char_name), "未分配"),
                            "parameters": tts_params,
                            "emotion": char.get("current_emotion", "平静"),
                            "start_time": current_time,
                            "end_time": current_time + duration_seconds,
                            "word_count": word_count,
                            "duration_seconds": duration_seconds
                        })
                        
                        current_time += duration_seconds
        
        # 2. 处理旁白内容
        narrator_content = character_card.get("narrator", {}).get("content", "")
        
        # 验证旁白内容是否为具体文本
        if narrator_content and narrator_content.strip() and self._is_valid_narrator_text(narrator_content):
            word_count = len(narrator_content.strip())
            duration_seconds = self._calculate_duration(word_count, "平静")
            
            # 旁白使用标准TTS参数
            narrator_params = self.character_tts_rules["旁白"].copy()
            
            synthesis_plan.append({
                "segment_id": len(synthesis_plan) + 1,
                "text": narrator_content.strip(),
                "speaker": "旁白",
                "character_id": "narrator_001",
                "voice_name": "旁白语音",
                "parameters": narrator_params,
                "start_time": current_time,
                "end_time": current_time + duration_seconds,
                "word_count": word_count,
                "duration_seconds": duration_seconds
            })
        
        # 3. 如果没有有效的对话和旁白，将整个段落作为旁白
        if not synthesis_plan:
            word_count = len(paragraph_text.strip())
            duration_seconds = self._calculate_duration(word_count, "平静")
            
            narrator_params = self.character_tts_rules["旁白"].copy()
            
            synthesis_plan.append({
                "segment_id": 1,
                "text": paragraph_text.strip(),
                "speaker": "旁白",
                "character_id": "narrator_001",
                "voice_name": "旁白语音",
                "parameters": narrator_params,
                "start_time": 0,
                "end_time": duration_seconds,
                "word_count": word_count,
                "duration_seconds": duration_seconds
            })
        
        return synthesis_plan
    
    def _is_valid_dialogue_text(self, text: str) -> bool:
        """验证对话文本是否为有效的具体内容"""
        if not text or len(text.strip()) < 3:
            return False
        
        # 检查是否为描述性总结（通常包含这些关键词）
        descriptive_keywords = [
            "具体对话内容", "对话内容", "角色对话", "对话", "说话",
            "描述", "总结", "概括", "分析", "说明"
        ]
        
        text_lower = text.lower()
        for keyword in descriptive_keywords:
            if keyword in text_lower:
                return False
        
        # 检查是否包含引号（真正的对话通常有引号）
        if '"' in text or '"' in text or '"' in text or '"' in text:
            return True
        
        # 检查是否为完整的句子（至少包含主语和谓语）
        if len(text.strip()) > 10 and any(char in text for char in '。！？，'):
            return True
        
        return True
    
    def _is_valid_narrator_text(self, text: str) -> bool:
        """验证旁白文本是否为有效的具体内容"""
        if not text or len(text.strip()) < 10:
            return False
        
        # 检查是否为描述性总结
        descriptive_keywords = [
            "旁白叙述内容", "叙述内容", "旁白内容", "林薇的心理活动及环境描写",
            "描述", "总结", "概括", "分析", "说明", "心理活动", "环境描写"
        ]
        
        text_lower = text.lower()
        for keyword in descriptive_keywords:
            if keyword in text_lower:
                return False
        
        # 检查是否为具体的叙述文本（通常较长且包含具体描述）
        if len(text.strip()) > 20:
            return True
        
        return False
    
    def _extract_dialogues_from_text(self, text: str) -> List[str]:
        """从原文中提取对话内容"""
        dialogues = []
        
        # 简单的对话提取逻辑（基于引号）
        import re
        
        # 匹配中文引号内的内容
        dialogue_pattern = r'["""]([^"""]*)["""]'
        matches = re.findall(dialogue_pattern, text)
        
        for match in matches:
            if match.strip():
                dialogues.append(match.strip())
        
        # 如果没有找到引号对话，尝试其他模式
        if not dialogues:
            # 检查是否包含"说"、"道"等关键词
            if "说" in text or "道" in text or "喊" in text or "叫" in text:
                # 简单分割，取包含这些关键词的句子
                sentences = re.split(r'[。！？]', text)
                for sentence in sentences:
                    if any(keyword in sentence for keyword in ["说", "道", "喊", "叫"]):
                        dialogues.append(sentence.strip())
        
        return dialogues
    
    def _generate_tts_params(self, character: Dict[str, Any], six_card_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """基于6卡分析生成TTS参数"""
        
        # 基础参数
        base_params = {
            "timeStep": 32,
            "pWeight": 1.4,
            "tWeight": 3.0,
            "dur_alpha": 1.0,
            "dur_disturb": 0.1
        }
        
        # 1. 角色权重计算
        role_type = character.get("role_type", "一般配角")
        if role_type in self.character_tts_rules:
            char_rules = self.character_tts_rules[role_type]
            base_params["timeStep"] = char_rules["timeStep"]
            base_params["pWeight"] = char_rules["pWeight"]
            base_params["tWeight"] = char_rules["tWeight"]
            base_params["dur_alpha"] = char_rules["dur_alpha"]
            base_params["dur_disturb"] = char_rules["dur_disturb"]
        
        # 2. 情绪权重计算
        emotion = character.get("current_emotion", "平静")
        if emotion in self.emotion_tts_rules:
            emotion_rules = self.emotion_tts_rules[emotion]
            base_params["dur_alpha"] *= emotion_rules["dur_alpha"]
            base_params["pWeight"] = emotion_rules["pWeight"]
            base_params["dur_disturb"] = emotion_rules["dur_disturb"]
        
        # 3. 事件权重计算
        event_card = six_card_analysis.get("event_card", {})
        event_significance = event_card.get("significance", "日常对话")
        if event_significance in self.event_tts_rules:
            event_rules = self.event_tts_rules[event_significance]
            base_params["timeStep"] = event_rules["timeStep"]
            base_params["pWeight"] = event_rules["pWeight"]
            base_params["tWeight"] = event_rules["tWeight"]
            base_params["dur_alpha"] *= event_rules["dur_alpha"]
            base_params["dur_disturb"] = event_rules["dur_disturb"]
        
        # 4. 场景权重计算
        scene_card = six_card_analysis.get("scene_card", {})
        atmosphere = scene_card.get("atmosphere", "")
        if "紧张" in atmosphere or "激烈" in atmosphere:
            scene_rules = self.scene_tts_rules["紧张激烈"]
            base_params["pWeight"] = scene_rules["pWeight"]
            base_params["dur_alpha"] *= scene_rules["dur_alpha"]
            base_params["dur_disturb"] = scene_rules["dur_disturb"]
        elif "安静" in atmosphere or "祥和" in atmosphere:
            scene_rules = self.scene_tts_rules["安静祥和"]
            base_params["pWeight"] = scene_rules["pWeight"]
            base_params["dur_alpha"] *= scene_rules["dur_alpha"]
            base_params["dur_disturb"] = scene_rules["dur_disturb"]
        
        # 5. 参数范围限制
        base_params["timeStep"] = max(20, min(50, base_params["timeStep"]))
        base_params["pWeight"] = max(1.0, min(2.0, base_params["pWeight"]))
        base_params["tWeight"] = max(2.0, min(4.0, base_params["tWeight"]))
        base_params["dur_alpha"] = max(0.5, min(2.0, base_params["dur_alpha"]))
        base_params["dur_disturb"] = max(0.0, min(0.3, base_params["dur_disturb"]))
        
        return base_params
    
    def _calculate_duration(self, word_count: int, emotion: str) -> float:
        """基于字数和情绪计算时长"""
        
        # 基础语速（字/分钟）- 优化为有声读物标准
        base_speed = 300  # 旁白 - 更符合有声读物标准
        if emotion != "平静":
            base_speed = 280  # 角色对话 - 稍慢于旁白
        
        # 情绪调整系数
        emotion_speed_multiplier = {
            "紧张": 1.1,    # 语速加快10%
            "悲伤": 0.85,   # 语速放慢15%
            "兴奋": 1.05,   # 语速稍快5%
            "愤怒": 1.2,    # 语速快20%
            "平静": 1.0     # 正常语速
        }
        
        speed_multiplier = emotion_speed_multiplier.get(emotion, 1.0)
        adjusted_speed = base_speed * speed_multiplier
        
        # 计算时长（秒）
        duration_minutes = word_count / adjusted_speed
        duration_seconds = duration_minutes * 60
        
        return round(duration_seconds, 2)
    
    def _create_fallback_audio_storyboard(self, paragraph_id: str) -> Dict[str, Any]:
        """创建基础的音频分镜卡（fallback）"""
        
        return {
            "storyboard_id": f"storyboard_{paragraph_id}_fallback",
            "paragraph_id": paragraph_id,
            "generation_time": datetime.now().isoformat(),
            "total_duration": 0,
            "timeline": {
                "paragraph_id": paragraph_id,
                "segments": [],
                "total_duration": 0,
                "time_units": "seconds"
            },
            "audio_tracks": {
                "main_track": {
                    "name": "主音轨",
                    "description": "旁白叙述和角色对话",
                    "priority": 1,
                    "volume": 100,
                    "effects": ["降噪", "均衡器"],
                    "segments": []
                },
                "background_music": {
                    "name": "背景音乐",
                    "description": "场景氛围音乐",
                    "priority": 2,
                    "volume": 30,
                    "effects": ["淡入淡出", "音量控制"],
                    "segments": []
                },
                "environment_sound": {
                    "name": "环境音效",
                    "description": "场景环境声音",
                    "priority": 3,
                    "volume": 40,
                    "effects": ["空间化", "混响"],
                    "segments": []
                }
            },
            "voice_assignments": {
                "characters": [],
                "narrator": {},
                "voice_effects": {}
            },
            "sound_effects": [],
            "background_music": {
                "type": "轻快日常音乐",
                "mood": "轻松愉快",
                "tempo": "中快节奏",
                "instruments": ["吉他", "口琴", "手风琴"],
                "volume": 20,
                "fade_in": 1.5,
                "fade_out": 2.0,
                "loop": True,
                "crossfade": True
            },
            "mixing_parameters": {
                "main_volume": 100,
                "background_volume": 30,
                "environment_volume": 40,
                "master_volume": 90
            },
            "scene_sequence": [],
            "audio_config": {
                "sample_rate": 44100,
                "bit_depth": 24,
                "channels": 2,
                "format": "WAV",
                "quality": "高"
            }
        }
    
    def _create_fallback_paragraph_data(self, paragraph_text: str, paragraph_id: str) -> Dict[str, Any]:
        """创建基础的段落数据结构（fallback）"""
        
        # 尝试从原文中提取对话内容
        dialogue_segments = self._extract_dialogues_from_text(paragraph_text)
        
        synthesis_plan = []
        current_time = 0
        
        # 添加对话内容
        for i, dialogue in enumerate(dialogue_segments):
            if dialogue and dialogue.strip():
                dialogue_duration = self._calculate_duration(len(dialogue.strip()), "平静")
                synthesis_plan.append({
                    "segment_id": i + 1,
                    "text": dialogue.strip(),
                    "speaker": "角色" + str(i + 1),
                    "character_id": f"char_{i + 1}",
                    "voice_name": "未分配",
                    "parameters": {
                        "timeStep": 32,
                        "pWeight": 1.4,
                        "tWeight": 3.0,
                        "dur_alpha": 1.0,
                        "dur_disturb": 0.1
                    },
                    "start_time": current_time,
                    "end_time": current_time + dialogue_duration,
                    "word_count": len(dialogue.strip()),
                    "duration_seconds": dialogue_duration
                })
                current_time += dialogue_duration
        
        # 如果没有对话，将整个段落作为旁白
        if not synthesis_plan:
            word_count = len(paragraph_text.strip())
            duration_seconds = self._calculate_duration(word_count, "平静")
            
            synthesis_plan.append({
                "segment_id": 1,
                "text": paragraph_text.strip(),
                "speaker": "旁白",
                "character_id": "narrator_001",
                "voice_name": "旁白语音",
                "parameters": self.character_tts_rules["旁白"].copy(),
                "start_time": 0,
                "end_time": duration_seconds,
                "word_count": word_count,
                "duration_seconds": duration_seconds
            })
        
        # 构建完整的fallback数据
        fallback_synthesis_json = {
            "project_info": {
                "novel_type": "智能检测",
                "total_segments": len(synthesis_plan),
                "ai_model": "paragraph-6card-analysis-fallback",
                "paragraph_id": paragraph_id,
                "analysis_time": datetime.now().isoformat()
            },
            "synthesis_plan": synthesis_plan,
            "characters": [
                {
                    "name": "旁白",
                    "character_id": "narrator_001",
                    "voice_name": "旁白语音",
                    "role_type": "旁白",
                    "personality": "叙述者",
                    "current_emotion": "平静"
                }
            ]
        }
        
        return {
            "paragraph_id": paragraph_id,
            "synthesis_json": fallback_synthesis_json,
            "story_card": {},
            "character_card": {},
            "scene_card": {},
            "event_card": {},
            "emotion_card": {},
            "audio_script_card": {},
            "audio_storyboard_card": self._create_fallback_audio_storyboard(paragraph_id)
        }
