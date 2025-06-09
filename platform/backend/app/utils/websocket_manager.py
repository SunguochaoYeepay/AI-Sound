"""
WebSocket实时通信管理器
处理实时进度更新、状态推送、用户通知等功能
"""

import json
import asyncio
import logging
from typing import Dict, List, Any, Optional, Set
from datetime import datetime
from dataclasses import dataclass, asdict
from fastapi import WebSocket, WebSocketDisconnect
from collections import defaultdict


logger = logging.getLogger(__name__)


@dataclass
class ProgressUpdate:
    """进度更新数据类"""
    session_id: str
    type: str  # 'analysis', 'synthesis', 'chapter_detection', etc.
    status: str
    progress: int  # 0-100
    message: str
    data: Dict[str, Any]
    timestamp: str
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class UserNotification:
    """用户通知数据类"""
    id: str
    type: str  # 'info', 'warning', 'error', 'success'
    title: str
    message: str
    duration: int = 5000  # 显示时长(毫秒)
    actions: List[Dict[str, Any]] = None
    timestamp: str = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow().isoformat()
        if self.actions is None:
            self.actions = []
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class WebSocketConnection:
    """WebSocket连接管理类"""
    
    def __init__(self, websocket: WebSocket, user_id: str = None):
        self.websocket = websocket
        self.user_id = user_id or "anonymous"
        self.connection_id = f"{self.user_id}_{id(websocket)}"
        self.subscriptions: Set[str] = set()  # 订阅的会话ID
        self.connected_at = datetime.utcnow()
        self.last_activity = datetime.utcnow()
        
    async def send_message(self, message: Dict[str, Any]):
        """发送消息"""
        try:
            await self.websocket.send_text(json.dumps(message))
            self.last_activity = datetime.utcnow()
        except Exception as e:
            logger.error(f"发送WebSocket消息失败: {str(e)}")
            raise
    
    async def send_progress_update(self, update: ProgressUpdate):
        """发送进度更新"""
        message = {
            "type": "progress_update",
            "data": update.to_dict()
        }
        await self.send_message(message)
    
    async def send_notification(self, notification: UserNotification):
        """发送用户通知"""
        message = {
            "type": "notification",
            "data": notification.to_dict()
        }
        await self.send_message(message)
    
    def subscribe(self, session_id: str):
        """订阅会话更新"""
        self.subscriptions.add(session_id)
    
    def unsubscribe(self, session_id: str):
        """取消订阅会话更新"""
        self.subscriptions.discard(session_id)
    
    def is_subscribed(self, session_id: str) -> bool:
        """检查是否订阅了指定会话"""
        return session_id in self.subscriptions


class ProgressWebSocketManager:
    """WebSocket进度管理器"""
    
    def __init__(self):
        # 活跃连接: connection_id -> WebSocketConnection
        self.active_connections: Dict[str, WebSocketConnection] = {}
        
        # 会话订阅: session_id -> set of connection_ids
        self.session_subscribers: Dict[str, Set[str]] = defaultdict(set)
        
        # 用户连接: user_id -> set of connection_ids
        self.user_connections: Dict[str, Set[str]] = defaultdict(set)
        
        # 锁保护并发访问
        self._lock = asyncio.Lock()
        
        # 心跳检测任务
        self._heartbeat_task = None
        self._start_heartbeat()
    
    def _start_heartbeat(self):
        """启动心跳检测"""
        if self._heartbeat_task is None:
            self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())
    
    async def _heartbeat_loop(self):
        """心跳检测循环"""
        while True:
            try:
                await asyncio.sleep(30)  # 每30秒检测一次
                await self._cleanup_stale_connections()
            except Exception as e:
                logger.error(f"心跳检测失败: {str(e)}")
    
    async def _cleanup_stale_connections(self):
        """清理失效连接"""
        async with self._lock:
            stale_connections = []
            current_time = datetime.utcnow()
            
            for connection_id, connection in self.active_connections.items():
                # 检查连接是否超时（5分钟无活动）
                if (current_time - connection.last_activity).total_seconds() > 300:
                    stale_connections.append(connection_id)
            
            for connection_id in stale_connections:
                await self._remove_connection(connection_id)
                logger.info(f"清理失效连接: {connection_id}")
    
    async def connect(self, websocket: WebSocket, user_id: str = None) -> WebSocketConnection:
        """建立WebSocket连接"""
        connection = WebSocketConnection(websocket, user_id)
        
        async with self._lock:
            self.active_connections[connection.connection_id] = connection
            self.user_connections[connection.user_id].add(connection.connection_id)
        
        logger.info(f"WebSocket连接建立: {connection.connection_id}")
        
        # 发送连接确认消息
        await connection.send_message({
            "type": "connection_established",
            "data": {
                "connection_id": connection.connection_id,
                "user_id": connection.user_id,
                "timestamp": connection.connected_at.isoformat()
            }
        })
        
        return connection
    
    async def disconnect(self, connection_id: str):
        """断开WebSocket连接"""
        async with self._lock:
            await self._remove_connection(connection_id)
        
        logger.info(f"WebSocket连接断开: {connection_id}")
    
    async def _remove_connection(self, connection_id: str):
        """移除连接（内部方法，需要锁保护）"""
        connection = self.active_connections.pop(connection_id, None)
        if not connection:
            return
        
        # 从用户连接中移除
        self.user_connections[connection.user_id].discard(connection_id)
        if not self.user_connections[connection.user_id]:
            del self.user_connections[connection.user_id]
        
        # 从所有订阅中移除
        for session_id in connection.subscriptions:
            self.session_subscribers[session_id].discard(connection_id)
            if not self.session_subscribers[session_id]:
                del self.session_subscribers[session_id]
    
    async def subscribe_to_session(self, connection_id: str, session_id: str):
        """订阅会话更新"""
        async with self._lock:
            connection = self.active_connections.get(connection_id)
            if connection:
                connection.subscribe(session_id)
                self.session_subscribers[session_id].add(connection_id)
                
                # 发送订阅确认
                await connection.send_message({
                    "type": "subscription_confirmed",
                    "data": {
                        "session_id": session_id,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                })
    
    async def unsubscribe_from_session(self, connection_id: str, session_id: str):
        """取消订阅会话更新"""
        async with self._lock:
            connection = self.active_connections.get(connection_id)
            if connection:
                connection.unsubscribe(session_id)
                self.session_subscribers[session_id].discard(connection_id)
                
                if not self.session_subscribers[session_id]:
                    del self.session_subscribers[session_id]
    
    async def send_progress_update(self, session_id: str, data: Dict[str, Any]):
        """发送进度更新到订阅的连接"""
        update = ProgressUpdate(
            session_id=session_id,
            type=data.get("type", "unknown"),
            status=data.get("status", "unknown"),
            progress=data.get("progress", 0),
            message=data.get("current_processing", ""),
            data=data,
            timestamp=data.get("timestamp", datetime.utcnow().isoformat())
        )
        
        async with self._lock:
            subscriber_ids = self.session_subscribers.get(session_id, set()).copy()
        
        # 并发发送给所有订阅者
        send_tasks = []
        for connection_id in subscriber_ids:
            connection = self.active_connections.get(connection_id)
            if connection:
                send_tasks.append(self._safe_send_progress_update(connection, update))
        
        if send_tasks:
            await asyncio.gather(*send_tasks, return_exceptions=True)
    
    async def _safe_send_progress_update(self, connection: WebSocketConnection, update: ProgressUpdate):
        """安全发送进度更新（捕获异常）"""
        try:
            await connection.send_progress_update(update)
        except Exception as e:
            logger.error(f"发送进度更新失败 {connection.connection_id}: {str(e)}")
            # 连接可能已断开，标记为待清理
            await self.disconnect(connection.connection_id)
    
    async def send_notification_to_user(self, user_id: str, notification: UserNotification):
        """发送通知给指定用户的所有连接"""
        async with self._lock:
            connection_ids = self.user_connections.get(user_id, set()).copy()
        
        send_tasks = []
        for connection_id in connection_ids:
            connection = self.active_connections.get(connection_id)
            if connection:
                send_tasks.append(self._safe_send_notification(connection, notification))
        
        if send_tasks:
            await asyncio.gather(*send_tasks, return_exceptions=True)
    
    async def _safe_send_notification(self, connection: WebSocketConnection, notification: UserNotification):
        """安全发送通知（捕获异常）"""
        try:
            await connection.send_notification(notification)
        except Exception as e:
            logger.error(f"发送通知失败 {connection.connection_id}: {str(e)}")
            await self.disconnect(connection.connection_id)
    
    async def broadcast_notification(self, notification: UserNotification):
        """广播通知给所有连接"""
        async with self._lock:
            connection_ids = list(self.active_connections.keys())
        
        send_tasks = []
        for connection_id in connection_ids:
            connection = self.active_connections.get(connection_id)
            if connection:
                send_tasks.append(self._safe_send_notification(connection, notification))
        
        if send_tasks:
            await asyncio.gather(*send_tasks, return_exceptions=True)
    
    async def send_custom_message(self, connection_id: str, message: Dict[str, Any]):
        """发送自定义消息给指定连接"""
        connection = self.active_connections.get(connection_id)
        if connection:
            try:
                await connection.send_message(message)
            except Exception as e:
                logger.error(f"发送自定义消息失败 {connection_id}: {str(e)}")
                await self.disconnect(connection_id)
    
    def get_connection_stats(self) -> Dict[str, Any]:
        """获取连接统计信息"""
        total_connections = len(self.active_connections)
        unique_users = len(self.user_connections)
        active_sessions = len(self.session_subscribers)
        
        user_stats = {}
        for user_id, connection_ids in self.user_connections.items():
            user_stats[user_id] = len(connection_ids)
        
        session_stats = {}
        for session_id, subscriber_ids in self.session_subscribers.items():
            session_stats[session_id] = len(subscriber_ids)
        
        return {
            "total_connections": total_connections,
            "unique_users": unique_users,
            "active_sessions": active_sessions,
            "user_connections": user_stats,
            "session_subscribers": session_stats,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def handle_websocket_message(self, connection_id: str, message: str):
        """处理WebSocket接收的消息"""
        try:
            data = json.loads(message)
            message_type = data.get("type")
            
            if message_type == "subscribe":
                session_id = data.get("session_id")
                if session_id:
                    await self.subscribe_to_session(connection_id, session_id)
            
            elif message_type == "unsubscribe":
                session_id = data.get("session_id")
                if session_id:
                    await self.unsubscribe_from_session(connection_id, session_id)
            
            elif message_type == "ping":
                # 心跳响应
                connection = self.active_connections.get(connection_id)
                if connection:
                    await connection.send_message({
                        "type": "pong",
                        "timestamp": datetime.utcnow().isoformat()
                    })
            
            else:
                logger.warning(f"未知消息类型: {message_type}")
        
        except json.JSONDecodeError:
            logger.error(f"无效的JSON消息: {message}")
        except Exception as e:
            logger.error(f"处理WebSocket消息失败: {str(e)}")


# 全局WebSocket管理器实例
_global_websocket_manager = None

def get_websocket_manager() -> ProgressWebSocketManager:
    """获取全局WebSocket管理器实例"""
    global _global_websocket_manager
    if _global_websocket_manager is None:
        _global_websocket_manager = ProgressWebSocketManager()
    return _global_websocket_manager


# 便利函数
async def send_analysis_progress(session_id: int, progress: int, message: str, data: Dict[str, Any] = None):
    """发送分析进度更新"""
    manager = get_websocket_manager()
    await manager.send_progress_update(
        session_id=f"analysis_{session_id}",
        data={
            "type": "analysis",
            "session_id": session_id,
            "status": "running",
            "progress": progress,
            "current_processing": message,
            "timestamp": datetime.utcnow().isoformat(),
            **(data or {})
        }
    )

async def send_synthesis_progress(task_id: int, progress: int, message: str, data: Dict[str, Any] = None):
    """发送合成进度更新"""
    manager = get_websocket_manager()
    await manager.send_progress_update(
        session_id=f"synthesis_{task_id}",
        data={
            "type": "synthesis",
            "task_id": task_id,
            "status": "running",
            "progress": progress,
            "current_processing": message,
            "timestamp": datetime.utcnow().isoformat(),
            **(data or {})
        }
    )

async def send_user_notification(user_id: str, title: str, message: str, type: str = "info"):
    """发送用户通知"""
    manager = get_websocket_manager()
    notification = UserNotification(
        id=f"notification_{datetime.utcnow().timestamp()}",
        type=type,
        title=title,
        message=message
    )
    await manager.send_notification_to_user(user_id, notification) 