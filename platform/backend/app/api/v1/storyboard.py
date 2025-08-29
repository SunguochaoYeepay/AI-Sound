"""
故事板分析API
基于6类卡片方案的小说转有声读物分析API
"""

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
import json

from app.database import get_db
from app.services.storyboard_analysis_service import StoryboardAnalysisService
from app.models import StoryboardAnalysisSession, BaseStoryboardCard, Book, BookChapter
from app.schemas.storyboard import (
    StoryboardSessionCreate, StoryboardSessionResponse, StoryboardSessionList,
    StoryboardCardResponse, StoryboardCardUpdate, StoryboardConfirmation
)
from app.utils.exceptions import ServiceException
from app.websocket.manager import websocket_manager

router = APIRouter(prefix="/storyboard")


@router.post("/sessions", response_model=StoryboardSessionResponse)
async def create_storyboard_session(
    session_data: StoryboardSessionCreate,
    db: Session = Depends(get_db)
):
    """
    创建新的故事板分析会话
    """
    service = StoryboardAnalysisService(db)
    
    try:
        session = await service.create_analysis_session(
            book_id=session_data.book_id,
            session_name=session_data.session_name,
            description=session_data.description,
            analysis_type=session_data.analysis_type,
            llm_config=session_data.llm_config,
            analysis_params=session_data.analysis_params
        )
        
        return session.to_dict()
        
    except ServiceException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建分析会话失败: {str(e)}")


@router.get("/sessions", response_model=StoryboardSessionList)
def get_storyboard_sessions(
    book_id: Optional[int] = None,
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """
    获取故事板分析会话列表
    """
    service = StoryboardAnalysisService(db)
    
    try:
        sessions = service.get_sessions(
            book_id=book_id,
            status=status,
            skip=skip,
            limit=limit
        )
        
        # 获取总数
        total_query = db.query(StoryboardAnalysisSession)
        if book_id:
            total_query = total_query.filter(StoryboardAnalysisSession.book_id == book_id)
        if status:
            total_query = total_query.filter(StoryboardAnalysisSession.status == status)
        total = total_query.count()
        
        return {
            "sessions": [session.to_dict() for session in sessions],
            "total": total,
            "skip": skip,
            "limit": limit
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取会话列表失败: {str(e)}")


@router.get("/sessions/{session_id}", response_model=StoryboardSessionResponse)
def get_storyboard_session(session_id: int, db: Session = Depends(get_db)):
    """
    获取故事板分析会话详情
    """
    service = StoryboardAnalysisService(db)
    
    try:
        session = service.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="分析会话不存在")
        
        return session.to_dict()
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取会话详情失败: {str(e)}")


@router.post("/sessions/{session_id}/start")
async def start_storyboard_analysis(session_id: int, db: Session = Depends(get_db)):
    """
    开始故事板分析
    """
    service = StoryboardAnalysisService(db)
    
    try:
        success = await service.start_analysis(session_id)
        if not success:
            raise HTTPException(status_code=400, detail="启动分析失败")
        
        return {"message": "分析已开始", "session_id": session_id}
        
    except ServiceException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"启动分析失败: {str(e)}")


@router.get("/sessions/{session_id}/cards", response_model=List[StoryboardCardResponse])
def get_session_cards(
    session_id: int,
    card_type: Optional[str] = None,
    chapter_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """
    获取会话的卡片列表
    """
    service = StoryboardAnalysisService(db)
    
    try:
        cards = service.get_session_cards(
            session_id=session_id,
            card_type=card_type,
            chapter_id=chapter_id
        )
        
        return [card.to_dict() for card in cards]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取卡片列表失败: {str(e)}")


@router.put("/cards/{card_id}", response_model=StoryboardCardResponse)
def update_card(
    card_id: int,
    card_data: StoryboardCardUpdate,
    db: Session = Depends(get_db)
):
    """
    更新卡片内容
    """
    service = StoryboardAnalysisService(db)
    
    try:
        card = service.update_card(card_id, card_data.content)
        return card.to_dict()
        
    except ServiceException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新卡片失败: {str(e)}")


@router.post("/cards/{card_id}/confirm")
def confirm_card(
    card_id: int,
    confirmation: StoryboardConfirmation,
    db: Session = Depends(get_db)
):
    """
    确认卡片
    """
    service = StoryboardAnalysisService(db)
    
    try:
        card = service.confirm_card(card_id, confirmation.confirmed_by)
        return {"message": "卡片已确认", "card_id": card_id}
        
    except ServiceException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"确认卡片失败: {str(e)}")


@router.post("/cards/{card_id}/reanalyze")
def request_card_reanalysis(
    card_id: int,
    reanalysis: StoryboardConfirmation,
    db: Session = Depends(get_db)
):
    """
    请求重新分析卡片
    """
    service = StoryboardAnalysisService(db)
    
    try:
        card = service.request_card_reanalysis(card_id, reanalysis.confirmed_by)
        return {"message": "已请求重新分析", "card_id": card_id}
        
    except ServiceException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"请求重新分析失败: {str(e)}")


@router.post("/sessions/{session_id}/confirm")
def confirm_session(
    session_id: int,
    confirmation: StoryboardConfirmation,
    db: Session = Depends(get_db)
):
    """
    确认分析会话
    """
    service = StoryboardAnalysisService(db)
    
    try:
        session = service.confirm_session(
            session_id=session_id,
            confirmation_type=confirmation.confirmation_type or 'storyboard'
        )
        return {"message": "会话已确认", "session_id": session_id}
        
    except ServiceException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"确认会话失败: {str(e)}")


@router.delete("/sessions/{session_id}")
def delete_session(session_id: int, db: Session = Depends(get_db)):
    """
    删除分析会话
    """
    service = StoryboardAnalysisService(db)
    
    try:
        success = service.delete_session(session_id)
        if not success:
            raise HTTPException(status_code=400, detail="删除会话失败")
        
        return {"message": "会话已删除", "session_id": session_id}
        
    except ServiceException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除会话失败: {str(e)}")


@router.get("/sessions/{session_id}/chapters")
def get_session_chapters(session_id: int, db: Session = Depends(get_db)):
    """
    获取会话的章节列表
    """
    service = StoryboardAnalysisService(db)
    
    try:
        session = service.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="分析会话不存在")
        
        # 获取书籍和章节
        book = db.query(Book).filter(Book.id == session.book_id).first()
        if not book:
            raise HTTPException(status_code=404, detail="书籍不存在")
        
        chapters = db.query(BookChapter).filter(
            BookChapter.book_id == session.book_id
        ).order_by(BookChapter.chapter_number).all()
        
        # 构建章节列表
        chapter_list = []
        for chapter in chapters:
            # 获取该章节的卡片数量
            cards = service.get_session_cards(
                session_id=session_id,
                chapter_id=chapter.id
            )
            
            chapter_data = {
                'chapter_id': chapter.id,
                'chapter_title': chapter.chapter_title,
                'chapter_number': chapter.chapter_number,
                'word_count': len(chapter.content) if chapter.content else 0,
                'analysis_status': 'completed' if cards else 'pending',
                'analysis_progress': 100 if cards else 0,
                'card_count': len(cards),
                'story_card': any(card.card_type == 'story' for card in cards),
                'character_cards': [card.to_dict() for card in cards if card.card_type == 'character'],
                'scene_cards': [card.to_dict() for card in cards if card.card_type == 'scene'],
                'event_cards': [card.to_dict() for card in cards if card.card_type == 'event'],
                'emotion_cards': [card.to_dict() for card in cards if card.card_type == 'emotion'],
                'storyboard_card': any(card.card_type == 'audio_storyboard' for card in cards)
            }
            chapter_list.append(chapter_data)
        
        return {
            "session_id": session_id,
            "chapters": chapter_list
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取章节列表失败: {str(e)}")


@router.get("/review/{session_id}/{chapter_id}")
def get_storyboard_review_data(session_id: int, chapter_id: int, db: Session = Depends(get_db)):
    """
    获取分镜确认页面的数据
    """
    service = StoryboardAnalysisService(db)
    
    try:
        # 获取会话
        session = service.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="分析会话不存在")
        
        # 获取章节
        chapter = db.query(BookChapter).filter(BookChapter.id == chapter_id).first()
        if not chapter:
            raise HTTPException(status_code=404, detail="章节不存在")
        
        # 获取所有相关卡片
        cards = service.get_session_cards(
            session_id=session_id,
            chapter_id=chapter_id
        )
        
        # 按类型分组卡片
        card_groups = {}
        for card in cards:
            if card.card_type not in card_groups:
                card_groups[card.card_type] = []
            card_groups[card.card_type].append(card.to_dict())
        
        # 获取书籍级卡片
        book_cards = service.get_session_cards(
            session_id=session_id,
            chapter_id=None  # 书籍级卡片没有章节ID
        )
        
        book_card_groups = {}
        for card in book_cards:
            if card.card_type not in book_card_groups:
                book_card_groups[card.card_type] = []
            book_card_groups[card.card_type].append(card.to_dict())
        
        return {
            "session": session.to_dict(),
            "chapter": {
                "id": chapter.id,
                "title": chapter.chapter_title,
                "content": chapter.content,
                "chapter_number": chapter.chapter_number
            },
            "cards": card_groups,
            "book_cards": book_card_groups
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取确认数据失败: {str(e)}")


@router.post("/review/{session_id}/{chapter_id}/confirm")
def confirm_storyboard(session_id: int, chapter_id: int, db: Session = Depends(get_db)):
    """
    确认分镜
    """
    service = StoryboardAnalysisService(db)
    
    try:
        # 确认该章节的所有卡片
        cards = service.get_session_cards(
            session_id=session_id,
            chapter_id=chapter_id
        )
        
        for card in cards:
            if card.confirmation_status == 'pending':
                service.confirm_card(card.id)
        
        return {"message": "分镜已确认", "session_id": session_id, "chapter_id": chapter_id}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"确认分镜失败: {str(e)}")


# WebSocket连接用于实时进度更新
@router.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: int):
    """
    WebSocket连接用于实时进度更新
    """
    await websocket.accept()
    
    try:
        # 加入会话房间
        await websocket_manager.join_session(f"storyboard_analysis_{session_id}", websocket)
        
        # 保持连接
        while True:
            data = await websocket.receive_text()
            # 处理客户端消息（如果需要）
            
    except WebSocketDisconnect:
        # 离开会话房间
        await websocket_manager.leave_session(f"storyboard_analysis_{session_id}", websocket)
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"WebSocket错误: {str(e)}")
        await websocket.close()
