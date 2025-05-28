"""
核心模块
提供应用核心功能的统一导入
"""

from .config import settings
from .database import get_database, get_collection
from .dependencies import dependency_manager, get_db
from .logging import setup_logging
from .queue import task_queue, TaskPriority
from .websocket import websocket_manager, MessageType

__all__ = [
    "settings",
    "get_database",
    "get_collection", 
    "dependency_manager",
    "get_db",
    "setup_logging",
    "task_queue",
    "TaskPriority",
    "websocket_manager",
    "MessageType"
]