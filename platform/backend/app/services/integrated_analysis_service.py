"""
整合分析服务
结合书籍智能准备的对话分析优势和6卡分析的内容丰富化
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

from app.detectors.ollama_character_detector import OllamaCharacterDetector
from app.services.content_enrichment_analyzer import ContentEnrichmentAnalyzer
from app.services.paragraph_script_generator import ParagraphScriptGenerator

logger = logging.getLogger(__name__)


class IntegratedAnalysisService:
    """整合分析服务 - 结合对话分析和内容丰富化"""
    
    def __init__(self):
        # 初始化各个组件
        self.character_detector = OllamaCharacterDetector()
        self.content_enrichment_analyzer = ContentEnrichmentAnalyzer()
        self.script_generator = ParagraphScriptGenerator()
        
        logger.info("整合分析服务初始化完成")
    
    async def analyze_paragraph(self, 
                              paragraph_text: str, 
                              paragraph_index: int,
                              chapter_id: int = None) -> Dict[str, Any]:
        """
        整合分析段落
        
        Args:
            paragraph_text: 段落原文
            paragraph_index: 段落索引
            chapter_id: 章节ID
            
        Returns:
            包含丰富信息的synthesis_json
        """
        try:
            logger.info(f"开始整合分析段落 {paragraph_index}")
            
            # 第一步：书籍智能准备 - 对话分析和角色识别
            logger.info(f"第一步：执行对话分析和角色识别...")
            dialogue_analysis = await self._analyze_dialogue_and_characters(
                paragraph_text, paragraph_index
            )
            
            # 第二步：6卡分析 - 内容丰富化
            logger.info(f"第二步：执行6卡内容丰富化...")
            six_card_analysis = await self.content_enrichment_analyzer.enrich_content(
                paragraph_text, dialogue_analysis, paragraph_index
            )
            
            # 第三步：整合输出
            logger.info(f"第三步：整合输出最终JSON...")
            final_result = await self._integrate_final_output(
                paragraph_text, paragraph_index, dialogue_analysis, six_card_analysis
            )
            
            logger.info(f"段落 {paragraph_index} 整合分析完成")
            return final_result
            
        except Exception as e:
            logger.error(f"段落 {paragraph_index} 整合分析失败: {str(e)}")
            raise
    
    async def _analyze_dialogue_and_characters(self, 
                                             paragraph_text: str, 
                                             paragraph_index: int) -> Dict[str, Any]:
        """第一步：使用书籍智能准备进行对话分析和角色识别"""
        
        # 构建章节信息
        chapter_info = {
            "chapter_id": None,
            "chapter_title": f"段落_{paragraph_index}",
            "chapter_number": paragraph_index,
            "processing_mode": "single"
        }
        
        # 使用OllamaCharacterDetector进行对话分析
        analysis_result = await self.character_detector.analyze_text(
            paragraph_text, chapter_info
        )
        
        # 提取segments和characters
        segments = analysis_result.get('segments', [])
        characters = analysis_result.get('characters', [])
        
        logger.info(f"对话分析完成：识别到 {len(segments)} 个段落，{len(characters)} 个角色")
        
        return {
            "segments": segments,
            "characters": characters,
            "analysis_metadata": analysis_result.get('analysis_metadata', {})
        }
    
    
    async def _integrate_final_output(self, 
                                    paragraph_text: str, 
                                    paragraph_index: int,
                                    dialogue_analysis: Dict[str, Any],
                                    six_card_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """第三步：整合输出最终JSON"""
        
        # 使用已有的segments（来自对话分析）
        segments = dialogue_analysis.get('segments', [])
        characters = dialogue_analysis.get('characters', [])
        
        # 基于6卡分析生成TTS参数
        synthesis_plan = []
        current_time = 0
        
        for i, segment in enumerate(segments):
            text = segment.get('text', '').strip()
            speaker = segment.get('speaker', '旁白')
            text_type = segment.get('text_type', 'dialogue')
            
            if not text:
                continue
            
            # 计算时长
            word_count = len(text.strip())
            duration_seconds = self.script_generator._calculate_duration(word_count, "平静")
            
            # 基于6卡分析生成TTS参数
            tts_params = self._generate_enhanced_tts_params(
                speaker, text_type, six_card_analysis, characters
            )
            
            synthesis_plan.append({
                "segment_id": i + 1,
                "text": text,
                "speaker": speaker,
                "character_id": f"char_{i + 1}",
                "voice_name": "未分配",
                "parameters": tts_params,
                "emotion": self._get_character_emotion(speaker, six_card_analysis),
                "start_time": current_time,
                "end_time": current_time + duration_seconds,
                "word_count": word_count,
                "duration_seconds": duration_seconds
            })
            
            current_time += duration_seconds
        
        # 构建最终结果
        final_result = {
            "project_info": {
                "novel_type": "智能检测",
                "total_segments": len(synthesis_plan),
                "ai_model": "integrated-analysis",
                "paragraph_id": f"paragraph_{paragraph_index}",
                "analysis_time": datetime.now().isoformat()
            },
            "synthesis_plan": synthesis_plan,
            "characters": self._build_character_list(characters),
            "six_card_analysis": six_card_analysis,
            "dialogue_analysis": dialogue_analysis
        }
        
        return final_result
    
    def _generate_enhanced_tts_params(self, 
                                    speaker: str, 
                                    text_type: str,
                                    six_card_analysis: Dict[str, Any],
                                    characters: List[Dict[str, Any]]) -> Dict[str, Any]:
        """基于6卡分析生成增强的TTS参数"""
        
        # 基础参数
        base_params = {
            "timeStep": 32,
            "pWeight": 1.4,
            "tWeight": 3.0,
            "dur_alpha": 1.0,
            "dur_disturb": 0.1
        }
        
        # 1. 角色类型调整
        if speaker == "旁白":
            base_params.update(self.script_generator.character_tts_rules["旁白"])
        else:
            # 查找角色信息
            char_info = next((c for c in characters if c.get('name') == speaker), None)
            if char_info:
                role_type = self._determine_role_type(char_info, six_card_analysis)
                if role_type in self.script_generator.character_tts_rules:
                    base_params.update(self.script_generator.character_tts_rules[role_type])
        
        # 2. 情绪调整
        emotion = self._get_character_emotion(speaker, six_card_analysis)
        if emotion in self.script_generator.emotion_tts_rules:
            emotion_rules = self.script_generator.emotion_tts_rules[emotion]
            base_params["dur_alpha"] *= emotion_rules["dur_alpha"]
            base_params["pWeight"] = emotion_rules["pWeight"]
            base_params["dur_disturb"] = emotion_rules["dur_disturb"]
        
        # 3. 事件重要性调整
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
    
    def _determine_role_type(self, char_info: Dict[str, Any], six_card_analysis: Dict[str, Any]) -> str:
        """确定角色类型"""
        # 从6卡分析中查找角色信息
        character_card = six_card_analysis.get("character_card", {})
        characters_in_analysis = character_card.get("characters", [])
        
        for char in characters_in_analysis:
            if char.get("name") == char_info.get("name"):
                return char.get("role_type", "一般配角")
        
        # 基于频率判断
        frequency = char_info.get("frequency", 0)
        if frequency >= 3:
            return "重要配角"
        elif frequency >= 1:
            return "一般配角"
        else:
            return "背景角色"
    
    def _get_character_emotion(self, speaker: str, six_card_analysis: Dict[str, Any]) -> str:
        """获取角色情感状态"""
        if speaker == "旁白":
            return "平静"
        
        # 从6卡分析中查找角色情感
        character_card = six_card_analysis.get("character_card", {})
        characters_in_analysis = character_card.get("characters", [])
        
        for char in characters_in_analysis:
            if char.get("name") == speaker:
                emotions = char.get("emotions", [])
                if emotions:
                    return emotions[0]
        
        # 从情绪卡中推断
        emotion_card = six_card_analysis.get("emotion_card", {})
        return emotion_card.get("primary_emotion", "平静")
    
    def _build_character_list(self, characters: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """构建角色列表"""
        character_list = []
        
        for i, char in enumerate(characters):
            character_list.append({
                "name": char.get("name", ""),
                "character_id": f"char_{i + 1}",
                "voice_name": "未分配",
                "role_type": "一般配角",
                "personality": "",
                "current_emotion": "平静"
            })
        
        # 确保旁白角色存在
        if not any(c.get("name") == "旁白" for c in character_list):
            character_list.append({
                "name": "旁白",
                "character_id": "narrator_001",
                "voice_name": "旁白语音",
                "role_type": "旁白",
                "personality": "叙述者",
                "current_emotion": "平静"
            })
        
        return character_list
    
