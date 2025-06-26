"""
音频合成API
提供TTS音频合成功能
"""

from fastapi import APIRouter, Depends, HTTPException, WebSocket
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database import get_db
# from app.services import SynthesisService  # 🚀 新架构已废弃
# from app.models import SynthesisTask  # 🚀 新架构已废弃

router = APIRouter(prefix="/synthesis")


@router.post("/tasks")
async def create_synthesis_task():
    """创建合成任务"""
    pass


@router.get("/tasks")
def get_synthesis_tasks():
    """获取合成任务列表"""
    pass


@router.post("/tasks/{task_id}/start")
async def start_synthesis_task():
    """启动合成任务"""
    pass


@router.websocket("/tasks/{task_id}/ws")
async def synthesis_progress_websocket():
    """WebSocket实时进度推送"""
    pass 