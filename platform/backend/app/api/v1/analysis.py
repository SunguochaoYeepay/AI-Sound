"""
智能分析API
提供LLM智能分析功能
"""

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
import asyncio
import json

from app.database import get_db
from app.services import AnalysisService
from app.models import AnalysisSession, AnalysisResult, Book, NovelProject
from app.schemas import (
    AnalysisSessionResponse, AnalysisSessionCreate,
    AnalysisResultResponse, AnalysisConfigUpdate
)
from app.utils.exceptions import (
    AnalysisSessionNotFoundError, AnalysisConfigError, LLMServiceError
)
from app.websocket.manager import WebSocketManager

router = APIRouter(prefix="/analysis")
websocket_manager = WebSocketManager()


@router.post("/sessions", response_model=AnalysisSessionResponse)
async def create_analysis_session(
    session_data: AnalysisSessionCreate,
    db: Session = Depends(get_db)
):
    """
    创建新的分析会话
    - 支持全书、单章、章节范围分析
    - 配置LLM参数和分析选项
    """
    analysis_service = AnalysisService(db)
    
    try:
        # 验证项目是否存在
        project = db.query(NovelProject).filter(
            NovelProject.id == session_data.project_id
        ).first()
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在")
        
        # 创建分析会话
        session = await analysis_service.create_analysis_session(
            project_id=session_data.project_id,
            session_name=session_data.session_name,
            description=session_data.description,
            target_type=session_data.target_type,
            target_config=session_data.target_config,
            llm_config=session_data.llm_config,
            analysis_params=session_data.analysis_params
        )
        
        return session.to_dict()
        
    except AnalysisConfigError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建分析会话失败: {str(e)}")


@router.get("/sessions", response_model=List[AnalysisSessionResponse])
def get_analysis_sessions(
    project_id: Optional[int] = None,
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """
    获取分析会话列表
    - 支持按项目筛选
    - 支持按状态筛选
    """
    query = db.query(AnalysisSession)
    
    if project_id:
        query = query.filter(AnalysisSession.project_id == project_id)
    
    if status:
        query = query.filter(AnalysisSession.status == status)
    
    sessions = query.order_by(AnalysisSession.created_at.desc()).offset(skip).limit(limit).all()
    return [session.to_dict() for session in sessions]


@router.get("/sessions/{session_id}", response_model=AnalysisSessionResponse)
def get_analysis_session(session_id: int, db: Session = Depends(get_db)):
    """获取分析会话详情"""
    session = db.query(AnalysisSession).filter(AnalysisSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="分析会话不存在")
    
    return session.to_dict()


@router.post("/sessions/{session_id}/start")
async def start_analysis_session(
    session_id: int,
    force_restart: bool = False,
    db: Session = Depends(get_db)
):
    """
    启动分析会话
    - 支持强制重启
    - 返回任务状态
    """
    analysis_service = AnalysisService(db)
    
    try:
        session = db.query(AnalysisSession).filter(AnalysisSession.id == session_id).first()
        if not session:
            raise AnalysisSessionNotFoundError(f"分析会话 {session_id} 不存在")
        
        # 检查是否可以启动
        if session.is_active() and not force_restart:
            return {
                "message": "分析会话正在运行中",
                "session_id": session_id,
                "status": session.status,
                "progress": session.progress
            }
        
        if session.is_completed() and not force_restart:
            return {
                "message": "分析会话已完成，使用 force_restart=true 重新运行",
                "session_id": session_id,
                "status": session.status,
                "completed_chapters": session.completed_chapters
            }
        
        # 启动分析任务
        task_id = await analysis_service.start_analysis_session(
            session_id=session_id,
            force_restart=force_restart
        )
        
        return {
            "message": "分析会话已启动",
            "session_id": session_id,
            "task_id": task_id
        }
        
    except AnalysisSessionNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except LLMServiceError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"启动分析失败: {str(e)}")


@router.post("/sessions/{session_id}/stop")
async def stop_analysis_session(session_id: int, db: Session = Depends(get_db)):
    """停止分析会话"""
    analysis_service = AnalysisService(db)
    
    try:
        result = await analysis_service.stop_analysis_session(session_id)
        return {
            "message": "分析会话已停止",
            "session_id": session_id,
            "stopped": result
        }
        
    except AnalysisSessionNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"停止分析失败: {str(e)}")


@router.get("/sessions/{session_id}/results", response_model=List[AnalysisResultResponse])
def get_analysis_results(
    session_id: int,
    skip: int = 0,
    limit: int = 50,
    status_filter: Optional[str] = None,
    include_raw: bool = False,
    db: Session = Depends(get_db)
):
    """
    获取分析结果列表
    - 支持分页查询
    - 支持状态筛选
    - 可选择是否包含原始数据
    """
    # 检查会话是否存在
    session = db.query(AnalysisSession).filter(AnalysisSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="分析会话不存在")
    
    query = db.query(AnalysisResult).filter(AnalysisResult.session_id == session_id)
    
    if status_filter:
        query = query.filter(AnalysisResult.status == status_filter)
    
    results = query.order_by(AnalysisResult.chapter_id).offset(skip).limit(limit).all()
    return [result.to_dict(include_raw=include_raw) for result in results]


@router.get("/results/{result_id}", response_model=AnalysisResultResponse)
def get_analysis_result(
    result_id: int,
    include_raw: bool = False,
    db: Session = Depends(get_db)
):
    """获取分析结果详情"""
    result = db.query(AnalysisResult).filter(AnalysisResult.id == result_id).first()
    if not result:
        raise HTTPException(status_code=404, detail="分析结果不存在")
    
    return result.to_dict(include_raw=include_raw)


@router.patch("/results/{result_id}")
def update_analysis_result(
    result_id: int,
    config_update: AnalysisConfigUpdate,
    db: Session = Depends(get_db)
):
    """
    用户修改分析结果
    - 修改角色声音映射
    - 调整合成参数
    - 添加/删除角色
    """
    result = db.query(AnalysisResult).filter(AnalysisResult.id == result_id).first()
    if not result:
        raise HTTPException(status_code=404, detail="分析结果不存在")
    
    try:
        # 添加用户修改记录
        for modification in config_update.modifications:
            result.add_user_modification(
                modification_type=modification.type,
                data=modification.data,
                user_id=config_update.user_id
            )
        
        db.commit()
        db.refresh(result)
        
        return {
            "message": "分析结果已更新",
            "result_id": result_id,
            "modification_count": len(config_update.modifications)
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"更新分析结果失败: {str(e)}")


@router.post("/results/{result_id}/confirm")
def confirm_analysis_result(
    result_id: int,
    user_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """用户确认分析结果"""
    result = db.query(AnalysisResult).filter(AnalysisResult.id == result_id).first()
    if not result:
        raise HTTPException(status_code=404, detail="分析结果不存在")
    
    if result.is_user_confirmed:
        return {
            "message": "分析结果已经确认",
            "confirmed_at": result.confirmed_at.isoformat()
        }
    
    try:
        result.confirm_by_user(user_id)
        db.commit()
        
        return {
            "message": "分析结果已确认",
            "result_id": result_id,
            "confirmed_at": result.confirmed_at.isoformat()
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"确认分析结果失败: {str(e)}")


@router.get("/sessions/{session_id}/progress")
def get_analysis_progress(session_id: int, db: Session = Depends(get_db)):
    """获取分析进度详情"""
    session = db.query(AnalysisSession).filter(AnalysisSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="分析会话不存在")
    
    # 统计结果状态
    result_stats = db.query(AnalysisResult.status, 
                           db.func.count(AnalysisResult.id).label('count')) \
                     .filter(AnalysisResult.session_id == session_id) \
                     .group_by(AnalysisResult.status) \
                     .all()
    
    status_counts = {stat.status: stat.count for stat in result_stats}
    
    return {
        "session_id": session_id,
        "status": session.status,
        "progress": session.progress,
        "current_step": session.current_step,
        "total_chapters": session.total_chapters,
        "completed_chapters": session.completed_chapters,
        "failed_chapters": session.failed_chapters,
        "result_status_counts": status_counts,
        "duration": session.get_duration(),
        "error_message": session.error_message
    }


@router.websocket("/sessions/{session_id}/ws")
async def analysis_progress_websocket(websocket: WebSocket, session_id: int):
    """
    WebSocket实时进度推送
    - 实时推送分析进度
    - 推送结果更新
    - 推送错误信息
    """
    await websocket_manager.connect(websocket, f"analysis_session_{session_id}")
    
    try:
        while True:
            # 保持连接活跃
            await asyncio.sleep(1)
            
    except WebSocketDisconnect:
        websocket_manager.disconnect(websocket, f"analysis_session_{session_id}") 