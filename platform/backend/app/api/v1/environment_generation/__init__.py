"""
环境音生成API模块
整合所有子模块的路由
"""

from fastapi import APIRouter
from . import analysis, projects, config, generation

# 创建主路由器
router = APIRouter(prefix="/environment-generation", tags=["环境音生成"])

# 包含所有子模块的路由
router.include_router(analysis.router)
router.include_router(projects.router)
router.include_router(config.router)
router.include_router(generation.router)
