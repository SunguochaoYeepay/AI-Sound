"""
API路由包
包含所有RESTful API接口定义
"""

from fastapi import APIRouter
from .v1 import api as api_v1

# 创建主API路由器
api_router = APIRouter()

# 注册v1版本API
api_router.include_router(api_v1, prefix="/v1")

__all__ = ['api_router', 'api_v1'] 