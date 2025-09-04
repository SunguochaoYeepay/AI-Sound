#!/usr/bin/env python3
"""
故事板分析服务 V3 - 两阶段分析版本
首轮：qwen3:8b快速分析
次轮：高级模型质量验证
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from datetime import datetime
import json

from app.models.storyboard_cards import (
    StoryboardAnalysisSession, BaseStoryboardCard, StoryCard, CharacterCard,
    SceneCard, EventCard, EmotionCard, AudioStoryboardCard, AudioScriptCard
)
from app.models import Book, BookChapter
from app.utils.exceptions import ServiceException

# 导入AI分析器
from .storyboard_analysis.llm_client import LLMClient
from .storyboard_analysis.scene_analyzer import SceneAnalyzer
from .storyboard_analysis.event_analyzer import EventAnalyzer
from .storyboard_analysis.emotion_analyzer import EmotionAnalyzer
from .storyboard_analysis.audio_storyboard_generator import AudioStoryboardGenerator
from .storyboard_analysis.audio_script_generator import AudioScriptGenerator
from .storyboard_analysis.story_analyzer import StoryAnalyzer
from .storyboard_analysis.character_analyzer import CharacterAnalyzer

# 导入智能分段服务
from .smart_segmentation_service import SmartSegmentationService

logger = logging.getLogger(__name__)


class StoryboardAnalysisServiceV3:
    """故事板分析服务 V3 - 两阶段分析版本"""
    
    def __init__(self, db: Session):
        self.db = db
        
        # 初始化两个LLM客户端
        # 首轮分析：qwen3:8b（快速）
        self.first_round_llm = LLMClient(model="qwen3:8b", base_url="http://localhost:11434")
        
        # 质量验证：qwen3:14b（高精度）
        self.advanced_llm = LLMClient(model="qwen3:14b", base_url="http://localhost:11434")
        
        # 初始化AI分析器（使用首轮LLM）
        self.scene_analyzer = SceneAnalyzer(self.first_round_llm)
        self.event_analyzer = EventAnalyzer(self.first_round_llm)
        self.emotion_analyzer = EmotionAnalyzer(self.first_round_llm)
        self.storyboard_generator = AudioStoryboardGenerator(self.first_round_llm)
        self.script_generator = AudioScriptGenerator(self.first_round_llm)
        self.story_analyzer = StoryAnalyzer(self.first_round_llm)
        self.character_analyzer = CharacterAnalyzer(self.first_round_llm)
        
        # 初始化智能分段服务
        self.segmentation_service = SmartSegmentationService()
    
    def get_session(self, session_id: int) -> Optional[StoryboardAnalysisSession]:
        """获取分析会话"""
        return self.db.query(StoryboardAnalysisSession).filter(
            StoryboardAnalysisSession.id == session_id
        ).first()
    
    async def start_analysis(self, session_id: int) -> bool:
        """开始两阶段分析"""
        try:
            session = self.get_session(session_id)
            if not session:
                logger.error(f"会话不存在: {session_id}")
                return False
            
            # 标记开始
            session.mark_started()
            self.db.commit()
            
            # 异步执行两阶段分析
            asyncio.create_task(self._run_two_stage_analysis(session))
            
            return True
            
        except Exception as e:
            logger.error(f"启动分析失败: {str(e)}")
            return False
    
    async def _run_two_stage_analysis(self, session: StoryboardAnalysisSession):
        """执行两阶段分析任务"""
        try:
            # 获取书籍章节
            chapters = self.db.query(BookChapter).filter(
                BookChapter.book_id == session.book_id
            ).order_by(BookChapter.chapter_number).all()
            
            session.total_chapters = len(chapters)
            session.current_step = f"开始两阶段分析 {len(chapters)} 个章节"
            session.progress = 0
            self.db.commit()
            
            # 第一阶段：首轮快速分析
            logger.info("🚀 第一阶段：首轮快速分析（qwen3:8b）")
            session.current_step = "第一阶段：首轮快速分析"
            first_round_results = {}
            
            for i, chapter in enumerate(chapters):
                try:
                    session.current_step = f"首轮分析章节 {i+1}/{len(chapters)}: {chapter.chapter_title}"
                    session.progress = int((i / len(chapters)) * 40)  # 第一阶段占40%
                    self.db.commit()
                    
                    # 首轮分析
                    first_round_cards = await self._first_round_analysis(session, chapter)
                    first_round_results[chapter.id] = first_round_cards
                    
                    session.analyzed_chapters += 1
                    self.db.commit()
                    
                except Exception as e:
                    logger.error(f"首轮分析章节 {chapter.id} 失败: {str(e)}")
                    session.failed_chapters += 1
                    self.db.commit()
            
            # 第二阶段：高级模型质量验证
            logger.info("🔍 第二阶段：高级模型质量验证（qwen:14b）")
            session.current_step = "第二阶段：高级模型质量验证"
            
            for i, chapter in enumerate(chapters):
                try:
                    session.current_step = f"质量验证章节 {i+1}/{len(chapters)}: {chapter.chapter_title}"
                    session.progress = 40 + int((i / len(chapters)) * 50)  # 第二阶段占50%
                    self.db.commit()
                    
                    # 获取首轮结果
                    first_round_cards = first_round_results.get(chapter.id, [])
                    
                    # 高级模型验证
                    validation_result = await self._advanced_model_validation(chapter.content, first_round_cards)
                    
                    # 基于验证结果优化卡片
                    optimized_cards = await self._optimize_cards_based_on_validation(
                        session, chapter, first_round_cards, validation_result
                    )
                    
                    # 保存优化后的卡片
                    for card in optimized_cards:
                        self.db.add(card)
                    self.db.commit()
                    
                except Exception as e:
                    logger.error(f"质量验证章节 {chapter.id} 失败: {str(e)}")
                    session.failed_chapters += 1
                    self.db.commit()
            
            # 第三阶段：书籍级别分析
            logger.info("📚 第三阶段：书籍级别分析")
            session.current_step = "第三阶段：书籍级别分析"
            session.progress = 90
            self.db.commit()
            
            await self._analyze_book_level(session)
            
            # 标记完成
            session.current_step = "两阶段分析完成，等待确认"
            session.progress = 100
            session.mark_completed()
            self.db.commit()
            
            logger.info("✅ 两阶段分析完成！")
            
        except Exception as e:
            logger.error(f"两阶段分析失败: {session.id}, 错误: {str(e)}")
            session.mark_failed(str(e))
            self.db.commit()
    
    async def _first_round_analysis(self, session: StoryboardAnalysisSession, chapter: BookChapter) -> List[Dict]:
        """第一阶段：首轮快速分析（qwen3:8b）"""
        try:
            logger.info(f"🚀 首轮分析章节: {chapter.chapter_title}")
            
            # 1. 智能分段（新增）
            logger.info("1. 智能分段...")
            segments = await self.segmentation_service.segment_content(chapter.content)
            
            # 验证分段结果
            is_valid = await self.segmentation_service.validate_segments(chapter.content, segments)
            if not is_valid:
                logger.warning("智能分段验证失败，使用原始内容")
                segments = [chapter.content]
            
            logger.info(f"智能分段完成，共 {len(segments)} 段")
            for i, segment in enumerate(segments):
                logger.debug(f"段落 {i+1}: {len(segment)} 字符")
            
            # 2. 智能内容预处理
            processed_content = await self._preprocess_content(chapter.content)
            
            # 3. 基于分段内容进行分析
            logger.info("2. 基于分段内容分析场景、事件、情绪...")
            
            # 收集所有段落的分析结果
            all_scene_data = []
            all_event_data = []
            all_emotion_data = []
            
            for i, segment in enumerate(segments):
                logger.info(f"分析段落 {i+1}/{len(segments)}")
                
                # 并行分析当前段落
                scene_task = self.scene_analyzer.analyze(segment)
                event_task = self.event_analyzer.analyze(segment)
                emotion_task = self.emotion_analyzer.analyze(segment)
                
                segment_scene, segment_event, segment_emotion = await asyncio.gather(
                    scene_task, event_task, emotion_task
                )
                
                # 合并结果
                all_scene_data.extend(segment_scene or [])
                all_event_data.extend(segment_event or [])
                all_emotion_data.extend(segment_emotion or [])
            
            # 使用合并后的数据
            scene_data = all_scene_data
            event_data = all_event_data
            emotion_data = all_emotion_data
            
            # 4. 生成音频剧本卡和分镜卡
            logger.info("3. 生成音频剧本卡和分镜卡...")
            script_data = await self.script_generator.generate_script(
                scene_data, event_data, emotion_data, 
                original_content=chapter.content
            )
            
            storyboard_data = await self.storyboard_generator.generate(scene_data, event_data, emotion_data)
            
            # 5. 创建首轮卡片（不保存到数据库）
            first_round_cards = []
            
            # 场景卡
            for i, scene_info in enumerate(scene_data):
                first_round_cards.append({
                    'type': 'scene',
                    'data': scene_info,
                    'chapter_id': chapter.id,
                    'index': i
                })
            
            # 事件卡
            for i, event_info in enumerate(event_data):
                first_round_cards.append({
                    'type': 'event',
                    'data': event_info,
                    'chapter_id': chapter.id,
                    'index': i
                })
            
            # 情绪卡
            for i, emotion_info in enumerate(emotion_data):
                first_round_cards.append({
                    'type': 'emotion',
                    'data': emotion_info,
                    'chapter_id': chapter.id,
                    'index': i
                })
            
            # 剧本卡
            first_round_cards.append({
                'type': 'audio_script',
                'data': script_data,
                'chapter_id': chapter.id,
                'index': 0
            })
            
            # 分镜卡
            for i, storyboard_info in enumerate(storyboard_data):
                first_round_cards.append({
                    'type': 'audio_storyboard',
                    'data': storyboard_info,
                    'chapter_id': chapter.id,
                    'index': i
                })
            
            logger.info(f"首轮分析完成，生成 {len(first_round_cards)} 个卡片")
            return first_round_cards
            
        except Exception as e:
            logger.error(f"首轮分析失败: {str(e)}")
            raise
    
    async def _advanced_model_validation(self, original_content: str, first_round_cards: List[Dict]) -> Dict:
        """第二阶段：高级模型质量验证（qwen:14b）"""
        try:
            logger.info("🔍 开始高级模型质量验证...")
            
            # 构建验证提示词
            validation_prompt = f"""
你是一个专业的文本分析质量评估专家。请评估以下AI分析结果的质量：

原文：
{original_content}

首轮分析结果（6类卡片）：
{json.dumps(first_round_cards, ensure_ascii=False, indent=2)}

请从以下维度评估每张卡片：

1. 准确性：分析结果是否准确反映了原文内容？
2. 完整性：是否遗漏了重要信息？
3. 逻辑性：分析逻辑是否合理？
4. 一致性：与原文的描述是否一致？

对每张卡片给出：
- 质量评分（0-1）
- 具体问题描述
- 改进建议

请用JSON格式返回详细评估结果，格式如下：
{{
    "overall_quality": 0.85,
    "cards_evaluation": [
        {{
            "card_index": 0,
            "card_type": "scene",
            "quality_score": 0.9,
            "accuracy": 0.9,
            "completeness": 0.8,
            "logic": 0.9,
            "consistency": 0.9,
            "issues": ["遗漏了部分环境描述"],
            "suggestions": ["补充环境细节描述"],
            "overall_feedback": "整体质量良好，但可以更详细"
        }}
    ],
    "summary": "首轮分析整体质量良好，主要问题在于细节完整性"
}}
"""
            
            # 调用高级模型进行评估
            logger.info("调用qwen:14b进行质量验证...")
            validation_result = await self.advanced_llm.call_json(validation_prompt, temperature=0.1)
            
            if validation_result:
                logger.info(f"质量验证完成，整体质量评分: {validation_result.get('overall_quality', 0)}")
                return validation_result
            else:
                logger.warning("高级模型验证失败，使用默认验证结果")
                return self._generate_default_validation_result(first_round_cards)
                
        except Exception as e:
            logger.error(f"高级模型验证失败: {str(e)}")
            return self._generate_default_validation_result(first_round_cards)
    
    def _generate_default_validation_result(self, first_round_cards: List[Dict]) -> Dict:
        """生成默认验证结果（当高级模型验证失败时）"""
        default_result = {
            "overall_quality": 0.7,
            "cards_evaluation": [],
            "summary": "高级模型验证失败，使用默认评估"
        }
        
        for i, card in enumerate(first_round_cards):
            default_result["cards_evaluation"].append({
                "card_index": i,
                "card_type": card.get("type", "unknown"),
                "quality_score": 0.7,
                "accuracy": 0.7,
                "completeness": 0.7,
                "logic": 0.7,
                "consistency": 0.7,
                "issues": ["需要进一步验证"],
                "suggestions": ["建议人工审核"],
                "overall_feedback": "默认评估，需要进一步验证"
            })
        
        return default_result
    
    async def _optimize_cards_based_on_validation(self, session: StoryboardAnalysisSession, 
                                                chapter: BookChapter, 
                                                first_round_cards: List[Dict], 
                                                validation_result: Dict) -> List[BaseStoryboardCard]:
        """基于验证结果优化卡片"""
        try:
            logger.info("🔧 基于验证结果优化卡片...")
            
            optimized_cards = []
            cards_evaluation = validation_result.get("cards_evaluation", [])
            
            for i, card in enumerate(first_round_cards):
                # 获取该卡片的验证结果
                card_eval = next((eval_item for eval_item in cards_evaluation if eval_item.get("card_index") == i), None)
                
                if card_eval:
                    quality_score = card_eval.get("quality_score", 0.7)
                    issues = card_eval.get("issues", [])
                    suggestions = card_eval.get("suggestions", [])
                    
                    # 如果质量不达标，尝试优化
                    if quality_score < 0.8:
                        logger.info(f"卡片 {i} 质量不达标({quality_score:.2f})，尝试优化...")
                        optimized_data = await self._attempt_card_optimization(
                            card, chapter.content, issues, suggestions
                        )
                        card['data'] = optimized_data
                        quality_score = min(quality_score + 0.1, 0.9)  # 优化后提升质量
                
                # 创建最终的数据库卡片
                final_card = self._create_final_card(session, chapter, card, quality_score)
                optimized_cards.append(final_card)
            
            logger.info(f"卡片优化完成，生成 {len(optimized_cards)} 个优化后的卡片")
            return optimized_cards
            
        except Exception as e:
            logger.error(f"卡片优化失败: {str(e)}")
            # 如果优化失败，返回原始卡片
            return [self._create_final_card(session, chapter, card, 0.7) for card in first_round_cards]
    
    async def _attempt_card_optimization(self, card: Dict, original_content: str, 
                                       issues: List[str], suggestions: List[str]) -> Dict:
        """尝试优化单个卡片"""
        try:
            # 构建优化提示词
            optimization_prompt = f"""
请基于以下反馈优化分析结果：

原始分析结果：
{json.dumps(card['data'], ensure_ascii=False)}

原文内容：
{original_content}

发现的问题：
{json.dumps(issues, ensure_ascii=False)}

改进建议：
{json.dumps(suggestions, ensure_ascii=False)}

请提供优化后的分析结果，确保：
1. 解决上述问题
2. 遵循改进建议
3. 保持与原文的一致性
4. 提高分析的准确性和完整性

请返回优化后的JSON格式结果。
"""
            
            # 使用高级模型进行优化
            optimized_result = await self.advanced_llm.call_json(optimization_prompt, temperature=0.2)
            
            if optimized_result:
                logger.info(f"卡片 {card.get('type')} 优化成功")
                return optimized_result
            else:
                logger.warning(f"卡片 {card.get('type')} 优化失败，保持原结果")
                return card['data']
                
        except Exception as e:
            logger.error(f"卡片优化失败: {str(e)}")
            return card['data']
    
    def _create_final_card(self, session: StoryboardAnalysisSession, chapter: BookChapter, 
                          card: Dict, quality_score: float) -> BaseStoryboardCard:
        """创建最终的数据库卡片"""
        try:
            card_type = card.get('type')
            card_data = card.get('data', {})
            
            # 确保卡片数据包含质量信息
            if isinstance(card_data, dict):
                card_data['quality_score'] = quality_score
                card_data['analysis_stage'] = 'two_stage_optimized'
                card_data['created_at'] = datetime.now().isoformat()
                card_data['version'] = 'v3_two_stage'
            
            # 根据卡片类型创建对应的数据库模型
            if card_type == 'scene':
                return SceneCard(
                    session_id=session.id,
                    chapter_id=chapter.id,
                    scene_id=card.get('index', 0) + 1,
                    content=card_data,
                    confidence_score=quality_score,
                    card_type='scene'
                )
            elif card_type == 'event':
                return EventCard(
                    session_id=session.id,
                    chapter_id=chapter.id,
                    content=card_data,
                    confidence_score=quality_score,
                    card_type='event'
                )
            elif card_type == 'emotion':
                return EmotionCard(
                    session_id=session.id,
                    chapter_id=chapter.id,
                    content=card_data,
                    confidence_score=quality_score,
                    card_type='emotion'
                )
            elif card_type == 'audio_script':
                return AudioScriptCard(
                    session_id=session.id,
                    chapter_id=chapter.id,
                    content=card_data,
                    confidence_score=quality_score,
                    card_type='audio_script'
                )
            elif card_type == 'audio_storyboard':
                return AudioStoryboardCard(
                    session_id=session.id,
                    chapter_id=chapter.id,
                    content=card_data,
                    confidence_score=quality_score,
                    card_type='audio_storyboard'
                )
            else:
                # 默认创建基础卡片
                return BaseStoryboardCard(
                    session_id=session.id,
                    chapter_id=chapter.id,
                    content=card_data,
                    confidence_score=quality_score,
                    card_type=card_type
                )
                
        except Exception as e:
            logger.error(f"创建最终卡片失败: {str(e)}")
            # 创建基础卡片作为后备
            return BaseStoryboardCard(
                session_id=session.id,
                chapter_id=chapter.id,
                content=card.get('data', {}),
                confidence_score=quality_score,
                card_type=card.get('type', 'unknown')
            )
    
    async def _preprocess_content(self, content: str) -> str:
        """智能内容预处理"""
        try:
            # 1. 清理和标准化文本
            cleaned_content = self._clean_text(content)
            
            # 2. 智能分段
            paragraphs = self._smart_paragraph_split(cleaned_content)
            
            # 3. 内容增强
            enhanced_content = await self._enhance_content_with_context(cleaned_content, paragraphs)
            
            return enhanced_content
            
        except Exception as e:
            logger.error(f"内容预处理失败: {str(e)}")
            return content
    
    def _clean_text(self, text: str) -> str:
        """清理文本"""
        # 移除多余的空白字符
        text = ' '.join(text.split())
        
        # 标准化标点符号
        text = text.replace('，', ',').replace('。', '.').replace('！', '!').replace('？', '?')
        
        # 移除特殊字符
        import re
        text = re.sub(r'[^\w\s,\.!?，。！？]', '', text)
        
        return text
    
    def _smart_paragraph_split(self, text: str) -> List[str]:
        """智能段落分割"""
        # 基于句号和换行符分割
        paragraphs = []
        
        # 按句号分割
        sentences = text.split('。')
        
        current_paragraph = ""
        for sentence in sentences:
            if sentence.strip():
                current_paragraph += sentence.strip() + "。"
                
                # 如果段落长度超过200字符，开始新段落
                if len(current_paragraph) > 200:
                    paragraphs.append(current_paragraph.strip())
                    current_paragraph = ""
        
        # 添加最后一个段落
        if current_paragraph.strip():
            paragraphs.append(current_paragraph.strip())
        
        return paragraphs
    
    async def _enhance_content_with_context(self, content: str, paragraphs: List[str]) -> str:
        """增强内容上下文"""
        try:
            # 构建上下文提示词
            context_prompt = f"""
请分析以下文本内容，并增强其上下文信息：

原文：
{content}

段落数量：{len(paragraphs)}

请提供：
1. 主要场景描述
2. 关键事件概述
3. 主要情绪变化
4. 人物关系说明

请用JSON格式返回增强后的内容。
"""
            
            # 调用首轮LLM增强内容
            enhanced_result = await self.first_round_llm.call_json(context_prompt, temperature=0.2)
            
            if enhanced_result and isinstance(enhanced_result, dict):
                # 将增强信息添加到原文
                enhanced_content = f"{content}\n\n[增强上下文]\n{json.dumps(enhanced_result, ensure_ascii=False)}"
                return enhanced_content
            
            return content
            
        except Exception as e:
            logger.error(f"内容增强失败: {str(e)}")
            return content
    
    async def _analyze_book_level(self, session: StoryboardAnalysisSession):
        """分析书籍级别信息"""
        try:
            # 获取所有章节的卡片
            all_cards = self.db.query(BaseStoryboardCard).filter(
                BaseStoryboardCard.session_id == session.id
            ).all()
            
            # 生成书籍级别的故事卡
            story_data = await self._generate_book_story_summary(all_cards)
            story_cards = self._create_enhanced_story_cards(session, story_data)
            
            # 生成书籍级别的角色卡
            character_data = await self._generate_book_character_summary(all_cards)
            character_cards = self._create_enhanced_character_cards(session, character_data)
            
            # 保存书籍级别卡片
            for card in story_cards + character_cards:
                self.db.add(card)
            
            self.db.commit()
            
        except Exception as e:
            logger.error(f"书籍级别分析失败: {str(e)}")
    
    async def _generate_book_story_summary(self, all_cards: List[BaseStoryboardCard]) -> List[Dict]:
        """生成书籍故事摘要"""
        try:
            # 收集所有卡片的关键信息
            story_elements = []
            
            for card in all_cards:
                content = getattr(card, 'content', {})
                if isinstance(content, dict):
                    if card.card_type == 'scene':
                        story_elements.append({
                            'type': 'scene',
                            'content': content.get('scene_name', ''),
                            'description': content.get('description', '')
                        })
                    elif card.card_type == 'event':
                        story_elements.append({
                            'type': 'event',
                            'content': content.get('event_name', ''),
                            'description': content.get('description', '')
                        })
            
            # 构建故事摘要提示词
            summary_prompt = f"""
基于以下故事元素，生成书籍级别的故事摘要：

故事元素：
{json.dumps(story_elements, ensure_ascii=False)}

请提供：
1. 整体故事概述
2. 主要情节线
3. 故事主题
4. 关键转折点

请用JSON格式返回。
"""
            
            # 调用高级LLM生成摘要
            summary_result = await self.advanced_llm.call_json(summary_prompt, temperature=0.3)
            
            if summary_result and isinstance(summary_result, dict):
                return [summary_result]
            
            return []
            
        except Exception as e:
            logger.error(f"生成书籍故事摘要失败: {str(e)}")
            return []
    
    async def _generate_book_character_summary(self, all_cards: List[BaseStoryboardCard]) -> List[Dict]:
        """生成书籍角色摘要"""
        try:
            # 收集角色信息
            character_elements = []
            
            for card in all_cards:
                content = getattr(card, 'content', {})
                if isinstance(content, dict) and card.card_type == 'character':
                    character_elements.append({
                        'name': content.get('character_name', ''),
                        'description': content.get('description', ''),
                        'role': content.get('role', '')
                    })
            
            # 构建角色摘要提示词
            character_prompt = f"""
基于以下角色信息，生成书籍级别的角色摘要：

角色信息：
{json.dumps(character_elements, ensure_ascii=False)}

请提供：
1. 主要角色分析
2. 角色关系网络
3. 角色发展弧线
4. 重要配角说明

请用JSON格式返回。
"""
            
            # 调用高级LLM生成摘要
            character_result = await self.advanced_llm.call_json(character_prompt, temperature=0.3)
            
            if character_result and isinstance(character_result, dict):
                return [character_result]
            
            return []
            
        except Exception as e:
            logger.error(f"生成书籍角色摘要失败: {str(e)}")
            return []
    
    def _create_enhanced_story_cards(self, session: StoryboardAnalysisSession, story_data: List[Dict]) -> List[StoryCard]:
        """创建增强的故事卡片"""
        story_cards = []
        for i, story_info in enumerate(story_data):
            card = StoryCard(
                session_id=session.id,
                content=story_info,
                confidence_score=story_info.get('confidence_score', 0.85),
                card_type='story'
            )
            story_cards.append(card)
        return story_cards
    
    def _create_enhanced_character_cards(self, session: StoryboardAnalysisSession, character_data: List[Dict]) -> List[CharacterCard]:
        """创建增强的角色卡片"""
        character_cards = []
        for i, character_info in enumerate(character_data):
            card = CharacterCard(
                session_id=session.id,
                content=character_info,
                confidence_score=character_info.get('confidence_score', 0.85),
                card_type='character'
            )
            character_cards.append(card)
        return character_cards
