"""
修正的整合分析服务
基于正确概念：段落 = 对话单元，不需要再次对话分段
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

from app.services.content_enrichment_analyzer import ContentEnrichmentAnalyzer
from app.services.paragraph_script_generator import ParagraphScriptGenerator

logger = logging.getLogger(__name__)


class CorrectedIntegratedAnalysisService:
    """修正的整合分析服务 - 基于正确概念"""
    
    def __init__(self):
        # 初始化各个组件
        self.content_enrichment_analyzer = ContentEnrichmentAnalyzer()
        self.script_generator = ParagraphScriptGenerator()
        
        logger.info("修正的整合分析服务初始化完成")
    
    async def analyze_dialogue_unit(self, 
                                  dialogue_unit_text: str, 
                                  dialogue_unit_index: int,
                                  chapter_id: int = None) -> Dict[str, Any]:
        """
        分析对话单元（段落）
        
        基于正确概念：
        - 段落 = 对话单元
        - 不需要再次对话分段
        - 直接进行6卡内容丰富化
        
        Args:
            dialogue_unit_text: 对话单元原文（智能分段后的段落）
            dialogue_unit_index: 对话单元索引（段落索引）
            chapter_id: 章节ID
            
        Returns:
            包含丰富信息的synthesis_json
        """
        try:
            logger.info(f"开始分析对话单元 {dialogue_unit_index}（段落）")
            
            # 第一步：6卡内容丰富化分析
            logger.info(f"第一步：执行6卡内容丰富化...")
            six_card_analysis = await self.content_enrichment_analyzer.enrich_content(
                dialogue_unit_text, {}, dialogue_unit_index  # 不需要对话分析结果
            )
            
            # 第二步：生成synthesis_json
            logger.info(f"第二步：生成synthesis_json...")
            final_result = await self._generate_synthesis_json(
                dialogue_unit_text, dialogue_unit_index, six_card_analysis
            )
            
            logger.info(f"对话单元 {dialogue_unit_index} 分析完成")
            return final_result
            
        except Exception as e:
            logger.error(f"对话单元 {dialogue_unit_index} 分析失败: {str(e)}")
            raise
    
    async def _generate_synthesis_json(self, 
                                     dialogue_unit_text: str, 
                                     dialogue_unit_index: int,
                                     six_card_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        生成synthesis_json
        
        Args:
            dialogue_unit_text: 对话单元原文（智能分段后的段落）
            dialogue_unit_index: 对话单元索引（段落索引）
            six_card_analysis: 6卡分析结果
            
        Returns:
            包含synthesis_plan的完整JSON结构
        """
        
        # 从6卡分析中提取角色信息
        characters = self._extract_characters_from_six_cards(six_card_analysis)
        
        # 生成synthesis_plan（对话单元内的细分段落）
        synthesis_plan = self._generate_synthesis_plan(
            dialogue_unit_text, six_card_analysis, characters
        )
        
        # 构建最终结果
        final_result = {
            "project_info": {
                "novel_type": "智能检测",
                "total_segments": len(synthesis_plan),  # 对话单元内的细分段落数
                "ai_model": "corrected-integrated-analysis",
                "dialogue_unit_id": f"dialogue_unit_{dialogue_unit_index}",  # 对话单元ID
                "analysis_time": datetime.now().isoformat()
            },
            "synthesis_plan": synthesis_plan,  # 对话单元内的细分段落列表
            "characters": characters,  # 角色列表
            "six_card_analysis": six_card_analysis  # 6卡分析结果
        }
        
        return final_result
    
    def _extract_characters_from_six_cards(self, six_card_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """从6卡分析中提取角色信息"""
        characters = []
        
        # 从角色卡提取
        character_card = six_card_analysis.get("character_card", {})
        characters_involved = character_card.get("characters", [])
        
        for char in characters_involved:
            char_name = char.get("name", "")
            if char_name and char_name not in [c.get("name") for c in characters]:
                characters.append({
                    "name": char_name,
                    "character_id": f"char_{len(characters) + 1}",
                    "voice_name": "未分配",
                    "role_type": char.get("role_type", "一般配角"),
                    "personality": char.get("description", ""),
                    "current_emotion": char.get("emotions", ["平静"])[0] if char.get("emotions") else "平静"
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
    
    def _generate_synthesis_plan(self, 
                               dialogue_unit_text: str, 
                               six_card_analysis: Dict[str, Any],
                               characters: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        生成synthesis_plan（对话单元内的细分段落）
        
        Args:
            dialogue_unit_text: 对话单元原文（智能分段后的段落）
            six_card_analysis: 6卡分析结果
            characters: 角色列表
            
        Returns:
            对话单元内的细分段落列表，每个段落包含对话或旁白
        """
        
        synthesis_plan = []
        current_time = 0
        
        # 从6卡分析中提取对话和旁白
        character_card = six_card_analysis.get("character_card", {})
        characters_involved = character_card.get("characters", [])
        
        # 处理角色对话
        for char in characters_involved:
            char_name = char.get("name", "")
            dialogues = char.get("dialogue", [])
            
            for i, dialogue in enumerate(dialogues):
                if dialogue and dialogue.strip():
                    # 计算时长
                    word_count = len(dialogue.strip())
                    duration_seconds = self.script_generator._calculate_duration(word_count, "平静")
                    
                    # 生成TTS参数
                    tts_params = self._generate_tts_params(char, six_card_analysis)
                    
                    synthesis_plan.append({
                        "segment_id": len(synthesis_plan) + 1,
                        "text": dialogue.strip(),
                        "speaker": char_name,
                        "character_id": next((c.get("character_id") for c in characters if c.get("name") == char_name), "unknown"),
                        "voice_name": next((c.get("voice_name") for c in characters if c.get("name") == char_name), "未分配"),
                        "parameters": tts_params,
                        "emotion": char.get("emotions", ["平静"])[0] if char.get("emotions") else "平静",
                        "start_time": current_time,
                        "end_time": current_time + duration_seconds,
                        "word_count": word_count,
                        "duration_seconds": duration_seconds
                    })
                    
                    current_time += duration_seconds
        
        # 处理旁白内容
        narrator_content = character_card.get("narrator", {}).get("content", "")
        
        if narrator_content and narrator_content.strip():
            word_count = len(narrator_content.strip())
            duration_seconds = self.script_generator._calculate_duration(word_count, "平静")
            
            # 旁白使用标准TTS参数
            narrator_params = self.script_generator.character_tts_rules["旁白"].copy()
            
            synthesis_plan.append({
                "segment_id": len(synthesis_plan) + 1,
                "text": narrator_content.strip(),
                "speaker": "旁白",
                "character_id": "narrator_001",
                "voice_name": "旁白语音",
                "parameters": narrator_params,
                "emotion": "平静",
                "start_time": current_time,
                "end_time": current_time + duration_seconds,
                "word_count": word_count,
                "duration_seconds": duration_seconds
            })
        
        # 如果没有有效的对话和旁白，将整个对话单元作为旁白
        if not synthesis_plan:
            word_count = len(dialogue_unit_text.strip())
            duration_seconds = self.script_generator._calculate_duration(word_count, "平静")
            
            narrator_params = self.script_generator.character_tts_rules["旁白"].copy()
            
            synthesis_plan.append({
                "segment_id": 1,
                "text": dialogue_unit_text.strip(),  # 整个对话单元作为旁白
                "speaker": "旁白",
                "character_id": "narrator_001",
                "voice_name": "旁白语音",
                "parameters": narrator_params,
                "emotion": "平静",
                "start_time": 0,
                "end_time": duration_seconds,
                "word_count": word_count,
                "duration_seconds": duration_seconds
            })
        
        return synthesis_plan
    
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
        if role_type in self.script_generator.character_tts_rules:
            char_rules = self.script_generator.character_tts_rules[role_type]
            base_params["timeStep"] = char_rules["timeStep"]
            base_params["pWeight"] = char_rules["pWeight"]
            base_params["tWeight"] = char_rules["tWeight"]
            base_params["dur_alpha"] = char_rules["dur_alpha"]
            base_params["dur_disturb"] = char_rules["dur_disturb"]
        
        # 2. 情绪权重计算
        emotions = character.get("emotions", ["平静"])
        emotion = emotions[0] if emotions else "平静"
        if emotion in self.script_generator.emotion_tts_rules:
            emotion_rules = self.script_generator.emotion_tts_rules[emotion]
            base_params["dur_alpha"] *= emotion_rules["dur_alpha"]
            base_params["pWeight"] = emotion_rules["pWeight"]
            base_params["dur_disturb"] = emotion_rules["dur_disturb"]
        
        # 3. 事件权重计算
        event_card = six_card_analysis.get("event_card", {})
        event_significance = event_card.get("significance", "日常对话")
        if event_significance in self.script_generator.event_tts_rules:
            event_rules = self.script_generator.event_tts_rules[event_significance]
            base_params["timeStep"] = event_rules["timeStep"]
            base_params["pWeight"] = event_rules["pWeight"]
            base_params["tWeight"] = event_rules["tWeight"]
            base_params["dur_alpha"] *= event_rules["dur_alpha"]
            base_params["dur_disturb"] = event_rules["dur_disturb"]
        
        return base_params
