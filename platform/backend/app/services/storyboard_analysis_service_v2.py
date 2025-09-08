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
        self.script_generator = AudioScriptGenerator(self.llm_client)
        self.story_analyzer = StoryAnalyzer(self.llm_client)
        self.character_analyzer = CharacterAnalyzer(self.llm_client)
    
    def get_session(self, session_id: int):
        """获取分析会话"""
        from app.models.analysis_session import AnalysisSession
        return self.db.query(AnalysisSession).filter(
            AnalysisSession.id == session_id
        ).first()
    
    def get_session_cards(self, session_id: int, chapter_id: Optional[int] = None, card_type: Optional[str] = None) -> List[BaseStoryboardCard]:
        """获取会话的卡片"""
        query = self.db.query(BaseStoryboardCard).filter(
            BaseStoryboardCard.session_id == session_id
        )
        
        if chapter_id:
            query = query.filter(BaseStoryboardCard.chapter_id == chapter_id)
        
        if card_type:
            query = query.filter(BaseStoryboardCard.card_type == card_type)
        
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
            
            # 1. 将章节内容按段落分割
            paragraphs = chapter.content.split('\n')
            paragraphs = [p.strip() for p in paragraphs if p.strip()]
            
            # 2. 分析场景
            logger.info("1. 分析场景...")
            scene_data = await self.scene_analyzer.analyze(chapter.content)
            scene_cards = self._create_scene_cards(session, chapter, scene_data)
            
            # 3. 分析事件
            logger.info("2. 分析事件...")
            event_data = await self.event_analyzer.analyze(chapter.content)
            event_cards = self._create_event_cards(session, chapter, event_data)
            
            # 4. 分析情绪
            logger.info("3. 分析情绪...")
            emotion_data = await self.emotion_analyzer.analyze(chapter.content)
            emotion_cards = self._create_emotion_cards(session, chapter, emotion_data)
            
            # 5. 生成音频剧本卡
            logger.info("4. 生成音频剧本卡...")
            script_data = await self.script_generator.generate_script(
                scene_data, event_data, emotion_data, 
                original_content=chapter.content
            )
            script_cards = self._create_script_cards(session, chapter, script_data, paragraphs)
            
            # 6. 生成音频分镜卡
            logger.info("5. 生成音频分镜卡...")
            storyboard_data = await self.storyboard_generator.generate(scene_data, event_data, emotion_data)
            storyboard_cards = self._create_storyboard_cards_with_mapping(session, chapter, storyboard_data, paragraphs, scene_cards, event_cards, emotion_cards)
            
            # 7. 为其他卡片添加对应关系
            self._add_text_mapping_to_cards(scene_cards, event_cards, emotion_cards, storyboard_cards, paragraphs)
            
            # 8. 先保存所有卡片
            all_cards = scene_cards + event_cards + emotion_cards + script_cards + storyboard_cards
            for card in all_cards:
                self.db.add(card)
            
            self.db.commit()
            
            # 9. 更新音频分镜卡的关联关系（使用真实的卡片ID）
            self._update_storyboard_card_relationships(storyboard_cards, scene_cards, event_cards, emotion_cards, script_cards)
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
    
    def _create_script_cards(self, session: StoryboardAnalysisSession, chapter: BookChapter, script_data: Dict[str, Any], paragraphs: List[str]) -> List[AudioScriptCard]:
        """创建音频剧本卡片"""
        script_cards = []
        
        # 检查剧本数据是否包含段落信息
        script_segments = script_data.get('script_segments', [])
        
        # 如果剧本segment数量少于段落数量，需要补充
        if len(script_segments) < len(paragraphs):
            logger.warning(f"剧本segment数量({len(script_segments)})少于段落数量({len(paragraphs)})，需要补充")
            
            # 为缺失的段落创建默认的剧本segment
            for i in range(len(script_segments), len(paragraphs)):
                default_segment = {
                    "segment_id": f"seg_{i+1:03d}",
                    "start_time": i * 30,
                    "end_time": (i + 1) * 30,
                    "original_text": paragraphs[i],
                    "dialogue": {
                        "speaker": "旁白",
                        "content": [{"content": paragraphs[i], "speaker": "旁白"}],
                        "emotion": "neutral",
                        "tone": "normal",
                        "voice_id": "narrator_001"
                    },
                    "sound_effects": {
                        "volume_levels": {"music": 20, "ambient": 40, "dialogue": 80},
                        "ambient_sounds": [],
                        "background_music": "default_music"
                    },
                    "production_notes": {
                        "sound_mixing": "音效渐入，音乐淡出",
                        "detailed_notes": f"段落 {i+1}: {paragraphs[i][:50]}...",
                        "voice_direction": "语速中等，语调自然",
                        "emotion_guidance": "通过语气表达自然的情感"
                    },
                    "text_mapping": {
                        "word_count": len(paragraphs[i]),
                        "accuracy_score": 0.95,
                        "paragraph_range": [i, i + 1]
                    }
                }
                script_segments.append(default_segment)
        
        # 确保每个segment都有正确的段落范围
        for i, segment in enumerate(script_segments):
            if 'text_mapping' not in segment:
                segment['text_mapping'] = {}
            if 'paragraph_range' not in segment['text_mapping']:
                segment['text_mapping']['paragraph_range'] = [i, i + 1]
        
        # 更新剧本数据
        script_data['script_segments'] = script_segments
        
        # 创建音频剧本卡
        card = AudioScriptCard(
            session_id=session.id,
            chapter_id=chapter.id,
            content=script_data,
            confidence_score=script_data.get('quality_score', 0.85),
            card_type='audio_script'
        )
        script_cards.append(card)
        
        return script_cards
    
    def _create_storyboard_cards_with_mapping(self, session: StoryboardAnalysisSession, chapter: BookChapter, storyboard_data: List[Dict[str, Any]], paragraphs: List[str], scene_cards: List[SceneCard], event_cards: List[EventCard], emotion_cards: List[EmotionCard]) -> List[AudioStoryboardCard]:
        """创建音频分镜卡片并建立对应关系"""
        storyboard_cards = []
        for i, storyboard_info in enumerate(storyboard_data):
            # 计算对应的时间范围
            total_paragraphs = len(paragraphs)
            start_paragraph = i * (total_paragraphs // len(storyboard_data))
            end_paragraph = min((i + 1) * (total_paragraphs // len(storyboard_data)), total_paragraphs)
            
            # 添加对应关系到内容中（暂时不包含卡片ID，等保存后再更新）
            storyboard_info['text_mapping'] = {
                'paragraph_range': [start_paragraph, end_paragraph],
                'scene_index': i,
                'time_range': [i * 30, (i + 1) * 30],  # 每个分镜卡30秒
                'related_cards': {
                    'scene': [i if i < len(scene_cards) else None],
                    'event': [i if i < len(event_cards) else None],
                    'emotion': [i if i < len(emotion_cards) else None]
                }
            }
            
            card = AudioStoryboardCard(
                session_id=session.id,
                chapter_id=chapter.id,
                content=storyboard_info,
                confidence_score=0.88,
                card_type='audio_storyboard'
            )
            storyboard_cards.append(card)
        return storyboard_cards
    
    def _add_text_mapping_to_cards(self, scene_cards: List[SceneCard], event_cards: List[EventCard], emotion_cards: List[EmotionCard], storyboard_cards: List[AudioStoryboardCard], paragraphs: List[str]):
        """为其他卡片添加文本映射关系"""
        total_paragraphs = len(paragraphs)
        
        # 为场景卡添加对应关系
        for i, card in enumerate(scene_cards):
            start_paragraph = i * (total_paragraphs // len(scene_cards))
            end_paragraph = min((i + 1) * (total_paragraphs // len(scene_cards)), total_paragraphs)
            
            if 'text_mapping' not in card.content:
                card.content['text_mapping'] = {}
            card.content['text_mapping']['paragraph_range'] = [start_paragraph, end_paragraph]
        
        # 为事件卡添加对应关系
        for i, card in enumerate(event_cards):
            start_paragraph = i * (total_paragraphs // len(event_cards))
            end_paragraph = min((i + 1) * (total_paragraphs // len(event_cards)), total_paragraphs)
            
            if 'text_mapping' not in card.content:
                card.content['text_mapping'] = {}
            card.content['text_mapping']['paragraph_range'] = [start_paragraph, end_paragraph]
        
        # 为情绪卡添加对应关系
        for i, card in enumerate(emotion_cards):
            start_paragraph = i * (total_paragraphs // len(emotion_cards))
            end_paragraph = min((i + 1) * (total_paragraphs // len(emotion_cards)), total_paragraphs)
            
            if 'text_mapping' not in card.content:
                card.content['text_mapping'] = {}
            card.content['text_mapping']['paragraph_range'] = [start_paragraph, end_paragraph]
    
    def _update_storyboard_card_relationships(self, storyboard_cards: List[AudioStoryboardCard], scene_cards: List[SceneCard], event_cards: List[EventCard], emotion_cards: List[EmotionCard], script_cards: List[AudioScriptCard]):
        """更新音频分镜卡的关联关系（使用真实的卡片ID）"""
        for i, storyboard_card in enumerate(storyboard_cards):
            if 'text_mapping' in storyboard_card.content and 'related_cards' in storyboard_card.content['text_mapping']:
                # 更新关联的卡片ID
                storyboard_card.content['text_mapping']['related_cards'] = {
                    'scene': [scene_cards[i].id if i < len(scene_cards) else None],
                    'event': [event_cards[i].id if i < len(event_cards) else None],
                    'emotion': [emotion_cards[i].id if i < len(emotion_cards) else None],
                    'audio_script': [script_cards[0].id if script_cards else None]  # 音频剧本卡只有一个
                }
    
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
    
    # ==================== API方法补充 ====================
    
    def get_sessions(self, book_id: Optional[int] = None, status: Optional[str] = None, 
                    skip: int = 0, limit: int = 20):
        """获取会话列表"""
        from app.models.analysis_session import AnalysisSession
        from app.models.novel_project import NovelProject
        
        query = self.db.query(AnalysisSession)
        
        # 如果需要按book_id过滤，需要通过项目表关联
        if book_id:
            query = query.join(NovelProject, AnalysisSession.project_id == NovelProject.id)
            query = query.filter(NovelProject.book_id == book_id)
        
        if status:
            query = query.filter(AnalysisSession.status == status)
        
        return query.offset(skip).limit(limit).all()
    
    async def create_analysis_session(self, book_id: int, session_name: str, 
                                    description: str = None, analysis_type: str = 'standard',
                                    llm_config: Dict[str, Any] = None, 
                                    analysis_params: Dict[str, Any] = None):
        """创建分析会话 - 先创建项目，再创建会话"""
        from app.models.novel_project import NovelProject
        from app.models.analysis_session import AnalysisSession
        
        try:
            # 第一步：创建或获取项目
            project = self.db.query(NovelProject).filter(
                NovelProject.book_id == book_id,
                NovelProject.name == session_name
            ).first()
            
            if not project:
                # 创建新项目
                project = NovelProject(
                    book_id=book_id,
                    name=session_name,
                    description=description or f"基于书籍 {book_id} 的分析项目",
                    status='active',
                    config={}
                )
                self.db.add(project)
                self.db.commit()
                self.db.refresh(project)
                logger.debug(f"创建新项目: {project.id} - {project.name}")
            else:
                logger.debug(f"使用现有项目: {project.id} - {project.name}")
            
            # 第二步：创建分析会话
            session = AnalysisSession(
                project_id=project.id,
                session_name=session_name,
                description=description,
                target_type='full_book',
                target_config={},
                llm_config=llm_config or {},
                analysis_params=analysis_params or {},
                status='pending',
                progress=0,
                current_step='等待开始',
                total_chapters=0,
                completed_chapters=0,
                failed_chapters=0
            )
            
            self.db.add(session)
            self.db.commit()
            self.db.refresh(session)
            
            logger.debug(f"创建分析会话: {session.id} - {session.session_name}")
            
            return session
            
        except Exception as e:
            logger.error(f"创建分析会话失败: {str(e)}")
            self.db.rollback()
            raise ServiceException(f"创建分析会话失败: {str(e)}")
    
    def update_card(self, card_id: int, content: Dict[str, Any]) -> BaseStoryboardCard:
        """更新卡片内容"""
        card = self.db.query(BaseStoryboardCard).filter(BaseStoryboardCard.id == card_id).first()
        if not card:
            raise ServiceException("卡片不存在")
        
        card.content = content
        card.updated_at = datetime.now()
        self.db.commit()
        self.db.refresh(card)
        
        return card
    
    def confirm_card(self, card_id: int, confirmed_by: str = None) -> BaseStoryboardCard:
        """确认卡片"""
        card = self.db.query(BaseStoryboardCard).filter(BaseStoryboardCard.id == card_id).first()
        if not card:
            raise ServiceException("卡片不存在")
        
        card.confirmation_status = 'confirmed'
        card.confirmed_by = confirmed_by
        card.confirmed_at = datetime.now()
        self.db.commit()
        self.db.refresh(card)
        
        return card
    
    def request_card_reanalysis(self, card_id: int, requested_by: str = None) -> BaseStoryboardCard:
        """请求重新分析卡片"""
        card = self.db.query(BaseStoryboardCard).filter(BaseStoryboardCard.id == card_id).first()
        if not card:
            raise ServiceException("卡片不存在")
        
        card.confirmation_status = 'reanalysis_requested'
        card.confirmed_by = requested_by
        card.updated_at = datetime.now()
        self.db.commit()
        self.db.refresh(card)
        
        return card
    
    def confirm_session(self, session_id: int, confirmation_type: str = 'storyboard') -> StoryboardAnalysisSession:
        """确认分析会话"""
        session = self.get_session(session_id)
        if not session:
            raise ServiceException("会话不存在")
        
        if confirmation_type == 'storyboard':
            session.storyboard_confirmed = True
        elif confirmation_type == 'book':
            session.book_confirmed = True
        
        session.updated_at = datetime.now()
        self.db.commit()
        self.db.refresh(session)
        
        return session
    
    def reanalyze_session(self, session_id: int) -> bool:
        """重新分析会话"""
        session = self.get_session(session_id)
        if not session:
            raise ServiceException("会话不存在")
        
        # 重置会话状态
        session.status = 'pending'
        session.progress = 0
        session.analyzed_chapters = 0
        session.failed_chapters = 0
        session.started_at = None
        session.completed_at = None
        session.updated_at = datetime.now()
        
        # 删除现有卡片
        cards = self.get_session_cards(session_id)
        for card in cards:
            self.db.delete(card)
        
        self.db.commit()
        
        # 启动重新分析
        asyncio.create_task(self.start_analysis(session_id))
        
        return True
    
    def delete_session(self, session_id: int) -> bool:
        """删除分析会话"""
        session = self.get_session(session_id)
        if not session:
            raise ServiceException("会话不存在")
        
        # 删除所有相关卡片
        cards = self.get_session_cards(session_id)
        for card in cards:
            self.db.delete(card)
        
        # 删除会话
        self.db.delete(session)
        self.db.commit()
        
        return True
