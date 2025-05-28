"""
API模块
提供FastAPI应用和路由的统一管理

包含：
- FastAPI应用创建和配置
- API路由注册
- 中间件配置
- WebSocket支持
- 异常处理
"""

from .app import create_app, app

__all__ = [
    "create_app",
    "app"
]