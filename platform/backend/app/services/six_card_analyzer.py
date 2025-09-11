"""
基于段落的6卡分析服务
根据AI-Sound-Plus设计方案实现
"""

import asyncio
import logging
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from app.services.storyboard_analysis.llm_client import LLMClient
from app.utils.llm_config_loader import llm_config_loader

logger = logging.getLogger(__name__)


class SixCardAnalyzer:
    """6卡分析器 - 基于段落生成6类卡片"""
    
    def __init__(self):
        # 从统一配置加载器读取LLM模型设置
        self.llm_config = llm_config_loader.get_config()
        self.llm = LLMClient(
            model=self.llm_config["model"], 
            base_url=self.llm_config["base_url"]
        )
        self.llm.timeout = self.llm_config["timeout"]
        
        # 6卡分析提示词
        self.analysis_prompt = self._build_analysis_prompt()
        
        # 导入段落剧本生成器
        try:
            from app.services.paragraph_script_generator import ParagraphScriptGenerator
            self.script_generator = ParagraphScriptGenerator()
            logger.info("段落剧本生成器初始化成功")
        except ImportError as e:
            logger.warning(f"段落剧本生成器导入失败: {e}")
            self.script_generator = None
        
        # 🔥 新增：导入音频分镜生成器
        try:
            from app.services.audio_storyboard_generator import AudioStoryboardGenerator
            self.storyboard_generator = AudioStoryboardGenerator()
            logger.info("音频分镜生成器初始化成功")
        except ImportError as e:
            logger.warning(f"音频分镜生成器导入失败: {e}")
            self.storyboard_generator = None
    
    def _build_analysis_prompt(self) -> str:
        """构建6卡分析提示词"""
        return """任务：分析以下小说段落，生成6类卡片的JSON结构。

【重要要求】
1. 角色识别必须完整：包括所有提到的角色，无论是否说话，包括群众、路人、背景角色等
2. 必须识别旁白/叙述内容：如果段落包含旁白叙述，要单独提取出来
3. 角色分类要准确：区分主角、配角、背景角色、群众等不同层级
4. 环境描述要详细：包括所有感官元素（视觉、听觉、触觉、嗅觉等）

【6类卡片说明】
1. 故事卡(story_card): 该段落的核心情节和主题
2. 角色卡(character_card): 该段落中所有角色的表现，包括旁白
3. 场景卡(scene_card): 该段落的场景描述和环境元素
4. 事件卡(event_card): 该段落的具体事件和动作
5. 情绪卡(emotion_card): 该段落的情感变化和氛围
6. 音频剧本卡(audio_script_card): 该段落的音频制作指导

【角色识别特别说明】
- 主角：有明确对话和行动的主要角色
- 配角：有对话或重要行动的支持角色
- 背景角色：被提及但无对话的角色（如"群众"、"路人"、"商贩"等）
- 旁白/叙述者：负责描述场景、心理活动、背景信息的叙述声音
- 集体角色：如"人群"、"士兵们"、"孩子们"等群体

【返回格式】
请返回严格的JSON格式，包含以下结构：

```json
{
  "story_card": {
    "theme": "该段落的主题",
    "plot_point": "核心情节点",
    "narrative_purpose": "叙事目的"
  },
  "character_card": {
    "characters": [
      {
        "name": "角色名",
        "role_type": "主角/配角/背景角色/旁白/集体角色",
        "actions": "角色行为描述",
        "dialogue": ["该角色在段落中说的具体对话内容，必须是原文中的具体文字，不是描述"],
        "emotions": ["情感状态"],
        "description": "角色特征描述"
      }
    ],
    "narrator": {
      "type": "旁白/叙述者",
      "content": "该段落中旁白/叙述者要说的具体文本内容（必须是原文中的具体文字，不是描述性总结）",
      "tone": "叙述语调"
    }
  },
  "scene_card": {
    "location": "具体地点",
    "time": "时间描述",
    "atmosphere": "整体氛围",
    "environment_sounds": [
      {
        "keyword": "环境音效关键词",
        "description": "该环境音效的详细描述，包含场景上下文信息"
      }
    ],
    "visual_elements": ["视觉元素1", "视觉元素2"],
    "sensory_details": ["触觉/嗅觉等其他感官细节"]
  },
  "event_card": {
    "main_event": "主要事件",
    "sub_events": ["子事件1", "子事件2"],
    "significance": "关键转折/日常对话/战斗场景",
    "causality": "因果关系"
  },
  "emotion_card": {
    "overall_tone": "整体情感基调",
    "emotion_changes": [
      {
        "from": "起始情感",
        "to": "结束情感",
        "trigger": "触发因素"
      }
    ],
    "emotional_intensity": 8,
    "primary_emotion": "紧张"
  },
  "audio_script_card": {
    "voice_direction": "语音指导",
    "pacing": "节奏控制",
    "background_music": [
      {
        "keyword": "背景音乐关键词",
        "description": "该背景音乐的详细描述，包含情感和氛围信息"
      }
    ],
    "voice_characteristics": "声音特征要求"
  }
}
```

【分析注意事项】
1. 仔细阅读每个句子，不要遗漏任何角色
2. 区分直接对话和旁白叙述
3. 注意环境描述的细节
4. 情感分析要准确反映段落的情感变化
5. 音频指导要具体且可操作
6. 【重要】角色对话必须是原文中的具体文字，不是描述性总结
7. 【重要】旁白内容必须是原文中的具体叙述文字，不是描述性总结
8. 如果角色没有直接对话，dialogue字段为空数组[]
9. 如果段落主要是叙述，将整个段落作为旁白内容

【角色识别特别规则】
1. 【直接角色】：在段落中直接出现、有具体行为或对话的角色
2. 【背景角色】：通过声音、描述等方式体现的角色（如"胡商叫卖声"中的胡商）
3. 【旁白角色】：负责叙述的角色，应该作为独立角色列出，role_type为"旁白"
4. 【集体角色】：如"人群"、"众人"等，只有当有具体行为时才识别为角色
5. 【声音角色】：通过"叫卖声"、"呼喊声"等体现的角色，应该识别为背景角色

【场景分析特别要求】
1. 【时代背景识别】：必须准确识别场景的时代背景（古代/现代/未来/架空等）
2. 【环境音效匹配】：environment_sounds必须与时代背景完全匹配
   - 严禁混用：古代场景不能出现现代音效，现代场景不能出现古代音效
3. 【场景一致性】：location、time、atmosphere、environment_sounds必须保持时代一致性
4. 【音效具体性】：环境音效要具体明确，避免模糊描述
5. 【环境音效结构化】：environment_sounds必须为对象数组，每个环境音效包含独立的关键词和描述
   - 每个环境音效对象包含keyword（关键词）和description（详细描述）
   - description必须包含该音效的具体场景上下文信息
   - 例如：{"keyword": "马蹄声", "description": "古代街道夜晚的马蹄声，节奏缓慢，营造宁静氛围"}
6. 【背景音乐结构化】：background_music必须为对象数组，每个背景音乐包含独立的关键词和描述
   - 每个背景音乐对象包含keyword（关键词）和description（详细描述）
   - description必须包含该音乐的情感、氛围、节奏等详细信息
   - 例如：{"keyword": "宁静祥和的背景音乐", "description": "轻柔的背景音乐，营造夜晚街道的宁静氛围，节奏缓慢"}

请分析以下段落："""

    async def analyze_segment(self, segment_text: str, segment_index: int, chapter_id: int = None) -> Dict[str, Any]:
        """分析单个段落，生成6卡数据"""
        try:
            logger.info(f"开始分析段落 {segment_index}，长度: {len(segment_text)} 字符")
            
            # 调用LLM进行分析
            prompt = self.analysis_prompt + "\n\n" + segment_text
            response = await self.llm.call_json(prompt)
            
            # 验证返回结果
            if not self._validate_six_cards(response):
                logger.warning(f"段落 {segment_index} 6卡分析结果验证失败")
                response = self._create_fallback_cards(segment_text, segment_index)
            
            # 场景一致性验证暂时跳过，避免方法不存在错误
            # TODO: 实现场景一致性验证逻辑
            
            # 添加元数据
            response["_metadata"] = {
                "segment_index": segment_index,
                "chapter_id": chapter_id,
                "segment_text": segment_text,
                "analysis_time": datetime.utcnow().isoformat(),
                "model_used": self.llm_config["model"]
            }
            
            # 🔥 新增：生成段落剧本（synthesis_json）
            if self.script_generator:
                try:
                    paragraph_id = f"paragraph_{segment_index}"
                    paragraph_script = await self.script_generator.generate_paragraph_script(
                        segment_text, response, paragraph_id
                    )
                    
                    # 将synthesis_json添加到6卡分析结果中
                    response["synthesis_json"] = paragraph_script["synthesis_json"]
                    response["paragraph_script"] = paragraph_script
                    
                    logger.info(f"段落 {segment_index} 剧本生成成功，包含 {len(paragraph_script['synthesis_json']['synthesis_plan'])} 个segment")
                except Exception as e:
                    logger.error(f"段落 {segment_index} 剧本生成失败: {str(e)}")
                    # 创建基础的synthesis_json作为fallback
                    response["synthesis_json"] = self._create_fallback_synthesis_json(segment_text, segment_index)
            else:
                logger.warning("段落剧本生成器未初始化，使用fallback synthesis_json")
                response["synthesis_json"] = self._create_fallback_synthesis_json(segment_text, segment_index)
            
            # 🔥 新增：生成音频制作卡
            if self.storyboard_generator:
                try:
                    # 构建段落剧本数据
                    paragraph_script_data = {
                        "synthesis_json": response["synthesis_json"],
                        "story_card": response.get("story_card", {}),
                        "character_card": response.get("character_card", {}),
                        "scene_card": response.get("scene_card", {}),
                        "event_card": response.get("event_card", {}),
                        "emotion_card": response.get("emotion_card", {}),
                        "audio_script_card": response.get("audio_script_card", {})
                    }
                    
                    # 生成音频制作卡
                    audio_storyboard_card = await self.storyboard_generator.generate_paragraph_storyboard(
                        paragraph_script_data, f"paragraph_{segment_index}"
                    )
                    response["audio_storyboard_card"] = audio_storyboard_card
                    logger.info(f"段落 {segment_index} 音频制作卡生成成功")
                except Exception as e:
                    logger.error(f"段落 {segment_index} 音频制作卡生成失败: {str(e)}")
                    # 创建基础的audio_storyboard_card作为fallback
                    response["audio_storyboard_card"] = self._create_fallback_audio_storyboard_card(segment_text, segment_index)
            else:
                logger.warning("音频分镜生成器未初始化，使用fallback audio_storyboard_card")
                response["audio_storyboard_card"] = self._create_fallback_audio_storyboard_card(segment_text, segment_index)
            
            logger.info(f"段落 {segment_index} 6卡分析完成")
            return response
            
        except Exception as e:
            logger.error(f"段落 {segment_index} 6卡分析失败: {str(e)}")
            fallback_result = self._create_fallback_cards(segment_text, segment_index)
            # 为fallback结果也添加synthesis_json和audio_storyboard_card
            fallback_result["synthesis_json"] = self._create_fallback_synthesis_json(segment_text, segment_index)
            fallback_result["audio_storyboard_card"] = self._create_fallback_audio_storyboard_card(segment_text, segment_index)
            return fallback_result

    async def analyze_segments(self, segments: List[str]) -> List[Dict[str, Any]]:
        """分析所有段落，生成6卡数据列表"""
        logger.info(f"开始分析 {len(segments)} 个段落")
        
        results = []
        for i, segment in enumerate(segments):
            result = await self.analyze_segment(segment, i + 1)
            results.append(result)
        
        logger.info(f"完成所有段落6卡分析，共 {len(results)} 个结果")
        return results

    def _validate_six_cards(self, cards: Dict[str, Any]) -> bool:
        """验证6卡结果是否完整"""
        required_cards = [
            "story_card", "character_card", "scene_card", 
            "event_card", "emotion_card", "audio_script_card"
        ]
        
        for card_type in required_cards:
            if card_type not in cards:
                return False
        
        return True

    def _create_fallback_cards(self, segment_text: str, segment_index: int) -> Dict[str, Any]:
        """创建失败时的回退6卡数据"""
        fallback_data = {
            "story_card": {
                "theme": "未知主题",
                "plot_point": "段落内容分析",
                "narrative_purpose": "推进故事发展"
            },
            "character_card": {
                "characters": [{
                    "name": "未识别角色",
                    "role_type": "背景角色",
                    "actions": "基本行为",
                    "dialogue": [],
                    "emotions": ["中性"],
                    "description": "角色描述缺失"
                }],
                "narrator": {
                    "type": "旁白",
                    "content": "段落叙述内容",
                    "tone": "中性语调"
                }
            },
            "scene_card": {
                "location": "未指定",
                "time": "未知时间",
                "atmosphere": "中性",
                "environment_sounds": [
                    {
                        "keyword": "默认环境音",
                        "description": "基础环境音效，用于fallback场景"
                    }
                ],
                "visual_elements": [],
                "sensory_details": []
            },
            "event_card": {
                "main_event": "段落事件",
                "sub_events": [],
                "significance": "日常对话",
                "causality": "因果关系不明"
            },
            "emotion_card": {
                "overall_tone": "中性",
                "emotion_changes": [],
                "emotional_intensity": 5,
                "primary_emotion": "平静"
            },
            "audio_script_card": {
                "voice_direction": "标准语音",
                "pacing": "正常节奏",
                "background_music": [
                    {
                        "keyword": "默认背景音乐",
                        "description": "基础背景音乐，用于fallback场景"
                    }
                ],
                "voice_characteristics": "标准音色"
            },
            "audio_storyboard_card": {
                "timeline": {
                    "total_duration": 5.0,
                    "segments": [
                        {
                            "start_time": 0,
                            "end_time": 5.0,
                            "speaker": "旁白",
                            "emotion": "中性"
                        }
                    ]
                },
                "audio_tracks": {
                    "main_track": {"name": "主音轨", "priority": "high", "volume": 100},
                    "background_music": {"name": "背景音乐", "priority": "low", "volume": 30},
                    "environment_sound": {"name": "环境音", "priority": "low", "volume": 40}
                },
                "voice_assignments": {
                    "characters": [
                        {
                            "name": "旁白",
                            "role_type": "叙述者",
                            "voice_name": "旁白语音"
                        }
                    ]
                },
                "background_music": {
                    "type": "环境音乐",
                    "mood": "中性",
                    "tempo": "中等",
                    "volume": 30
                },
                "mixing_parameters": {
                    "main_volume": 100,
                    "background_volume": 30,
                    "environment_volume": 40
                },
                "sound_effects": [
                    {
                        "type": "环境音",
                        "description": "基础环境音效",
                        "start_time": 0,
                        "end_time": 5.0,
                        "volume": 40
                    }
                ],
                "scene_sequence": [
                    {
                        "type": "基础场景",
                        "description": "段落场景描述",
                        "start_time": 0,
                        "end_time": 5.0,
                        "atmosphere": "中性"
                    }
                ]
            }
        }
        
        # 添加synthesis_json作为fallback
        fallback_data["synthesis_json"] = self._create_fallback_synthesis_json(segment_text, segment_index)
        
        # 添加元数据
        fallback_data["_metadata"] = {
            "segment_index": segment_index,
            "chapter_id": None,  # fallback数据暂时没有chapter_id
            "segment_text": segment_text,
            "analysis_time": datetime.utcnow().isoformat(),
            "model_used": "fallback"
        }
        
        return fallback_data
    
    def _create_fallback_synthesis_json(self, segment_text: str, segment_index: int) -> Dict[str, Any]:
        """创建基础的synthesis_json作为fallback"""
        word_count = len(segment_text.strip())
        duration_seconds = round(word_count / 300 * 60 / 60, 2)  # 300字/分钟，更符合有声读物标准
        
        return {
            "project_info": {
                "novel_type": "智能检测",
                "total_segments": 1,
                "ai_model": "paragraph-6card-analysis-fallback",
                "paragraph_id": f"paragraph_{segment_index}",
                "analysis_time": datetime.utcnow().isoformat()
            },
            "synthesis_plan": [
                {
                    "segment_id": 1,
                    "text": segment_text.strip(),
                    "speaker": "旁白",
                    "character_id": "narrator_001",
                    "voice_name": "旁白语音",
                    "parameters": {
                        "timeStep": 30,
                        "pWeight": 1.3,
                        "tWeight": 2.8,
                        "dur_alpha": 1.0,
                        "dur_disturb": 0.05
                    },
                    "start_time": 0,
                    "end_time": duration_seconds,
                    "word_count": word_count,
                    "duration_seconds": duration_seconds
                }
            ],
            "characters": [
                {
                    "name": "旁白",
                    "character_id": "narrator_001",
                    "voice_name": "旁白语音"
                }
            ]
        }

    def _create_fallback_audio_script_card(self, segment_text: str, segment_index: int) -> Dict[str, Any]:
        """创建基础的audio_script_card作为fallback"""
        return {
            "voice_direction": "标准语音",
            "pacing": "正常节奏",
            "background_music": [
                {
                    "keyword": "默认背景音乐",
                    "description": "基础背景音乐，用于fallback场景"
                }
            ],
            "voice_characteristics": "标准音色"
        }

    def _create_fallback_audio_storyboard_card(self, segment_text: str, segment_index: int) -> Dict[str, Any]:
        """创建基础的audio_storyboard_card作为fallback"""
        return {
            "timeline": {
                "total_duration": 5.0,
                "segments": [
                    {
                        "start_time": 0,
                        "end_time": 5.0,
                        "speaker": "旁白",
                        "emotion": "中性"
                    }
                ]
            },
            "audio_tracks": {
                "main_track": {"name": "主音轨", "priority": "high", "volume": 100},
                "background_music": {"name": "背景音乐", "priority": "low", "volume": 30},
                "environment_sound": {"name": "环境音", "priority": "low", "volume": 40}
            },
            "voice_assignments": {
                "characters": [
                    {
                        "name": "旁白",
                        "role_type": "叙述者",
                        "voice_name": "旁白语音"
                    }
                ]
            },
            "background_music": {
                "type": "环境音乐",
                "mood": "中性",
                "tempo": "中等",
                "volume": 30
            },
            "mixing_parameters": {
                "main_volume": 100,
                "background_volume": 30,
                "environment_volume": 40
            },
            "sound_effects": [
                {
                    "type": "环境音",
                    "description": "基础环境音效",
                    "start_time": 0,
                    "end_time": 5.0,
                    "volume": 40
                }
            ],
            "scene_sequence": [
                {
                    "type": "基础场景",
                    "description": "段落场景描述",
                    "start_time": 0,
                    "end_time": 5.0,
                    "atmosphere": "中性"
                }
            ]
        }
