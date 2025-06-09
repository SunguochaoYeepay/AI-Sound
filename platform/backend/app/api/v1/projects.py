"""
项目管理API
提供TTS项目管理功能
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database import get_db
from app.models import NovelProject

router = APIRouter(prefix="/projects")


@router.post("/")
async def create_project():
    """创建项目"""
    pass


@router.get("/")
def get_projects():
    """获取项目列表"""
    pass


@router.get("/{project_id}")
def get_project():
    """获取项目详情"""
    pass


@router.patch("/{project_id}")
def update_project():
    """更新项目信息"""
    pass


@router.delete("/{project_id}")
def delete_project():
    """删除项目"""
    pass 