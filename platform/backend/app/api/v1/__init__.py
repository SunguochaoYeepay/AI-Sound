"""
API v1版本路由汇总
集成所有v1版本的API路由
"""

from fastapi import APIRouter

from .books import router as books_router
from .chapters import router as chapters_router
from .analysis import router as analysis_router
from .synthesis import router as synthesis_router
from .presets import router as presets_router
from .projects import router as projects_router

# 创建v1版本的主路由
api = APIRouter()

# 注册各模块路由
api.include_router(books_router, tags=["Books"])
api.include_router(chapters_router, tags=["Chapters"])
api.include_router(analysis_router, tags=["Analysis"])
api.include_router(synthesis_router, tags=["Synthesis"])
api.include_router(presets_router, tags=["Presets"])
api.include_router(projects_router, tags=["Projects"]) 