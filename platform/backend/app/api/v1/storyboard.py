"""
故事板分析API
基于6类卡片方案的小说转有声读物分析API
"""

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
import json
import logging

logger = logging.getLogger(__name__)

from app.database import get_db
from app.services.storyboard_analysis_service_v2 import StoryboardAnalysisServiceV2
from app.models import StoryboardAnalysisSession, BaseStoryboardCard, Book, BookChapter, AnalysisResult
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
    service = StoryboardAnalysisServiceV2(db)
    
    try:
        session = await service.create_analysis_session(
            book_id=session_data.book_id,
            session_name=session_data.session_name,
            description=session_data.description,
            analysis_type=session_data.analysis_type,
            llm_config=session_data.llm_config,
            analysis_params=session_data.analysis_params
        )
        
        # 获取项目信息以获取book_id
        from app.models.novel_project import NovelProject
        project = db.query(NovelProject).filter(NovelProject.id == session.project_id).first()
        
        # 获取书籍信息
        book_info = None
        if project and project.book_id:
            from app.models import Book
            book = db.query(Book).filter(Book.id == project.book_id).first()
            if book:
                book_info = {
                    "id": book.id,
                    "title": book.title,
                    "author": book.author or "未知作者",
                    "description": book.description
                }
        
        # 返回会话信息，包含所有必需字段
        return {
            "id": session.id,
            "book_id": project.book_id if project else None,
            "book": book_info,
            "session_name": session.session_name,
            "description": session.description,
            "analysis_type": "standard",  # 默认值
            "llm_config": session.llm_config or {},
            "analysis_params": session.analysis_params or {},
            "status": session.status,
            "progress": session.progress,
            "current_step": session.current_step,
            "total_chapters": session.total_chapters,
            "analyzed_chapters": session.completed_chapters,  # 映射字段名
            "failed_chapters": session.failed_chapters,
            "book_confirmed": False,  # 默认值
            "storyboard_confirmed": False,  # 默认值
            "error_message": session.error_message,
            "created_at": session.created_at.isoformat() if session.created_at else None,
            "started_at": session.started_at.isoformat() if session.started_at else None,
            "completed_at": session.completed_at.isoformat() if session.completed_at else None,
            "updated_at": session.updated_at.isoformat() if session.updated_at else None
        }
        
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
    service = StoryboardAnalysisServiceV2(db)
    
    try:
        sessions = service.get_sessions(
            book_id=book_id,
            status=status,
            skip=skip,
            limit=limit
        )
        
        # 获取总数
        from app.models.analysis_session import AnalysisSession
        from app.models.novel_project import NovelProject
        
        total_query = db.query(AnalysisSession)
        if book_id:
            total_query = total_query.join(NovelProject, AnalysisSession.project_id == NovelProject.id)
            total_query = total_query.filter(NovelProject.book_id == book_id)
        if status:
            total_query = total_query.filter(AnalysisSession.status == status)
        total = total_query.count()
        
        # 构建会话响应数据
        session_responses = []
        for session in sessions:
            # 获取项目信息
            project = db.query(NovelProject).filter(NovelProject.id == session.project_id).first()
            
            # 获取书籍信息
            book_info = None
            if project and project.book_id:
                from app.models import Book
                book = db.query(Book).filter(Book.id == project.book_id).first()
                if book:
                    book_info = {
                        "id": book.id,
                        "title": book.title,
                        "author": book.author or "未知作者",
                        "description": book.description
                    }
            
            session_responses.append({
                "id": session.id,
                "book_id": project.book_id if project else None,
                "book": book_info,
                "session_name": session.session_name,
                "description": session.description,
                "analysis_type": "standard",
                "llm_config": session.llm_config or {},
                "analysis_params": session.analysis_params or {},
                "status": session.status,
                "progress": session.progress,
                "current_step": session.current_step,
                "total_chapters": session.total_chapters,
                "analyzed_chapters": session.completed_chapters,
                "failed_chapters": session.failed_chapters,
                "book_confirmed": False,
                "storyboard_confirmed": False,
                "error_message": session.error_message,
                "created_at": session.created_at.isoformat() if session.created_at else None,
                "started_at": session.started_at.isoformat() if session.started_at else None,
                "completed_at": session.completed_at.isoformat() if session.completed_at else None,
                "updated_at": session.updated_at.isoformat() if session.updated_at else None
            })
        
        return {
            "sessions": session_responses,
            "total": total,
            "skip": skip,
            "limit": limit
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取会话列表失败: {str(e)}")


@router.get("/sessions/{session_id}/chapters")
def get_session_chapters(session_id: int, db: Session = Depends(get_db)):
    """
    获取分析会话的章节列表
    """
    try:
        # 获取会话信息
        from app.models.analysis_session import AnalysisSession
        session = db.query(AnalysisSession).filter(AnalysisSession.id == session_id).first()
        if not session:
            raise HTTPException(status_code=404, detail="分析会话不存在")
        
        # 获取项目信息
        from app.models.novel_project import NovelProject
        project = db.query(NovelProject).filter(NovelProject.id == session.project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在")
        
        # 获取书籍的章节列表
        from app.models import BookChapter
        chapters = db.query(BookChapter).filter(
            BookChapter.book_id == project.book_id
        ).order_by(BookChapter.chapter_number).all()
        
        # 构建章节响应数据
        chapter_list = []
        for chapter in chapters:
            chapter_list.append({
                "id": chapter.id,
                "book_id": chapter.book_id,
                "chapter_title": chapter.chapter_title,
                "chapter_number": chapter.chapter_number,
                "content": chapter.content,
                "word_count": chapter.word_count,
                "analysis_status": chapter.analysis_status,
                "created_at": chapter.created_at.isoformat() if chapter.created_at else None,
                "updated_at": chapter.updated_at.isoformat() if chapter.updated_at else None
            })
        
        return {
            "success": True,
            "data": {
                "session_id": session_id,
                "book_id": project.book_id,
                "chapters": chapter_list,
                "total": len(chapter_list)
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取章节列表失败: {str(e)}")


@router.get("/sessions/{session_id}", response_model=StoryboardSessionResponse)
def get_storyboard_session(session_id: int, db: Session = Depends(get_db)):
    """
    获取故事板分析会话详情
    """
    service = StoryboardAnalysisServiceV2(db)
    
    try:
        session = service.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="分析会话不存在")
        
        # 获取项目信息以获取book_id
        from app.models.novel_project import NovelProject
        project = db.query(NovelProject).filter(NovelProject.id == session.project_id).first()
        
        # 获取书籍信息
        book_info = None
        if project and project.book_id:
            from app.models import Book
            book = db.query(Book).filter(Book.id == project.book_id).first()
            if book:
                book_info = {
                    "id": book.id,
                    "title": book.title,
                    "author": book.author or "未知作者",
                    "description": book.description
                }
        
        # 返回会话信息，包含所有必需字段
        return {
            "id": session.id,
            "book_id": project.book_id if project else None,
            "book": book_info,
            "session_name": session.session_name,
            "description": session.description,
            "analysis_type": "standard",  # 默认值
            "llm_config": session.llm_config or {},
            "analysis_params": session.analysis_params or {},
            "status": session.status,
            "progress": session.progress,
            "current_step": session.current_step,
            "total_chapters": session.total_chapters,
            "analyzed_chapters": session.completed_chapters,  # 映射字段名
            "failed_chapters": session.failed_chapters,
            "book_confirmed": False,  # 默认值
            "storyboard_confirmed": False,  # 默认值
            "error_message": session.error_message,
            "created_at": session.created_at.isoformat() if session.created_at else None,
            "started_at": session.started_at.isoformat() if session.started_at else None,
            "completed_at": session.completed_at.isoformat() if session.completed_at else None,
            "updated_at": session.updated_at.isoformat() if session.updated_at else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取会话详情失败: {str(e)}")


@router.post("/sessions/{session_id}/start")
async def start_storyboard_analysis(session_id: int, db: Session = Depends(get_db)):
    """
    开始故事板分析
    """
    service = StoryboardAnalysisServiceV2(db)
    
    try:
        success = await service.start_analysis(session_id)
        if not success:
            raise HTTPException(status_code=400, detail="启动分析失败")
        
        return {"message": "分析已开始", "session_id": session_id}
        
    except ServiceException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"启动分析失败: {str(e)}")


@router.post("/sessions/{session_id}/chapters/{chapter_id}/analyze")
async def analyze_single_chapter(
    session_id: int, 
    chapter_id: int, 
    db: Session = Depends(get_db)
):
    """
    分析单个章节
    """
    service = StoryboardAnalysisServiceV2(db)
    
    try:
        # 获取会话
        session = service.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="会话不存在")
        
        # 获取章节
        chapter = db.query(BookChapter).filter(BookChapter.id == chapter_id).first()
        if not chapter:
            raise HTTPException(status_code=404, detail="章节不存在")
        
        # 检查章节是否属于该会话的书籍
        if chapter.book_id != session.book_id:
            raise HTTPException(status_code=400, detail="章节不属于该会话的书籍")
        
        # 分析单个章节
        await service._analyze_chapter(session, chapter)
        
        return {
            "message": "章节分析完成", 
            "session_id": session_id, 
            "chapter_id": chapter_id,
            "chapter_title": chapter.chapter_title
        }
        
    except ServiceException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"章节分析失败: {str(e)}")


@router.get("/sessions/{session_id}/chapters/{chapter_id}/cards")
async def get_chapter_cards(
    session_id: int, 
    chapter_id: int, 
    db: Session = Depends(get_db)
):
    """
    获取章节的分析卡片
    """
    service = StoryboardAnalysisServiceV2(db)
    
    try:
        cards = service.get_session_cards(session_id, chapter_id)
        
        # 按卡片类型分组
        cards_by_type = {}
        for card in cards:
            if card.card_type not in cards_by_type:
                cards_by_type[card.card_type] = []
            cards_by_type[card.card_type].append(card.to_dict())
        
        return {
            "session_id": session_id,
            "chapter_id": chapter_id,
            "cards": cards_by_type,
            "total_cards": len(cards)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取章节卡片失败: {str(e)}")


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
    service = StoryboardAnalysisServiceV2(db)
    
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
    service = StoryboardAnalysisServiceV2(db)
    
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
    service = StoryboardAnalysisServiceV2(db)
    
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
    service = StoryboardAnalysisServiceV2(db)
    
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
    service = StoryboardAnalysisServiceV2(db)
    
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


@router.post("/sessions/{session_id}/reanalyze")
def reanalyze_session(session_id: int, db: Session = Depends(get_db)):
    """
    重新分析会话
    """
    service = StoryboardAnalysisServiceV2(db)
    
    try:
        success = service.reanalyze_session(session_id)
        if not success:
            raise HTTPException(status_code=400, detail="重新分析会话失败")
        
        return {"message": "会话重新分析已开始", "session_id": session_id}
        
    except ServiceException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"重新分析会话失败: {str(e)}")

# 这些API端点已移除，因为功能已在StoryboardAnalysisService中实现


@router.delete("/sessions/{session_id}")
def delete_session(session_id: int, db: Session = Depends(get_db)):
    """
    删除分析会话
    """
    service = StoryboardAnalysisServiceV2(db)
    
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
    service = StoryboardAnalysisServiceV2(db)
    
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
async def get_storyboard_review_data(session_id: int, chapter_id: int, db: Session = Depends(get_db)):
    """
    获取分镜确认页面的数据
    """
    service = StoryboardAnalysisServiceV2(db)
    
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

        # 获取智能分段数据（如果存在）
        try:
            from app.services.smart_segmentation_service import SmartSegmentationService
            segmentation_service = SmartSegmentationService()
            
            # 添加调试日志
            logger.info(f"🔍 开始获取章节 {chapter_id} 的智能分段数据")
            
            # 先检查数据库中是否有AnalysisResult记录
            analysis_results = db.query(AnalysisResult).filter(
                AnalysisResult.session_id == session_id,
                AnalysisResult.chapter_id == chapter_id
            ).all()
            logger.info(f"🔍 数据库中找到 {len(analysis_results)} 条AnalysisResult记录")
            
            for result in analysis_results:
                logger.info(f"🔍 记录ID: {result.id}, 状态: {result.status}, 有original_analysis: {result.original_analysis is not None}")
                if result.original_analysis:
                    logger.info(f"🔍 original_analysis字段内容: {result.original_analysis}")
            
            segments = await segmentation_service.get_cached_segments(session_id, chapter_id, db)
            logger.info(f"🔍 get_cached_segments返回结果: {segments}")
            
            if segments and len(segments) > 0:
                segmentation_data = {
                    "segments": segments,
                    "segment_count": len(segments),
                    "is_smart_segmented": True
                }
                logger.info(f"章节 {chapter_id} 返回智能分段数据，共 {len(segments)} 段")
            else:
                segmentation_data = None
                logger.info(f"章节 {chapter_id} 未进行智能分段，不返回分段数据")
        except Exception as e:
            logger.warning(f"获取智能分段数据失败: {str(e)}")
            import traceback
            logger.error(f"完整错误堆栈: {traceback.format_exc()}")
            segmentation_data = None

        return {
            "session": session.to_dict(),
            "chapter": {
                "id": chapter.id,
                "title": chapter.chapter_title,
                "content": chapter.content,
                "chapter_number": chapter.chapter_number
            },
            "cards": card_groups,
            "book_cards": book_card_groups,
            "segmentation_data": segmentation_data
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
    service = StoryboardAnalysisServiceV2(db)
    
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

# WebSocket端点
@router.websocket("/ws/{session_id}")
async def storyboard_websocket(websocket: WebSocket, session_id: int):
    """
    故事板分析WebSocket端点
    用于实时接收分析进度更新
    """
    connection_id = f"storyboard_{session_id}"
    
    try:
        await websocket_manager.connect(websocket, connection_id, {
            "session_id": session_id,
            "type": "storyboard_analysis"
        })
        
        # 发送初始状态
        await websocket.send_text(json.dumps({
            "type": "connected",
            "session_id": session_id,
            "message": "WebSocket连接已建立"
        }))
        
        # 保持连接直到客户端断开
        while True:
            try:
                # 等待客户端消息
                data = await websocket.receive_text()
                message = json.loads(data)
                
                # 处理客户端消息
                if message.get("type") == "ping":
                    await websocket.send_text(json.dumps({
                        "type": "pong",
                        "timestamp": message.get("timestamp")
                    }))
                    
            except WebSocketDisconnect:
                break
                
    except WebSocketDisconnect:
        logger.info(f"WebSocket连接断开: {connection_id}")
    except Exception as e:
        logger.error(f"WebSocket错误: {connection_id}, 错误: {e}")
    finally:
        await websocket_manager.disconnect(connection_id)
