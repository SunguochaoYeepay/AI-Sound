"""
音频分镜卡生成器服务
基于段落剧本生成完整的音频分镜卡JSON
专注段落级音频配置，确保输出JSON符合设计规范
"""

import logging
import json
from typing import Dict, List, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class AudioStoryboardGenerator:
    """音频分镜卡生成器 - 基于段落剧本生成音频分镜卡"""
    
    def __init__(self):
        # 音轨配置规则
        self.track_configs = {
            "main_track": {  # 旁白+对话音轨
                "name": "主音轨",
                "description": "旁白叙述和角色对话",
                "priority": 1,
                "volume": 100,
                "effects": ["降噪", "均衡器"]
            },
            "background_music": {  # 背景音乐音轨
                "name": "背景音乐",
                "description": "场景氛围音乐",
                "priority": 2,
                "volume": 30,
                "effects": ["淡入淡出", "音量控制"]
            },
            "environment_sound": {  # 环境音效音轨
                "name": "环境音效",
                "description": "场景环境声音",
                "priority": 3,
                "volume": 40,
                "effects": ["空间化", "混响"]
            }
        }
        
        # 场景音乐映射规则
        self.scene_music_rules = {
            "紧张激烈": {
                "type": "紧张战斗音乐",
                "mood": "紧张激烈",
                "tempo": "快节奏",
                "instruments": ["鼓", "弦乐", "铜管"],
                "volume": 35,
                "fade_in": 2.0,
                "fade_out": 3.0
            },
            "安静祥和": {
                "type": "轻柔背景音乐",
                "mood": "安静祥和",
                "tempo": "慢节奏",
                "instruments": ["钢琴", "长笛", "竖琴"],
                "volume": 25,
                "fade_in": 3.0,
                "fade_out": 4.0
            },
            "神秘诡异": {
                "type": "神秘氛围音乐",
                "mood": "神秘诡异",
                "tempo": "中节奏",
                "instruments": ["电子音效", "弦乐", "打击乐"],
                "volume": 30,
                "fade_in": 2.5,
                "fade_out": 3.5
            },
            "日常对话": {
                "type": "轻快日常音乐",
                "mood": "轻松愉快",
                "tempo": "中快节奏",
                "instruments": ["吉他", "口琴", "手风琴"],
                "volume": 20,
                "fade_in": 1.5,
                "fade_out": 2.0
            }
        }
        
        # 环境音效映射规则
        self.environment_sound_rules = {
            "古战场": {
                "sounds": ["刀剑碰撞声", "风声", "脚步声", "马蹄声"],
                "volume": 45,
                "spatial": "环绕立体声",
                "reverb": "开阔空间"
            },
            "古代街道": {
                "sounds": ["马蹄声", "叫卖声", "脚步声", "市井嘈杂声", "钟声"],
                "volume": 40,
                "spatial": "古代市集",
                "reverb": "街道混响"
            },
            "古代室内": {
                "sounds": ["脚步声", "门开关声", "家具移动声", "烛火声"],
                "volume": 35,
                "spatial": "近距离",
                "reverb": "古代建筑混响"
            },
            "古代自然": {
                "sounds": ["鸟叫声", "风声", "水流声", "树叶声", "虫鸣声"],
                "volume": 40,
                "spatial": "自然环绕",
                "reverb": "自然空间"
            },
            "室内场景": {
                "sounds": ["脚步声", "门开关声", "家具移动声"],
                "volume": 35,
                "spatial": "近距离",
                "reverb": "室内混响"
            },
            "自然场景": {
                "sounds": ["鸟叫声", "风声", "水流声", "树叶声"],
                "volume": 40,
                "spatial": "自然环绕",
                "reverb": "自然空间"
            },
            "城市场景": {
                "sounds": ["车流声", "人声", "建筑声", "交通声"],
                "volume": 50,
                "spatial": "城市立体声",
                "reverb": "城市混响"
            }
        }
    
    def generate_paragraph_storyboard(self, 
                                    paragraph_script: Dict[str, Any],
                                    paragraph_id: str) -> Dict[str, Any]:
        """
        基于段落剧本生成音频分镜卡
        
        Args:
            paragraph_script: 段落剧本数据（包含synthesis_json和6卡分析）
            paragraph_id: 段落ID
            
        Returns:
            完整的音频分镜卡JSON
        """
        try:
            logger.info(f"开始生成段落 {paragraph_id} 的音频分镜卡")
            
            # 1. 提取基础信息
            synthesis_json = paragraph_script.get("synthesis_json", {})
            scene_card = paragraph_script.get("scene_card", {})
            event_card = paragraph_script.get("event_card", {})
            emotion_card = paragraph_script.get("emotion_card", {})
            
            # 2. 生成时间轴
            timeline = self._generate_timeline(synthesis_json, paragraph_id)
            
            # 3. 生成音轨配置
            audio_tracks = self._generate_audio_tracks(synthesis_json, scene_card, paragraph_script)
            
            # 4. 生成角色语音配置
            voice_assignments = self._generate_voice_assignments(synthesis_json)
            
            # 5. 生成音效配置
            sound_effects = self._generate_sound_effects(scene_card, event_card, timeline["total_duration"])
            
            # 6. 生成背景音乐配置
            background_music = self._generate_background_music(scene_card, emotion_card)
            
            # 7. 生成混音参数
            mixing_parameters = self._generate_mixing_parameters(
                synthesis_json, scene_card, emotion_card
            )
            
            # 8. 构建完整的音频分镜卡
            audio_storyboard = {
                "storyboard_id": f"storyboard_{paragraph_id}",
                "paragraph_id": paragraph_id,
                "generation_time": datetime.now().isoformat(),
                "total_duration": timeline.get("total_duration", 0),
                "timeline": timeline,
                "audio_tracks": audio_tracks,
                "voice_assignments": voice_assignments,
                "sound_effects": sound_effects,
                "background_music": background_music,
                "mixing_parameters": mixing_parameters,
                "scene_sequence": self._generate_scene_sequence(scene_card, event_card, timeline["total_duration"]),
                "audio_config": self._generate_audio_config(synthesis_json, scene_card)
            }
            
            logger.info(f"段落 {paragraph_id} 音频分镜卡生成完成")
            return audio_storyboard
            
        except Exception as e:
            logger.error(f"生成段落 {paragraph_id} 音频分镜卡失败: {str(e)}")
            # 返回基础结构，确保系统可用
            return self._create_fallback_storyboard(paragraph_id)
    
    def _generate_timeline(self, synthesis_json: Dict[str, Any], paragraph_id: str) -> Dict[str, Any]:
        """生成时间轴配置"""
        
        synthesis_plan = synthesis_json.get("synthesis_plan", [])
        timeline = {
            "paragraph_id": paragraph_id,
            "segments": [],
            "total_duration": 0,
            "time_units": "seconds"
        }
        
        current_time = 0
        for segment in synthesis_plan:
            segment_timeline = {
                "segment_id": segment.get("segment_id", 0),
                "character_id": segment.get("character_id", ""),
                "paragraph_id": paragraph_id,
                "start_time": segment.get("start_time", current_time),
                "end_time": segment.get("end_time", current_time),
                "duration": segment.get("duration_seconds", 0),
                "word_count": segment.get("word_count", 0),
                "speaker": segment.get("speaker", ""),
                "emotion": segment.get("emotion", "平静"),
                "audio_type": "voice" if segment.get("speaker") != "旁白" else "narration"
            }
            
            timeline["segments"].append(segment_timeline)
            current_time = segment.get("end_time", current_time)
        
        timeline["total_duration"] = current_time
        return timeline
    
    def _generate_audio_tracks(self, synthesis_json: Dict[str, Any], scene_card: Dict[str, Any], paragraph_script_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """生成音轨配置"""
        
        audio_tracks = {}
        
        # 主音轨（旁白+对话）
        main_track = self.track_configs["main_track"].copy()
        main_track["segments"] = []
        
        synthesis_plan = synthesis_json.get("synthesis_plan", [])
        for segment in synthesis_plan:
            main_track["segments"].append({
                "segment_id": segment.get("segment_id", 0),
                "start_time": segment.get("start_time", 0),
                "end_time": segment.get("end_time", 0),
                "speaker": segment.get("speaker", ""),
                "character_id": segment.get("character_id", ""),
                "volume": 100,
                "pan": 0,  # 居中
                "effects": main_track.get("effects", ["降噪", "均衡器"])
            })
        
        audio_tracks["main_track"] = main_track
        
        # 背景音乐音轨
        background_track = self.track_configs["background_music"].copy()
        background_track["segments"] = []
        
        # 根据场景确定背景音乐 - 使用统一的音乐配置逻辑
        atmosphere = scene_card.get("atmosphere", "日常对话")
        emotion_card = paragraph_script_data.get("emotion_card", {}) if paragraph_script_data else {}
        music_config = self._generate_background_music(scene_card, emotion_card)
        
        # 计算总时长
        synthesis_plan = synthesis_json.get("synthesis_plan", [])
        total_duration = 0
        if synthesis_plan:
            total_duration = synthesis_plan[-1].get("end_time", 0)
        
        background_track["segments"].append({
            "segment_id": "bg_music_001",
            "start_time": 0,
            "end_time": total_duration,  # 修复：使用正确的总时长
            "music_type": music_config["type"],
            "mood": music_config["mood"],
            "volume": music_config["volume"],
            "fade_in": music_config["fade_in"],
            "fade_out": music_config["fade_out"],
            "effects": background_track.get("effects", ["淡入淡出", "音量控制"])
        })
        
        audio_tracks["background_music"] = background_track
        
        # 环境音效音轨
        environment_track = self.track_configs["environment_sound"].copy()
        environment_track["segments"] = []
        
        # 根据场景确定环境音效
        location = scene_card.get("location", "未知场景")
        env_config = self._get_environment_config(location)
        
        if env_config:
            environment_track["segments"].append({
                "segment_id": "env_sound_001",
                "start_time": 0,
                "end_time": total_duration,  # 修复：使用正确的总时长
                "sound_type": "环境音效",
                "sounds": env_config["sounds"],
                "volume": env_config["volume"],
                "spatial": env_config["spatial"],
                "reverb": env_config["reverb"],
                "effects": environment_track.get("effects", ["空间化", "混响"])
            })
        
        audio_tracks["environment_sound"] = environment_track
        
        return audio_tracks
    
    def _generate_voice_assignments(self, synthesis_json: Dict[str, Any]) -> Dict[str, Any]:
        """生成角色语音配置"""
        
        voice_assignments = {
            "characters": [],
            "narrator": {},
            "voice_effects": {}
        }
        
        characters = synthesis_json.get("characters", [])
        for char in characters:
            char_config = {
                "character_id": char.get("character_id", ""),
                "name": char.get("name", ""),
                "voice_name": char.get("voice_name", "未分配"),
                "role_type": char.get("role_type", "一般配角"),
                "voice_characteristics": {
                    "pitch": "标准",
                    "speed": "标准",
                    "emotion": char.get("current_emotion", "平静"),
                    "clarity": "高" if char.get("role_type") in ["主角", "重要配角"] else "中"
                },
                "tts_parameters": {
                    "timeStep": 32,
                    "pWeight": 1.4,
                    "tWeight": 3.0,
                    "dur_alpha": 1.0,
                    "dur_disturb": 0.1
                }
            }
            
            # 根据角色类型调整TTS参数
            if char.get("role_type") == "主角":
                char_config["tts_parameters"]["timeStep"] = 35
                char_config["tts_parameters"]["pWeight"] = 1.6
                char_config["tts_parameters"]["tWeight"] = 3.2
            elif char.get("role_type") == "重要配角":
                char_config["tts_parameters"]["timeStep"] = 32
                char_config["tts_parameters"]["pWeight"] = 1.5
                char_config["tts_parameters"]["tWeight"] = 3.0
            
            voice_assignments["characters"].append(char_config)
        
        # 旁白配置
        narrator = next((c for c in characters if c.get("name") == "旁白"), None)
        if narrator:
            voice_assignments["narrator"] = {
                "character_id": narrator.get("character_id", ""),
                "voice_name": narrator.get("voice_name", "旁白语音"),
                "voice_characteristics": {
                    "pitch": "标准",
                    "speed": "标准",
                    "emotion": "平静",
                    "clarity": "高"
                },
                "tts_parameters": {
                    "timeStep": 30,
                    "pWeight": 1.3,
                    "tWeight": 2.8,
                    "dur_alpha": 1.0,
                    "dur_disturb": 0.05
                }
            }
        
        return voice_assignments
    
    def _generate_sound_effects(self, scene_card: Dict[str, Any], event_card: Dict[str, Any], total_duration: float = 0) -> List[Dict[str, Any]]:
        """生成音效配置"""
        
        sound_effects = []
        
        # 从场景卡提取环境音效
        environment_sounds = scene_card.get("environment_sounds", [])
        for i, sound in enumerate(environment_sounds):
            sound_effects.append({
                "effect_id": f"env_effect_{i+1:03d}",
                "type": "环境音效",
                "description": sound,
                "start_time": 0,
                "end_time": total_duration if total_duration > 0 else 30,  # 与主音轨同步
                "volume": 40,
                "spatial": "环绕",
                "effects": ["空间化", "混响"]
            })
        
        # 从事件卡提取动作音效
        if event_card.get("significance") == "战斗场景":
            battle_sounds = ["刀剑声", "脚步声", "撞击声", "喊叫声"]
            for i, sound in enumerate(battle_sounds):
                sound_effects.append({
                    "effect_id": f"battle_effect_{i+1:03d}",
                    "type": "动作音效",
                    "description": sound,
                    "start_time": 0,
                    "end_time": total_duration if total_duration > 0 else 30,  # 与主音轨同步
                    "volume": 50,
                    "spatial": "立体声",
                    "effects": ["动态音量", "空间化"]
                })
        
        return sound_effects
    
    def _generate_background_music(self, scene_card: Dict[str, Any], emotion_card: Dict[str, Any]) -> Dict[str, Any]:
        """生成背景音乐配置"""
        
        atmosphere = scene_card.get("atmosphere", "日常对话")
        primary_emotion = emotion_card.get("primary_emotion", "平静")
        
        # 根据场景和情绪选择音乐
        if "紧张" in atmosphere or "激烈" in atmosphere:
            music_config = self.scene_music_rules["紧张激烈"]
        elif "安静" in atmosphere or "祥和" in atmosphere:
            music_config = self.scene_music_rules["安静祥和"]
        elif "神秘" in atmosphere or "诡异" in atmosphere:
            music_config = self.scene_music_rules["神秘诡异"]
        else:
            music_config = self.scene_music_rules["日常对话"]
        
        # 根据情绪调整音乐参数
        if primary_emotion in ["愤怒", "紧张"]:
            music_config["volume"] = min(40, music_config["volume"] + 5)
            music_config["tempo"] = "快节奏"
        elif primary_emotion in ["悲伤", "平静"]:
            music_config["volume"] = max(20, music_config["volume"] - 5)
            music_config["tempo"] = "慢节奏"
        
        return {
            "type": music_config["type"],
            "mood": music_config["mood"],
            "tempo": music_config["tempo"],
            "instruments": music_config["instruments"],
            "volume": music_config["volume"],
            "fade_in": music_config["fade_in"],
            "fade_out": music_config["fade_out"],
            "loop": True,
            "crossfade": True
        }
    
    def _generate_mixing_parameters(self, synthesis_json: Dict[str, Any], 
                                  scene_card: Dict[str, Any], 
                                  emotion_card: Dict[str, Any]) -> Dict[str, Any]:
        """生成混音参数"""
        
        # 基础混音参数
        mixing_params = {
            "main_volume": 100,
            "background_volume": 30,
            "environment_volume": 40,
            "master_volume": 90,
            "compression": {
                "threshold": -20,
                "ratio": 4,
                "attack": 5,
                "release": 50
            },
            "equalizer": {
                "low": 0,
                "mid": 0,
                "high": 0
            },
            "reverb": {
                "wet": 15,
                "dry": 85,
                "decay": 1.5,
                "pre_delay": 20
            }
        }
        
        # 根据场景调整混音参数
        atmosphere = scene_card.get("atmosphere", "")
        if "紧张" in atmosphere or "激烈" in atmosphere:
            mixing_params["background_volume"] = 35
            mixing_params["environment_volume"] = 45
            mixing_params["compression"]["threshold"] = -25
            mixing_params["compression"]["ratio"] = 6
        elif "安静" in atmosphere or "祥和" in atmosphere:
            mixing_params["background_volume"] = 25
            mixing_params["environment_volume"] = 35
            mixing_params["reverb"]["wet"] = 20
            mixing_params["reverb"]["decay"] = 2.0
        
        # 根据情绪调整混音参数
        emotional_intensity = emotion_card.get("emotional_intensity", 5)
        if emotional_intensity > 7:
            mixing_params["main_volume"] = 100  # 修复：避免音频失真
            mixing_params["compression"]["threshold"] = -30
        elif emotional_intensity < 3:
            mixing_params["main_volume"] = 95
            mixing_params["reverb"]["wet"] = 25
        
        return mixing_params
    
    def _generate_scene_sequence(self, scene_card: Dict[str, Any], event_card: Dict[str, Any], total_duration: float) -> List[Dict[str, Any]]:
        """生成场景序列"""
        
        scene_sequence = []
        
        # 场景开始
        scene_sequence.append({
            "sequence_id": "scene_start",
            "type": "场景开始",
            "start_time": 0,
            "end_time": 2.0,
            "description": f"场景：{scene_card.get('location', '未知地点')}",
            "audio_transition": "淡入",
            "visual_elements": scene_card.get("visual_elements", []),
            "atmosphere": scene_card.get("atmosphere", "中性")
        })
        
        # 主要事件
        main_event = event_card.get("main_event", "")
        if main_event:
            scene_sequence.append({
                "sequence_id": "main_event",
                "type": "主要事件",
                "start_time": 2.0,
                "end_time": total_duration - 2.0,  # 修复：使用正确的结束时间
                "description": main_event,
                "audio_transition": "保持",
                "significance": event_card.get("significance", "日常"),
                "emotional_impact": "中等"
            })
        
        # 场景结束
        scene_sequence.append({
            "sequence_id": "scene_end",
            "type": "场景结束",
            "start_time": total_duration - 2.0,  # 修复：使用正确的开始时间
            "end_time": total_duration,  # 修复：使用正确的结束时间
            "description": "场景过渡",
            "audio_transition": "淡出",
            "next_scene": "下一场景"
        })
        
        return scene_sequence
    
    def _generate_audio_config(self, synthesis_json: Dict[str, Any], scene_card: Dict[str, Any]) -> Dict[str, Any]:
        """生成音频配置"""
        
        return {
            "sample_rate": 44100,
            "bit_depth": 24,
            "channels": 2,
            "format": "WAV",
            "quality": "高",
            "compression": "无损",
            "metadata": {
                "title": f"段落音频 - {synthesis_json.get('project_info', {}).get('paragraph_id', '')}",
                "artist": "AI-Sound系统",
                "genre": "有声小说",
                "scene": scene_card.get("location", "未知场景"),
                "atmosphere": scene_card.get("atmosphere", "中性")
            }
        }
    
    def _get_environment_config(self, location: str) -> Optional[Dict[str, Any]]:
        """根据场景获取环境音效配置"""
        
        # 场景类型映射
        scene_mapping = {
            "古战场": "古战场",
            "战场": "古战场",
            "长安": "古代街道",
            "盛唐": "古代街道",
            "古代": "古代街道",
            "市集": "古代街道",
            "街道": "古代街道",
            "古代室内": "古代室内",
            "古代房间": "古代室内",
            "古代自然": "古代自然",
            "古代森林": "古代自然",
            "室内": "室内场景",
            "房间": "室内场景",
            "自然": "自然场景",
            "森林": "自然场景",
            "城市": "城市场景",
            "现代街道": "城市场景"
        }
        
        for keyword, config_key in scene_mapping.items():
            if keyword in location:
                return self.environment_sound_rules.get(config_key)
        
        # 默认返回古代街道配置（适合穿越小说等古代背景）
        return self.environment_sound_rules.get("古代街道")
    
    def _create_fallback_storyboard(self, paragraph_id: str) -> Dict[str, Any]:
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
                "main_track": self.track_configs["main_track"].copy(),
                "background_music": self.track_configs["background_music"].copy(),
                "environment_sound": self.track_configs["environment_sound"].copy()
            },
            "voice_assignments": {
                "characters": [],
                "narrator": {},
                "voice_effects": {}
            },
            "sound_effects": [],
            "background_music": self.scene_music_rules["日常对话"].copy(),
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
