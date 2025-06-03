"""
WebSocket实时通信模块
提供实时通知和进度推送
"""

import asyncio
import json
from datetime import datetime
from typing import Dict, List, Set, Any, Optional
from enum import Enum
import logging

from fastapi import WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)


class MessageType(str, Enum):
    """消息类型"""
    TASK_PROGRESS = "task_progress"
    TASK_COMPLETED = "task_completed"
    TASK_FAILED = "task_failed"
    ENGINE_STATUS = "engine_status"
    SYSTEM_STATUS = "system_status"
    NOTIFICATION = "notification"


class NotificationLevel(str, Enum):
    """通知级别"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    SUCCESS = "success"


class WebSocketManager:
    """WebSocket连接管理器"""
    
    def __init__(self):
        # 活跃连接
        self._connections: Dict[str, WebSocket] = {}
        # 订阅关系：连接ID -> 订阅的消息类型集合
        self._subscriptions: Dict[str, Set[MessageType]] = {}
        # 房间订阅：连接ID -> 房间名称集合
        self._rooms: Dict[str, Set[str]] = {}
        # 房间成员：房间名称 -> 连接ID集合
        self._room_members: Dict[str, Set[str]] = {}
    
    async def connect(self, websocket: WebSocket, client_id: str) -> None:
        """接受WebSocket连接"""
        await websocket.accept()
        self._connections[client_id] = websocket
        self._subscriptions[client_id] = set()
        self._rooms[client_id] = set()
        
        logger.info(f"WebSocket客户端已连接: {client_id}")
        
        # 发送连接成功消息
        await self.send_to_client(client_id, {
            "type": "connection",
            "status": "connected",
            "client_id": client_id,
            "timestamp": datetime.now().isoformat()
        })
    
    async def disconnect(self, client_id: str) -> None:
        """断开WebSocket连接"""
        # 从所有房间移除
        if client_id in self._rooms:
            for room in list(self._rooms[client_id]):
                await self.leave_room(client_id, room)
        
        # 清理连接信息
        self._connections.pop(client_id, None)
        self._subscriptions.pop(client_id, None)
        self._rooms.pop(client_id, None)
        
        logger.info(f"WebSocket客户端已断开: {client_id}")
    
    async def send_to_client(self, client_id: str, message: Dict[str, Any]) -> bool:
        """向指定客户端发送消息"""
        websocket = self._connections.get(client_id)
        if not websocket:
            return False
        
        try:
            await websocket.send_text(json.dumps(message, ensure_ascii=False))
            return True
        except Exception as e:
            logger.error(f"发送消息失败 {client_id}: {e}")
            await self.disconnect(client_id)
            return False
    
    async def broadcast(self, message: Dict[str, Any], message_type: Optional[MessageType] = None) -> int:
        """广播消息给所有订阅的客户端"""
        sent_count = 0
        
        for client_id in list(self._connections.keys()):
            # 检查是否订阅了该消息类型
            if message_type and message_type not in self._subscriptions.get(client_id, set()):
                continue
            
            if await self.send_to_client(client_id, message):
                sent_count += 1
        
        return sent_count
    
    async def send_to_room(self, room: str, message: Dict[str, Any]) -> int:
        """向房间内所有客户端发送消息"""
        sent_count = 0
        room_members = self._room_members.get(room, set())
        
        for client_id in list(room_members):
            if await self.send_to_client(client_id, message):
                sent_count += 1
        
        return sent_count
    
    async def subscribe(self, client_id: str, message_types: List[MessageType]) -> bool:
        """订阅消息类型"""
        if client_id not in self._connections:
            return False
        
        self._subscriptions[client_id].update(message_types)
        logger.info(f"客户端 {client_id} 订阅消息类型: {message_types}")
        return True
    
    async def unsubscribe(self, client_id: str, message_types: List[MessageType]) -> bool:
        """取消订阅消息类型"""
        if client_id not in self._connections:
            return False
        
        self._subscriptions[client_id].difference_update(message_types)
        logger.info(f"客户端 {client_id} 取消订阅消息类型: {message_types}")
        return True
    
    async def join_room(self, client_id: str, room: str) -> bool:
        """加入房间"""
        if client_id not in self._connections:
            return False
        
        self._rooms[client_id].add(room)
        if room not in self._room_members:
            self._room_members[room] = set()
        self._room_members[room].add(client_id)
        
        logger.info(f"客户端 {client_id} 加入房间: {room}")
        return True
    
    async def leave_room(self, client_id: str, room: str) -> bool:
        """离开房间"""
        if client_id not in self._connections:
            return False
        
        self._rooms[client_id].discard(room)
        if room in self._room_members:
            self._room_members[room].discard(client_id)
            # 如果房间为空，删除房间
            if not self._room_members[room]:
                del self._room_members[room]
        
        logger.info(f"客户端 {client_id} 离开房间: {room}")
        return True
    
    async def send_task_progress(self, task_id: str, progress: float, message: str = "") -> int:
        """发送任务进度消息"""
        message_data = {
            "type": MessageType.TASK_PROGRESS,
            "task_id": task_id,
            "progress": progress,
            "message": message,
            "timestamp": datetime.now().isoformat()
        }
        return await self.broadcast(message_data, MessageType.TASK_PROGRESS)
    
    async def send_task_completed(self, task_id: str, result: Any = None) -> int:
        """发送任务完成消息"""
        message_data = {
            "type": MessageType.TASK_COMPLETED,
            "task_id": task_id,
            "result": result,
            "timestamp": datetime.now().isoformat()
        }
        return await self.broadcast(message_data, MessageType.TASK_COMPLETED)
    
    async def send_task_failed(self, task_id: str, error: str) -> int:
        """发送任务失败消息"""
        message_data = {
            "type": MessageType.TASK_FAILED,
            "task_id": task_id,
            "error": error,
            "timestamp": datetime.now().isoformat()
        }
        return await self.broadcast(message_data, MessageType.TASK_FAILED)
    
    async def send_notification(
        self,
        title: str,
        content: str,
        level: NotificationLevel = NotificationLevel.INFO,
        room: Optional[str] = None
    ) -> int:
        """发送通知消息"""
        message_data = {
            "type": MessageType.NOTIFICATION,
            "title": title,
            "content": content,
            "level": level,
            "timestamp": datetime.now().isoformat()
        }
        
        if room:
            return await self.send_to_room(room, message_data)
        else:
            return await self.broadcast(message_data, MessageType.NOTIFICATION)
    
    def get_stats(self) -> Dict[str, Any]:
        """获取WebSocket统计信息"""
        return {
            "total_connections": len(self._connections),
            "total_rooms": len(self._room_members),
            "active_subscriptions": sum(len(subs) for subs in self._subscriptions.values()),
            "connections": list(self._connections.keys()),
            "rooms": {room: list(members) for room, members in self._room_members.items()}
        }


# 全局WebSocket管理器实例
websocket_manager = WebSocketManager()