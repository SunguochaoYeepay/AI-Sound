"""
独立音频分镜卡生成服务
基于5卡分析结果，使用LLM独立生成详细的音频分镜卡
分离音频卡生成逻辑以提升整体分析性能
"""

import asyncio
import logging
import json
from typing import Dict, List, Any, Optional
from datetime import datetime

from app.services.storyboard_analysis.llm_client import LLMClient
from app.utils.llm_config_loader import llm_config_loader

logger = logging.getLogger(__name__)


class IndependentAudioStoryboardService:
    """优化的音频分镜卡生成服务
    - 前2个部分直接复用：timeline, voice_assignments
    - 后2个部分LLM分析：sound_effects, background_music
    - 失败就失败，不使用兜底机制
    """
    
    def __init__(self):
        # 初始化LLM客户端
        self.llm_config = llm_config_loader.get_config()
        self.llm = LLMClient(
            model=self.llm_config["model"], 
            base_url=self.llm_config["base_url"]
        )
        self.llm.timeout = self.llm_config["timeout"]
        
        # 环境音和背景音分析提示词（只分析后2个部分）
        self.audio_environment_prompt = self._build_audio_environment_prompt()
        
        logger.info("独立音频分镜卡生成服务初始化完成")
    
    def _build_audio_environment_prompt(self) -> str:
        """构建环境音和背景音分析提示词（只分析后2个部分）"""
        return """任务：基于环境音关键词和情感基调，生成详细的音效和音乐配置。

【输入信息】
- environment_sounds: 环境音关键词数组
- emotion_tone: 情感基调描述  
- total_duration: 总时长（秒）

【分析要求】
只需要生成以下2个部分的详细配置：

1. **环境音效配置** (sound_effects)
   - 为每个环境音关键词生成详细参数
   - 包含音量、空间位置、时间、淡入淡出、循环等

2. **背景音乐配置** (background_music)  
   - 基于情感基调匹配音乐类型
   - 包含音乐风格、节奏、音量、乐器等

【返回格式】
请返回严格的JSON格式，只包含以下2个部分：

```json
{
  "sound_effects": [
    {
      "id": "effect_1",
      "keyword": "环境音关键词1",
      "description": "详细音效描述",
      "start_time": 2,
      "end_time": 12,
      "volume": 40,
      "spatial_position": "right",
      "loop": false,
      "fade_in": 1.5,
      "fade_out": 2
    },
    {
      "id": "effect_2", 
      "keyword": "环境音关键词2",
      "description": "另一个音效描述",
      "start_time": 18,
      "end_time": 25,
      "volume": 35,
      "spatial_position": "left",
      "loop": false,
      "fade_in": 1,
      "fade_out": 1.5
    }
  ],
  "background_music": {
    "type": "音乐类型",
    "mood": "情感基调",
    "genre": "音乐风格",
    "tempo": "节奏（慢/中/快）",
    "volume": 25,
    "start_time": 0,
    "fade_in": 3,
    "fade_out": 3,
    "loop": true
  }
}
```

【生成注意事项】
1. **环境音时间安排**：
   - 不要让所有环境音同时播放或全程播放
   - 每个环境音应该有合理的出现时机和持续时长
   - 在关键时刻出现，营造氛围后适时淡出
   - 留出"安静"的时间段，让对话更清晰
   - **重要**：环境音应该是点缀性的，不是背景音
   
2. **环境音时长建议**：
   - 短促音效：2-8秒（如马蹄声、脚步声）
   - 持续音效：5-15秒（如叫卖声、人群声）
   - **严格限制**：单个环境音最长不超过15秒
   - 避免超过总时长的30%
   
3. **环境音间隔**：
   - 不同音效之间可以有2-5秒的间隔
   - 重要对话时段减少或暂停环境音
   - 营造"有声有静"的节奏感
   
4. **背景音乐配置**：
   - 音量要低于环境音，不掩盖内容
   - 情感要与场景完全匹配
   
5. **技术参数**：
   - 时间参数使用秒为单位，音量范围0-100
   - 空间位置: center/left/right
   - 淡入淡出时间1-3秒

请基于以下环境音和情感数据生成**有节奏感**的配置："""

    async def generate_audio_storyboard(self, 
                                      five_card_analysis: Dict[str, Any],
                                      segment_text: str,
                                      segment_index: int) -> Dict[str, Any]:
        """
        优化的音频分镜卡生成：前2个直接复用，后2个LLM分析
        
        Args:
            five_card_analysis: 5卡分析结果
            segment_text: 原始段落文本（备用）
            segment_index: 段落索引
            
        Returns:
            完整的音频分镜卡JSON
        """
        logger.debug(f"音频分镜卡生成: 段落 {segment_index}")
        
        # 1. 直接复用：时间轴配置
        synthesis_json = five_card_analysis.get("synthesis_json", {})
        synthesis_plan = synthesis_json.get("synthesis_plan", [])
        
        # 计算总时长
        total_duration = max([seg.get("end_time", 0) for seg in synthesis_plan]) if synthesis_plan else 30
        
        timeline = {
            "total_duration": total_duration,
            "segments": [
                {
                    "segment_id": f"segment_{seg.get('segment_id', i+1)}",
                    "start_time": seg.get("start_time", 0),
                    "end_time": seg.get("end_time", 0),
                    "content_type": "dialogue" if seg.get("speaker") != "旁白" else "narration",
                    "speaker": seg.get("speaker", "旁白"),
                    "content": seg.get("text", ""),
                    "estimated_duration": seg.get("duration_seconds", 0)
                }
                for i, seg in enumerate(synthesis_plan)
            ]
        }
        
        # 2. 直接复用：角色语音配置
        character_card = five_card_analysis.get("character_card", {})
        characters = character_card.get("characters", [])
        narrator = character_card.get("narrator", {})
        
        voice_assignments = {}
        
        # 添加旁白
        voice_assignments["旁白"] = {
            "voice_id": "narrator_001",
            "voice_name": "旁白语音",
            "characteristics": narrator.get("tone", "沉稳叙述"),
            "emotion": "平静"
        }
        
        # 添加角色语音
        for i, char in enumerate(characters):
            char_name = char.get("name", f"角色{i+1}")
            if char_name != "旁白":
                emotions = char.get("emotions", ["平静"])
                voice_assignments[char_name] = {
                    "voice_id": f"char_{i+1:03d}",
                    "voice_name": f"{char_name}语音",
                    "characteristics": char.get("description", "普通语音"),
                    "emotion": emotions[0] if emotions else "平静"
                }
        
        # 3. LLM分析：环境音效和背景音乐
        scene_card = five_card_analysis.get("scene_card", {})
        emotion_card = five_card_analysis.get("emotion_card", {})
        
        environment_sounds = scene_card.get("environment_sounds", [])
        emotion_tone = emotion_card.get("overall_tone", "平静")
        
        # 构建LLM输入（只包含需要分析的部分）
        llm_input = {
            "environment_sounds": environment_sounds,
            "emotion_tone": emotion_tone,
            "total_duration": total_duration
        }
        
        # 调用LLM分析环境音和背景音
        prompt = self.audio_environment_prompt + "\n\n" + json.dumps(llm_input, ensure_ascii=False, indent=2)
        audio_environment = await self.llm.call_json(prompt)
        
        # 4. 组合完整的音频分镜卡
        audio_storyboard = {
            "timeline": timeline,
            "audio_tracks": {
                "main_track": {
                    "name": "主音轨",
                    "priority": 1,
                    "volume": 100,
                    "description": "旁白叙述和角色对话"
                },
                "environment_track": {
                    "name": "环境音轨",
                    "priority": 2,
                    "volume": 40,
                    "description": "环境音效"
                },
                "background_music_track": {
                    "name": "背景音乐",
                    "priority": 3,
                    "volume": 25,
                    "description": "情感氛围音乐"
                }
            },
            "voice_assignments": voice_assignments,
            "sound_effects": audio_environment.get("sound_effects", []),
            "background_music": audio_environment.get("background_music", {}),
            "mixing_parameters": {
                "master_volume": 85,
                "dynamic_range": "normal",
                "spatial_audio": False,
                "reverb": "轻微",
                "eq_settings": "balanced"
            },
            "_metadata": {
                "segment_index": segment_index,
                "generation_time": datetime.utcnow().isoformat(),
                "model_used": self.llm_config["model"],
                "generation_method": "optimized_hybrid",
                "parts_reused": ["timeline", "voice_assignments"],
                "parts_analyzed": ["sound_effects", "background_music"]
            }
        }
        
        logger.debug(f"段落 {segment_index} 音频分镜卡完成（复用+LLM）")
        return audio_storyboard
    
    

    async def batch_generate_audio_storyboards(self, 
                                             five_card_results: List[Dict[str, Any]],
                                             segment_texts: List[str]) -> List[Dict[str, Any]]:
        """批量生成音频分镜卡（失败就直接抛异常，不使用fallback）"""
        logger.debug(f"批量生成 {len(five_card_results)} 个音频分镜卡")
        
        tasks = []
        for i, (five_card_result, segment_text) in enumerate(zip(five_card_results, segment_texts)):
            task = self.generate_audio_storyboard(five_card_result, segment_text, i)
            tasks.append(task)
        
        # 并行生成，失败就失败
        results = await asyncio.gather(*tasks)
        
        logger.debug(f"批量音频分镜卡完成: {len(results)}个")
        return results
