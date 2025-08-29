#!/usr/bin/env python3
"""
故事板分析服务 V2
使用模块化的AI分析器
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from datetime import datetime

from app.models.storyboard_cards import (
    StoryboardAnalysisSession, BaseStoryboardCard, StoryCard, CharacterCard,
    SceneCard, EventCard, EmotionCard, AudioStoryboardCard
)
from app.models import Book, BookChapter

# 导入AI分析器
from .storyboard_analysis.llm_client import LLMClient
from .storyboard_analysis.scene_analyzer import SceneAnalyzer
from .storyboard_analysis.event_analyzer import EventAnalyzer
from .storyboard_analysis.emotion_analyzer import EmotionAnalyzer
from .storyboard_analysis.audio_storyboard_generator import AudioStoryboardGenerator
from .storyboard_analysis.story_analyzer import StoryAnalyzer
from .storyboard_analysis.character_analyzer import CharacterAnalyzer

logger = logging.getLogger(__name__)


class StoryboardAnalysisServiceV2:
    """故事板分析服务 V2"""
    
    def __init__(self, db: Session):
        self.db = db
        
        # 初始化AI客户端和分析器
        self.llm_client = LLMClient()
        self.scene_analyzer = SceneAnalyzer(self.llm_client)
        self.event_analyzer = EventAnalyzer(self.llm_client)
        self.emotion_analyzer = EmotionAnalyzer(self.llm_client)
        self.storyboard_generator = AudioStoryboardGenerator(self.llm_client)
        self.story_analyzer = StoryAnalyzer(self.llm_client)
        self.character_analyzer = CharacterAnalyzer(self.llm_client)
    
    def get_session(self, session_id: int) -> Optional[StoryboardAnalysisSession]:
        """获取分析会话"""
        return self.db.query(StoryboardAnalysisSession).filter(
            StoryboardAnalysisSession.id == session_id
        ).first()
    
    def get_session_cards(self, session_id: int, chapter_id: Optional[int] = None) -> List[BaseStoryboardCard]:
        """获取会话的卡片"""
        query = self.db.query(BaseStoryboardCard).filter(
            BaseStoryboardCard.session_id == session_id
        )
        
        if chapter_id:
            query = query.filter(BaseStoryboardCard.chapter_id == chapter_id)
        
        return query.all()
    
    async def start_analysis(self, session_id: int) -> bool:
        """开始分析"""
        try:
            session = self.get_session(session_id)
            if not session:
                logger.error(f"会话不存在: {session_id}")
                return False
            
            # 标记开始
            session.mark_started()
            self.db.commit()
            
            # 异步执行分析
            asyncio.create_task(self._run_analysis(session))
            
            return True
            
        except Exception as e:
            logger.error(f"启动分析失败: {str(e)}")
            return False
    
    async def _run_analysis(self, session: StoryboardAnalysisSession):
        """执行分析任务"""
        try:
            # 获取书籍章节
            chapters = self.db.query(BookChapter).filter(
                BookChapter.book_id == session.book_id
            ).order_by(BookChapter.chapter_number).all()
            
            session.total_chapters = len(chapters)
            session.current_step = f"开始分析 {len(chapters)} 个章节"
            session.progress = 0
            self.db.commit()
            
            # 第一阶段：章节级分析
            for i, chapter in enumerate(chapters):
                try:
                    session.current_step = f"分析章节 {i+1}/{len(chapters)}: {chapter.chapter_title}"
                    self.db.commit()
                    
                    # 分析章节内容
                    await self._analyze_chapter(session, chapter)
                    
                    session.analyzed_chapters += 1
                    session.progress = session.get_progress_percentage()
                    self.db.commit()
                    
                    # 添加短暂延迟让进度显示更明显
                    await asyncio.sleep(0.1)
                    
                except Exception as e:
                    logger.error(f"分析章节失败: {chapter.id}, 错误: {str(e)}")
                    session.failed_chapters += 1
                    self.db.commit()
            
            # 第二阶段：书籍级分析
            session.current_step = "进行书籍级分析"
            self.db.commit()
            
            await self._analyze_book_level(session)
            
            # 标记完成
            session.current_step = "分析完成，等待确认"
            session.mark_completed()
            self.db.commit()
            
        except Exception as e:
            logger.error(f"分析会话失败: {session.id}, 错误: {str(e)}")
            session.mark_failed(str(e))
            self.db.commit()
    
    async def _analyze_chapter(self, session: StoryboardAnalysisSession, chapter: BookChapter):
        """分析单个章节"""
        try:
            logger.info(f"开始分析章节: {chapter.chapter_title}")
            
            # 1. 分析场景
            logger.info("1. 分析场景...")
            scene_data = await self.scene_analyzer.analyze(chapter.content)
            scene_cards = self._create_scene_cards(session, chapter, scene_data)
            
            # 2. 分析事件
            logger.info("2. 分析事件...")
            event_data = await self.event_analyzer.analyze(chapter.content)
            event_cards = self._create_event_cards(session, chapter, event_data)
            
            # 3. 分析情绪
            logger.info("3. 分析情绪...")
            emotion_data = await self.emotion_analyzer.analyze(chapter.content)
            emotion_cards = self._create_emotion_cards(session, chapter, emotion_data)
            
            # 4. 生成音频分镜卡
            logger.info("4. 生成音频分镜卡...")
            storyboard_data = await self.storyboard_generator.generate(scene_data, event_data, emotion_data)
            storyboard_cards = self._create_storyboard_cards(session, chapter, storyboard_data)
            
            # 保存所有卡片
            all_cards = scene_cards + event_cards + emotion_cards + storyboard_cards
            for card in all_cards:
                self.db.add(card)
            
            self.db.commit()
            logger.info(f"章节 {chapter.id} 分析完成，生成 {len(all_cards)} 个卡片")
            
        except Exception as e:
            logger.error(f"章节分析失败: {str(e)}")
            raise
    
    def _create_scene_cards(self, session: StoryboardAnalysisSession, chapter: BookChapter, scene_data: List[Dict[str, Any]]) -> List[SceneCard]:
        """创建场景卡片"""
        scene_cards = []
        for i, scene_info in enumerate(scene_data):
            card = SceneCard(
                session_id=session.id,
                chapter_id=chapter.id,
                scene_id=i + 1,
                content=scene_info,
                confidence_score=0.85,
                card_type='scene'
            )
            scene_cards.append(card)
        return scene_cards
    
    def _create_event_cards(self, session: StoryboardAnalysisSession, chapter: BookChapter, event_data: List[Dict[str, Any]]) -> List[EventCard]:
        """创建事件卡片"""
        event_cards = []
        for i, event_info in enumerate(event_data):
            card = EventCard(
                session_id=session.id,
                chapter_id=chapter.id,
                content=event_info,
                confidence_score=0.90,
                card_type='event'
            )
            event_cards.append(card)
        return event_cards
    
    def _create_emotion_cards(self, session: StoryboardAnalysisSession, chapter: BookChapter, emotion_data: List[Dict[str, Any]]) -> List[EmotionCard]:
        """创建情绪卡片"""
        emotion_cards = []
        for i, emotion_info in enumerate(emotion_data):
            card = EmotionCard(
                session_id=session.id,
                chapter_id=chapter.id,
                content=emotion_info,
                confidence_score=0.80,
                card_type='emotion'
            )
            emotion_cards.append(card)
        return emotion_cards
    
    def _create_storyboard_cards(self, session: StoryboardAnalysisSession, chapter: BookChapter, storyboard_data: List[Dict[str, Any]]) -> List[AudioStoryboardCard]:
        """创建音频分镜卡片"""
        storyboard_cards = []
        for i, storyboard_info in enumerate(storyboard_data):
            card = AudioStoryboardCard(
                session_id=session.id,
                chapter_id=chapter.id,
                content=storyboard_info,
                confidence_score=0.88,
                card_type='storyboard'
            )
            storyboard_cards.append(card)
        return storyboard_cards
    
    async def _analyze_book_level(self, session: StoryboardAnalysisSession):
        """进行书籍级分析"""
        try:
            logger.info("开始书籍级分析...")
            
            # 获取书籍的所有内容
            chapters = self.db.query(BookChapter).filter(
                BookChapter.book_id == session.book_id
            ).order_by(BookChapter.chapter_number).all()
            
            # 合并所有章节内容
            all_content = "\n\n".join([chapter.content or "" for chapter in chapters])
            
            # 1. 分析故事
            logger.info("1. 分析故事...")
            story_data = await self.story_analyzer.analyze(all_content)
            story_cards = self._create_story_cards(session, story_data)
            
            # 2. 分析角色
            logger.info("2. 分析角色...")
            character_data = await self.character_analyzer.analyze(all_content)
            character_cards = self._create_character_cards(session, character_data)
            
            # 保存书籍级卡片
            all_cards = story_cards + character_cards
            for card in all_cards:
                self.db.add(card)
            
            self.db.commit()
            logger.info(f"书籍级分析完成，生成 {len(all_cards)} 个卡片")
            
        except Exception as e:
            logger.error(f"书籍级分析失败: {str(e)}")
            raise
    
    def _create_story_cards(self, session: StoryboardAnalysisSession, story_data: List[Dict[str, Any]]) -> List[StoryCard]:
        """创建故事卡片"""
        story_cards = []
        for i, story_info in enumerate(story_data):
            card = StoryCard(
                session_id=session.id,
                content=story_info,
                confidence_score=0.92,
                card_type='story'
            )
            story_cards.append(card)
        return story_cards
    
    def _create_character_cards(self, session: StoryboardAnalysisSession, character_data: List[Dict[str, Any]]) -> List[CharacterCard]:
        """创建角色卡片"""
        character_cards = []
        for i, character_info in enumerate(character_data):
            card = CharacterCard(
                session_id=session.id,
                content=character_info,
                confidence_score=0.85,
                card_type='character'
            )
            character_cards.append(card)
        return character_cards
