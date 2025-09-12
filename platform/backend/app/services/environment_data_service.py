"""
环境音数据服务
从 generation.py 中提取的数据提取和转换逻辑
"""

import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class EnvironmentDataService:
    """环境音数据服务"""
    
    @staticmethod
    def extract_environment_sounds_from_analysis(
        book_analysis: Dict[str, Any], 
        chapter_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """从书籍分析结果中提取环境音数据"""
        environment_sounds = []
        
        if chapter_id:
            # 单章节模式
            chapter_data = book_analysis.get(str(chapter_id), {})
            
            # 支持6卡分析结果格式
            if 'six_card_results' in chapter_data:
                six_card_results = chapter_data.get('six_card_results', [])
                for six_card_result in six_card_results:
                    scene_card = six_card_result.get('scene_card', {})
                    character_card = six_card_result.get('character_card', {})
                    audio_storyboard_card = six_card_result.get('audio_storyboard_card', {})
                    
                    # 提取旁白内容
                    narrator_content = ""
                    if 'narrator' in character_card:
                        narrator_content = character_card['narrator'].get('content', '')
                    
                    # 优先从 audio_storyboard_card.sound_effects 中提取详细描述
                    sound_effects = audio_storyboard_card.get('sound_effects', [])
                    if sound_effects:
                        # 有详细的环境音描述，使用详细描述
                        for effect in sound_effects:
                            if isinstance(effect, dict):
                                sound_obj = {
                                    'keyword': effect.get('keyword', ''),
                                    'description': effect.get('description', ''),
                                    'chinese_description': effect.get('description', ''),  # 使用详细描述
                                    'chapter_id': chapter_id,
                                    'segment_index': six_card_result.get('_metadata', {}).get('segment_index', 0),
                                    'narration_text': narrator_content
                                }
                                environment_sounds.append(sound_obj)
                    else:
                        # 回退到 scene_card.environment_sounds
                        sounds = scene_card.get('environment_sounds', [])
                        for sound in sounds:
                            if isinstance(sound, str):
                                # 新格式：字符串关键词
                                sound_obj = {
                                    'keyword': sound,
                                    'description': f'{sound}的环境音效',  # 简单描述
                                    'chinese_description': f'{sound}的环境音效',  # 添加中文描述字段
                                    'chapter_id': chapter_id,
                                    'segment_index': six_card_result.get('_metadata', {}).get('segment_index', 0),
                                    'narration_text': narrator_content
                                }
                                environment_sounds.append(sound_obj)
                            elif isinstance(sound, dict):
                                # 兼容旧格式：对象格式
                                sound_copy = sound.copy()
                                sound_copy['chapter_id'] = chapter_id
                                sound_copy['segment_index'] = six_card_result.get('_metadata', {}).get('segment_index', 0)
                                sound_copy['narration_text'] = narrator_content
                                environment_sounds.append(sound_copy)
            else:
                # 兼容旧格式
                scene_card = chapter_data.get('scene_card', {})
                sounds = scene_card.get('environment_sounds', [])
                
                # 为每个环境音添加章节信息
                for sound in sounds:
                    if isinstance(sound, dict):
                        sound_copy = sound.copy()
                        sound_copy['chapter_id'] = chapter_id
                        environment_sounds.append(sound_copy)
                    elif isinstance(sound, str):
                        # 如果是字符串，创建基本的环境音对象
                        sound_obj = {
                            'keyword': sound,
                            'description': sound,
                            'chapter_id': chapter_id
                        }
                        environment_sounds.append(sound_obj)
        else:
            # 多章节模式
            for chapter_id_str, chapter_data in book_analysis.items():
                if isinstance(chapter_data, dict):
                    # 支持6卡分析结果格式
                    if 'six_card_results' in chapter_data:
                        six_card_results = chapter_data.get('six_card_results', [])
                        for six_card_result in six_card_results:
                            scene_card = six_card_result.get('scene_card', {})
                            character_card = six_card_result.get('character_card', {})
                            audio_storyboard_card = six_card_result.get('audio_storyboard_card', {})
                            
                            # 提取旁白内容
                            narrator_content = ""
                            if 'narrator' in character_card:
                                narrator_content = character_card['narrator'].get('content', '')
                            
                            # 优先从 audio_storyboard_card.sound_effects 中提取详细描述
                            sound_effects = audio_storyboard_card.get('sound_effects', [])
                            if sound_effects:
                                # 有详细的环境音描述，使用详细描述
                                for effect in sound_effects:
                                    if isinstance(effect, dict):
                                        sound_obj = {
                                            'keyword': effect.get('keyword', ''),
                                            'description': effect.get('description', ''),
                                            'chinese_description': effect.get('description', ''),  # 使用详细描述
                                            'chapter_id': int(chapter_id_str),
                                            'segment_index': six_card_result.get('_metadata', {}).get('segment_index', 0),
                                            'narration_text': narrator_content
                                        }
                                        environment_sounds.append(sound_obj)
                            else:
                                # 回退到 scene_card.environment_sounds
                                chapter_sounds = scene_card.get('environment_sounds', [])
                                for sound in chapter_sounds:
                                    if isinstance(sound, str):
                                        # 新格式：字符串关键词
                                        sound_obj = {
                                            'keyword': sound,
                                            'description': f'{sound}的环境音效',  # 简单描述
                                            'chinese_description': f'{sound}的环境音效',  # 添加中文描述字段
                                            'chapter_id': int(chapter_id_str),
                                            'segment_index': six_card_result.get('_metadata', {}).get('segment_index', 0),
                                            'narration_text': narrator_content
                                        }
                                        environment_sounds.append(sound_obj)
                                    elif isinstance(sound, dict):
                                        # 兼容旧格式：对象格式
                                        sound_copy = sound.copy()
                                        sound_copy['chapter_id'] = int(chapter_id_str)
                                        sound_copy['segment_index'] = six_card_result.get('_metadata', {}).get('segment_index', 0)
                                        sound_copy['narration_text'] = narrator_content
                                        environment_sounds.append(sound_copy)
                    else:
                        # 兼容旧格式
                        scene_card = chapter_data.get('scene_card', {})
                        chapter_sounds = scene_card.get('environment_sounds', [])
                        
                        # 为每个环境音添加章节信息
                        for sound in chapter_sounds:
                            if isinstance(sound, dict):
                                sound_copy = sound.copy()
                                sound_copy['chapter_id'] = int(chapter_id_str)
                                environment_sounds.append(sound_copy)
                            elif isinstance(sound, str):
                                # 如果是字符串，创建基本的环境音对象
                                sound_obj = {
                                    'keyword': sound,
                                    'description': sound,
                                    'chapter_id': int(chapter_id_str)
                                }
                                environment_sounds.append(sound_obj)
        
        return environment_sounds

    @staticmethod
    def convert_to_environment_tracks_format(environment_sounds: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """转换为环境音项目需要的轨道格式"""
        environment_tracks = []
        
        for sound in environment_sounds:
            # 基础字段映射
            keyword = sound.get("keyword", "")
            description = sound.get("description", "")
            chinese_description = sound.get("chinese_description") or description
            
            # 直接使用书籍分析结果中的时间和强度信息
            start_time = sound.get("start_time", 0)
            end_time = sound.get("end_time", start_time + 30)  # 如果没有end_time，基于start_time计算
            duration = max(1.0, end_time - start_time) if end_time > start_time else 30.0
            
            # 优先使用书籍分析结果中的强度，否则从音量推导
            intensity = sound.get("intensity")
            if not intensity:
                volume = sound.get("volume", 40)
                if volume <= 30:
                    intensity = "low"
                elif volume <= 50:
                    intensity = "medium"
                else:
                    intensity = "high"
            
            # 构建轨道数据（保留分镜原始字段 + 补齐生成所需字段）
            track = {
                # 生成器需要的字段
                "environment_keywords": [keyword] if keyword else [],  # 关键：生成端筛选依赖此字段
                "chinese_description": chinese_description,
                "english_prompt": sound.get("english_prompt", ""),  # 如果没有会在生成时自动生成
                "duration": duration,
                "intensity": intensity,
                
                # 保留分镜原始字段
                "keyword": keyword,
                "description": description,
                "start_time": start_time,
                "end_time": end_time,
                "volume": sound.get("volume", 40),  # 保持原有逻辑作为最后的默认值
                "spatial_position": sound.get("spatial_position", "center"),  # 书籍分析结果中的空间位置
                "fade_in": sound.get("fade_in", 0.2),    # 书籍分析结果中的淡入时间
                "fade_out": sound.get("fade_out", 0.2),  # 书籍分析结果中的淡出时间
                "loop": sound.get("loop", False),        # 书籍分析结果中的循环设置
                
                # 元数据字段
                "chapter_id": sound.get("chapter_id"),
                "segment_index": sound.get("segment_index", 0),
                "narration_text": sound.get("narration_text", ""),
                "source": "book_analysis_sync",
                "sync_timestamp": datetime.now().isoformat(),
                
                # 生成状态字段
                "generated_file_path": None,
                "generation_status": "pending",
                "confidence": 0.9
            }
            
            environment_tracks.append(track)
        
        return environment_tracks

    @staticmethod
    def convert_to_frontend_format(environment_sounds: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """转换为前端需要的格式"""
        formatted_tracks = []
        
        for i, sound in enumerate(environment_sounds):
            # 计算时长，优先使用书籍分析结果
            start_time = sound.get("start_time", 0)
            end_time = sound.get("end_time", start_time + 30)
            duration = max(1.0, end_time - start_time) if end_time > start_time else 30.0
            
            # 获取强度，优先使用书籍分析结果
            intensity = sound.get("intensity")
            if not intensity:
                volume = sound.get("volume", 40)
                if volume <= 30:
                    intensity = "low"
                elif volume <= 50:
                    intensity = "medium"
                else:
                    intensity = "high"
            
            track = {
                "track_id": f"book_analysis_{i+1:03d}",
                "keyword": sound.get("keyword", ""),
                "description": sound.get("description", ""),
                "chinese_description": sound.get("chinese_description", ""),  # 添加中文描述字段
                "source": "book_analysis",  # 标识数据来源
                "duration": duration,      # 使用计算出的时长
                "intensity": intensity,    # 使用推导的强度
                "english_prompt": sound.get("english_prompt", ""),  # 书籍分析结果中的英文提示词
                "chapter_id": sound.get("chapter_id"),
                "paragraph_index": sound.get("segment_index", 0),  # 使用segment_index字段
                "narration_text": sound.get("narration_text", ""),
                "start_time": start_time,  # 使用书籍分析结果中的开始时间
                "generated_file_path": None,  # 默认未生成
                "confidence": sound.get("confidence", 0.85)  # 使用书籍分析结果中的置信度
            }
            formatted_tracks.append(track)
        
        return formatted_tracks
