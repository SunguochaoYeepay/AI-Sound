"""
故事板分析服务
基于6类卡片方案的AI智能分析服务
"""

import asyncio
import json
import logging
from typing import List, Dict, Any, Optional, AsyncGenerator
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from ..models import (
    Book, BookChapter, StoryboardAnalysisSession, BaseStoryboardCard,
    StoryCard, CharacterCard, SceneCard, EventCard, EmotionCard, AudioStoryboardCard
)
from ..utils.exceptions import ServiceException
from ..websocket.manager import websocket_manager

logger = logging.getLogger(__name__)


class StoryboardAnalysisService:
    """故事板分析服务"""
    
    def __init__(self, db: Session):
        self.db = db
        self.websocket_manager = websocket_manager
        
    async def create_analysis_session(
        self,
        book_id: int,
        session_name: str,
        description: str = None,
        analysis_type: str = 'standard',
        llm_config: Dict[str, Any] = None,
        analysis_params: Dict[str, Any] = None
    ) -> StoryboardAnalysisSession:
        """创建新的故事板分析会话"""
        
        # 验证书籍存在
        book = self.db.query(Book).filter(Book.id == book_id).first()
        if not book:
            raise ServiceException("书籍不存在")
        
        # 计算章节总数
        total_chapters = self.db.query(BookChapter).filter(
            BookChapter.book_id == book_id
        ).count()
        
        # 创建会话
        session = StoryboardAnalysisSession(
            book_id=book_id,
            session_name=session_name,
            description=description,
            analysis_type=analysis_type,
            llm_config=llm_config or {},
            analysis_params=analysis_params or {},
            total_chapters=total_chapters
        )
        
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)
        
        logger.info(f"创建故事板分析会话: {session.id}")
        return session
    
    async def start_analysis(self, session_id: int) -> bool:
        """开始分析会话"""
        session = self.db.query(StoryboardAnalysisSession).filter(
            StoryboardAnalysisSession.id == session_id
        ).first()
        
        if not session:
            raise ServiceException("分析会话不存在")
        
        if session.status != 'pending':
            raise ServiceException(f"会话状态不正确: {session.status}")
        
        # 更新会话状态
        session.mark_started()
        self.db.commit()
        
        # 异步启动分析任务
        asyncio.create_task(self._run_analysis(session))
        
        return True
    
    async def _run_analysis(self, session: StoryboardAnalysisSession):
        """执行分析任务"""
        try:
            # 获取书籍章节
            chapters = self.db.query(BookChapter).filter(
                BookChapter.book_id == session.book_id
            ).order_by(BookChapter.chapter_number).all()
            
            session.current_step = f"开始分析 {len(chapters)} 个章节"
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
                    
                    # 发送进度更新
                    await self._send_progress_update(session)
                    
                except Exception as e:
                    logger.error(f"分析章节失败: {chapter.id}, 错误: {str(e)}")
                    session.failed_chapters += 1
                    self.db.commit()
            
            # 第二阶段：书籍级分析
            session.current_step = "进行书籍级分析"
            self.db.commit()
            
            await self._analyze_book_level(session)
            
            # 标记完成
            session.mark_completed()
            self.db.commit()
            
            # 发送完成通知
            await self._send_completion_notification(session)
            
        except Exception as e:
            logger.error(f"分析会话失败: {session.id}, 错误: {str(e)}")
            session.mark_failed(str(e))
            self.db.commit()
    
    async def _analyze_chapter(self, session: StoryboardAnalysisSession, chapter: BookChapter):
        """分析单个章节"""
        # 这里调用AI服务进行实际分析
        # 为了演示，我们创建示例卡片数据
        
        # 1. 分析场景
        scene_cards = await self._analyze_scenes(session, chapter)
        
        # 2. 分析事件
        event_cards = await self._analyze_events(session, chapter)
        
        # 3. 分析情绪
        emotion_cards = await self._analyze_emotions(session, chapter)
        
        # 4. 生成音频分镜卡
        storyboard_cards = await self._generate_audio_storyboard(
            session, chapter, scene_cards, event_cards, emotion_cards
        )
        
        # 保存所有卡片
        all_cards = scene_cards + event_cards + emotion_cards + storyboard_cards
        for card in all_cards:
            self.db.add(card)
        
        self.db.commit()
    
    async def _analyze_scenes(self, session: StoryboardAnalysisSession, chapter: BookChapter) -> List[SceneCard]:
        """分析章节中的场景"""
        # 这里应该调用AI服务分析场景
        # 示例数据
        scenes = [
            {
                'scene_name': f"{chapter.chapter_title} - 场景1",
                'scene_type': '室内',
                'location': {'type': '客栈', 'description': '热闹的客栈内部'},
                'atmosphere': {'mood': '热闹', 'lighting': '温暖'},
                'time_period': '夜晚',
                'environmental_sounds': ['人声嘈杂', '酒杯碰撞声']
            }
        ]
        
        scene_cards = []
        for i, scene_data in enumerate(scenes):
            card = SceneCard(
                session_id=session.id,
                chapter_id=chapter.id,
                scene_id=i + 1,
                content=scene_data,
                confidence_score=0.85
            )
            scene_cards.append(card)
        
        return scene_cards
    
    async def _analyze_events(self, session: StoryboardAnalysisSession, chapter: BookChapter) -> List[EventCard]:
        """分析章节中的事件"""
        # 这里应该调用AI服务分析事件
        # 示例数据
        events = [
            {
                'event_name': '萧炎点酒',
                'event_type': '对话',
                'participants': ['萧炎', '店小二'],
                'action_description': '萧炎走进客栈，向店小二点酒',
                'dialogue_content': [
                    {'speaker': '萧炎', 'content': '来一壶好酒'},
                    {'speaker': '店小二', 'content': '好嘞，客官稍等'}
                ],
                'emotional_context': {'mood': '平静', 'tension': '低'}
            }
        ]
        
        event_cards = []
        for i, event_data in enumerate(events):
            card = EventCard(
                session_id=session.id,
                chapter_id=chapter.id,
                content=event_data,
                confidence_score=0.90
            )
            event_cards.append(card)
        
        return event_cards
    
    async def _analyze_emotions(self, session: StoryboardAnalysisSession, chapter: BookChapter) -> List[EmotionCard]:
        """分析章节中的情绪"""
        # 这里应该调用AI服务分析情绪
        # 示例数据
        emotions = [
            {
                'emotion_type': '平静',
                'intensity': 0.7,
                'duration': {'start': 0, 'end': 30},
                'triggers': ['进入熟悉环境'],
                'expression': ['面部放松', '步伐从容'],
                'voice_impact': {'tone': '温和', 'pace': '中等'}
            }
        ]
        
        emotion_cards = []
        for i, emotion_data in enumerate(emotions):
            card = EmotionCard(
                session_id=session.id,
                chapter_id=chapter.id,
                content=emotion_data,
                confidence_score=0.80
            )
            emotion_cards.append(card)
        
        return emotion_cards
    
    async def _generate_audio_storyboard(
        self,
        session: StoryboardAnalysisSession,
        chapter: BookChapter,
        scene_cards: List[SceneCard],
        event_cards: List[EventCard],
        emotion_cards: List[EmotionCard]
    ) -> List[AudioStoryboardCard]:
        """生成音频分镜卡"""
        # 这里应该基于场景、事件、情绪卡生成音频分镜
        # 示例数据
        storyboard_data = {
            'timeline': [
                {
                    'time_range': '0-15s',
                    'content': '萧炎走进客栈',
                    'audio_type': 'narration',
                    'voice_id': 'narrator_001'
                },
                {
                    'time_range': '15-30s',
                    'content': '萧炎点酒对话',
                    'audio_type': 'dialogue',
                    'voice_id': 'xiaoyan_001',
                    'participants': ['萧炎', '店小二']
                }
            ],
            'audio_tracks': {
                'dialogue': {'volume': 80, 'priority': 'high'},
                'narration': {'volume': 70, 'priority': 'medium'},
                'environment': {'volume': 30, 'priority': 'low'},
                'background_music': {'volume': 20, 'priority': 'low'}
            },
            'voice_assignments': {
                '萧炎': 'xiaoyan_001',
                '店小二': 'waiter_001',
                '旁白': 'narrator_001'
            },
            'sound_effects': [
                {'time': '0-5s', 'effect': 'footsteps', 'volume': 40},
                {'time': '10-15s', 'effect': 'door_open', 'volume': 50}
            ],
            'background_music': {
                'type': 'ambient',
                'mood': 'peaceful',
                'volume': 20,
                'fade_in': 3,
                'fade_out': 3
            }
        }
        
        card = AudioStoryboardCard(
            session_id=session.id,
            chapter_id=chapter.id,
            content=storyboard_data,
            confidence_score=0.88
        )
        
        return [card]
    
    async def _analyze_book_level(self, session: StoryboardAnalysisSession):
        """进行书籍级分析"""
        # 1. 生成故事卡
        story_card = await self._generate_story_card(session)
        
        # 2. 生成角色卡
        character_cards = await self._generate_character_cards(session)
        
        # 保存书籍级卡片
        self.db.add(story_card)
        for card in character_cards:
            self.db.add(card)
        
        self.db.commit()
    
    async def _generate_story_card(self, session: StoryboardAnalysisSession) -> StoryCard:
        """生成故事卡"""
        # 这里应该调用AI服务分析整个故事
        # 示例数据
        story_data = {
            'story_summary': '这是一个关于修炼者萧炎的成长故事',
            'main_plot': [
                {'chapter': 1, 'event': '萧炎开始修炼'},
                {'chapter': 2, 'event': '萧炎遇到挑战'}
            ],
            'themes': ['成长', '友情', '坚持'],
            'genre': '玄幻',
            'target_audience': '青少年'
        }
        
        card = StoryCard(
            session_id=session.id,
            content=story_data,
            confidence_score=0.92
        )
        
        return card
    
    async def _generate_character_cards(self, session: StoryboardAnalysisSession) -> List[CharacterCard]:
        """生成角色卡"""
        # 这里应该调用AI服务分析所有角色
        # 示例数据
        characters = [
            {
                'character_name': '萧炎',
                'character_type': '主角',
                'personality': ['坚韧', '聪明', '正义'],
                'background': '萧家天才，后来失去天赋，重新崛起',
                'voice_characteristics': {
                    'tone': '沉稳',
                    'age_range': '16-20',
                    'accent': '标准普通话'
                },
                'emotional_range': ['平静', '愤怒', '喜悦', '悲伤']
            },
            {
                'character_name': '店小二',
                'character_type': '配角',
                'personality': ['热情', '机灵'],
                'background': '客栈服务员',
                'voice_characteristics': {
                    'tone': '轻快',
                    'age_range': '20-25',
                    'accent': '略带方言'
                },
                'emotional_range': ['热情', '好奇']
            }
        ]
        
        character_cards = []
        for char_data in characters:
            card = CharacterCard(
                session_id=session.id,
                content=char_data,
                confidence_score=0.85
            )
            character_cards.append(card)
        
        return character_cards
    
    async def _send_progress_update(self, session: StoryboardAnalysisSession):
        """发送进度更新"""
        try:
            await self.websocket_manager.broadcast_to_session(
                f"storyboard_analysis_{session.id}",
                {
                    "type": "progress_update",
                    "session_id": session.id,
                    "progress": session.progress,
                    "current_step": session.current_step,
                    "analyzed_chapters": session.analyzed_chapters,
                    "total_chapters": session.total_chapters
                }
            )
        except Exception as e:
            logger.error(f"发送进度更新失败: {str(e)}")
    
    async def _send_completion_notification(self, session: StoryboardAnalysisSession):
        """发送完成通知"""
        try:
            await self.websocket_manager.broadcast_to_session(
                f"storyboard_analysis_{session.id}",
                {
                    "type": "analysis_completed",
                    "session_id": session.id,
                    "status": session.status
                }
            )
        except Exception as e:
            logger.error(f"发送完成通知失败: {str(e)}")
    
    def get_session(self, session_id: int) -> Optional[StoryboardAnalysisSession]:
        """获取分析会话"""
        return self.db.query(StoryboardAnalysisSession).filter(
            StoryboardAnalysisSession.id == session_id
        ).first()
    
    def get_sessions(
        self,
        book_id: Optional[int] = None,
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 20
    ) -> List[StoryboardAnalysisSession]:
        """获取分析会话列表"""
        query = self.db.query(StoryboardAnalysisSession)
        
        if book_id:
            query = query.filter(StoryboardAnalysisSession.book_id == book_id)
        
        if status:
            query = query.filter(StoryboardAnalysisSession.status == status)
        
        return query.order_by(StoryboardAnalysisSession.created_at.desc()).offset(skip).limit(limit).all()
    
    def get_session_cards(
        self,
        session_id: int,
        card_type: Optional[str] = None,
        chapter_id: Optional[int] = None
    ) -> List[BaseStoryboardCard]:
        """获取会话的卡片"""
        query = self.db.query(BaseStoryboardCard).filter(
            BaseStoryboardCard.session_id == session_id
        )
        
        if card_type:
            query = query.filter(BaseStoryboardCard.card_type == card_type)
        
        if chapter_id:
            query = query.filter(BaseStoryboardCard.chapter_id == chapter_id)
        
        return query.all()
    
    def update_card(self, card_id: int, content: Dict[str, Any]) -> BaseStoryboardCard:
        """更新卡片内容"""
        card = self.db.query(BaseStoryboardCard).filter(
            BaseStoryboardCard.id == card_id
        ).first()
        
        if not card:
            raise ServiceException("卡片不存在")
        
        card.content = content
        card.updated_at = datetime.utcnow()
        self.db.commit()
        
        return card
    
    def confirm_card(self, card_id: int, confirmed_by: str = None) -> BaseStoryboardCard:
        """确认卡片"""
        card = self.db.query(BaseStoryboardCard).filter(
            BaseStoryboardCard.id == card_id
        ).first()
        
        if not card:
            raise ServiceException("卡片不存在")
        
        card.confirm(confirmed_by)
        self.db.commit()
        
        return card
    
    def request_card_reanalysis(self, card_id: int, reason: str) -> BaseStoryboardCard:
        """请求重新分析卡片"""
        card = self.db.query(BaseStoryboardCard).filter(
            BaseStoryboardCard.id == card_id
        ).first()
        
        if not card:
            raise ServiceException("卡片不存在")
        
        card.request_reanalysis(reason)
        self.db.commit()
        
        return card
    
    def confirm_session(self, session_id: int, confirmation_type: str = 'storyboard') -> StoryboardAnalysisSession:
        """确认分析会话"""
        session = self.get_session(session_id)
        if not session:
            raise ServiceException("分析会话不存在")
        
        if confirmation_type == 'book':
            session.confirm_book_level()
        elif confirmation_type == 'storyboard':
            session.confirm_storyboard_level()
        else:
            raise ServiceException("不支持的确认类型")
        
        self.db.commit()
        return session
    
    def delete_session(self, session_id: int) -> bool:
        """删除分析会话"""
        session = self.get_session(session_id)
        if not session:
            raise ServiceException("分析会话不存在")
        
        self.db.delete(session)
        self.db.commit()
        
        return True
