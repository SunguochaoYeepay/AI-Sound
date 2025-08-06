"""角色管理路由模块"""

from fastapi import APIRouter

from .crud import router as crud_router
from .batch import router as batch_router
from .ai import router as ai_router
from .matching import router as matching_router

# 创建主路由器
router = APIRouter()

# 注册子路由
router.include_router(crud_router, tags=["角色管理-基础CRUD"])
router.include_router(batch_router, tags=["角色管理-批量操作"])
router.include_router(ai_router, tags=["角色管理-AI功能"])
router.include_router(matching_router, tags=["角色管理-匹配功能"])

__all__ = ["router"]