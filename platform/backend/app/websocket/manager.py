"""
WebSocket连接管理器
处理客户端连接、消息广播和会话管理
"""

import json
import logging
import asyncio
from typing import Dict, List, Any, Optional, Set
from datetime import datetime
from fastapi import WebSocket, WebSocketDisconnect
from fastapi.websockets import WebSocketState

logger = logging.getLogger(__name__)


class WebSocketManager:
    """WebSocket连接管理器"""
    
    def __init__(self):
        # 活跃连接存储
        self.active_connections: Dict[str, WebSocket] = {}
        
        # 连接元数据
        self.connection_metadata: Dict[str, Dict[str, Any]] = {}
        
        # 订阅管理
        self.subscriptions: Dict[str, Set[str]] = {}  # topic -> connection_ids
        
        # 统计信息
        self.stats = {
            "total_connections": 0,
            "active_connections": 0,
            "messages_sent": 0,
            "messages_received": 0,
            "start_time": None
        }
        
        # 管理器状态
        self.is_running = False
        
        # 心跳任务
        self.heartbeat_task: Optional[asyncio.Task] = None
    
    async def start(self):
        """启动WebSocket管理器"""
        if self.is_running:
            return
        
        self.is_running = True
        self.stats["start_time"] = datetime.now()
        
        # 启动心跳检查
        self.heartbeat_task = asyncio.create_task(self._heartbeat_loop())
        
        logger.info("🔌 WebSocket管理器已启动")
    
    async def stop(self):
        """停止WebSocket管理器"""
        if not self.is_running:
            return
        
        self.is_running = False
        
        # 停止心跳任务
        if self.heartbeat_task:
            self.heartbeat_task.cancel()
            try:
                await self.heartbeat_task
            except asyncio.CancelledError:
                pass
        
        # 关闭所有连接
        await self._close_all_connections()
        
        logger.info("🔌 WebSocket管理器已停止")
    
    async def connect(self, websocket: WebSocket, connection_id: str, metadata: Dict[str, Any] = None):
        """接受新的WebSocket连接"""
        try:
            await websocket.accept()
            
            # 存储连接
            self.active_connections[connection_id] = websocket
            self.connection_metadata[connection_id] = {
                "connected_at": datetime.now(),
                "last_activity": datetime.now(),
                "metadata": metadata or {}
            }
            
            # 更新统计
            self.stats["total_connections"] += 1
            self.stats["active_connections"] = len(self.active_connections)
            
            logger.info(f"✅ WebSocket连接已建立: {connection_id}")
            
            # 发送欢迎消息
            await self.send_personal_message(connection_id, {
                "type": "connection_established",
                "data": {
                    "connection_id": connection_id,
                    "server_time": datetime.now().isoformat(),
                    "message": "WebSocket连接已建立"
                }
            })
            
        except Exception as e:
            logger.error(f"❌ WebSocket连接失败: {connection_id}, 错误: {e}")
            raise
    
    async def disconnect(self, connection_id: str):
        """断开WebSocket连接"""
        try:
            # 移除连接
            if connection_id in self.active_connections:
                del self.active_connections[connection_id]
            
            if connection_id in self.connection_metadata:
                del self.connection_metadata[connection_id]
            
            # 移除所有订阅
            for topic in list(self.subscriptions.keys()):
                self.subscriptions[topic].discard(connection_id)
                if not self.subscriptions[topic]:
                    del self.subscriptions[topic]
            
            # 更新统计
            self.stats["active_connections"] = len(self.active_connections)
            
            logger.info(f"🔌 WebSocket连接已断开: {connection_id}")
            
        except Exception as e:
            logger.error(f"❌ 断开WebSocket连接失败: {connection_id}, 错误: {e}")
    
    async def send_personal_message(self, connection_id: str, message: Dict[str, Any]):
        """发送个人消息"""
        if connection_id not in self.active_connections:
            logger.warning(f"⚠️ 尝试向不存在的连接发送消息: {connection_id}")
            return False
        
        websocket = self.active_connections[connection_id]
        
        try:
            # 检查连接状态
            if websocket.client_state != WebSocketState.CONNECTED:
                await self.disconnect(connection_id)
                return False
            
            # 发送消息
            message_str = json.dumps(message, ensure_ascii=False, default=str)
            await websocket.send_text(message_str)
            
            # 更新活动时间
            if connection_id in self.connection_metadata:
                self.connection_metadata[connection_id]["last_activity"] = datetime.now()
            
            self.stats["messages_sent"] += 1
            return True
            
        except WebSocketDisconnect:
            await self.disconnect(connection_id)
            return False
        except Exception as e:
            logger.error(f"❌ 发送个人消息失败: {connection_id}, 错误: {e}")
            await self.disconnect(connection_id)
            return False
    
    async def broadcast_message(self, message: Dict[str, Any], exclude: List[str] = None):
        """广播消息给所有连接"""
        exclude = exclude or []
        success_count = 0
        failed_connections = []
        
        for connection_id in list(self.active_connections.keys()):
            if connection_id in exclude:
                continue
            
            success = await self.send_personal_message(connection_id, message)
            if success:
                success_count += 1
            else:
                failed_connections.append(connection_id)
        
        # 清理失败的连接
        for connection_id in failed_connections:
            await self.disconnect(connection_id)
        
        logger.info(f"📡 广播消息完成: 成功 {success_count}, 失败 {len(failed_connections)}")
        return success_count
    
    async def subscribe(self, connection_id: str, topic: str):
        """订阅主题"""
        if connection_id not in self.active_connections:
            return False
        
        if topic not in self.subscriptions:
            self.subscriptions[topic] = set()
        
        self.subscriptions[topic].add(connection_id)
        logger.info(f"📝 连接 {connection_id} 订阅主题: {topic}")
        return True
    
    async def unsubscribe(self, connection_id: str, topic: str):
        """取消订阅主题"""
        if topic in self.subscriptions:
            self.subscriptions[topic].discard(connection_id)
            if not self.subscriptions[topic]:
                del self.subscriptions[topic]
        
        logger.info(f"📝 连接 {connection_id} 取消订阅主题: {topic}")
    
    async def publish_to_topic(self, topic: str, message: Dict[str, Any]):
        """发布消息到主题"""
        if topic not in self.subscriptions:
            logger.warning(f"⚠️ 主题无订阅者: {topic}")
            return 0
        
        subscribers = list(self.subscriptions[topic])
        success_count = 0
        
        for connection_id in subscribers:
            success = await self.send_personal_message(connection_id, {
                "type": "topic_message",
                "topic": topic,
                "data": message
            })
            if success:
                success_count += 1
        
        logger.info(f"📡 主题消息发布: {topic}, 订阅者 {len(subscribers)}, 成功 {success_count}")
        return success_count
    
    async def handle_message(self, connection_id: str, message: str):
        """处理接收到的消息"""
        try:
            data = json.loads(message)
            message_type = data.get("type")
            
            self.stats["messages_received"] += 1
            
            # 更新活动时间
            if connection_id in self.connection_metadata:
                self.connection_metadata[connection_id]["last_activity"] = datetime.now()
            
            # 处理不同类型的消息
            if message_type == "subscribe":
                # 兼容两种格式：直接topic字段或data.topic字段
                topic = data.get("topic") or (data.get("data", {}).get("topic") if isinstance(data.get("data"), dict) else None)
                if topic:
                    await self.subscribe(connection_id, topic)
                    await self.send_personal_message(connection_id, {
                        "type": "subscription_confirmed",
                        "topic": topic
                    })
                    logger.info(f"✅ 订阅成功: {connection_id} -> {topic}")
                else:
                    logger.warning(f"⚠️ 订阅请求缺少topic: {data}")
            
            elif message_type == "unsubscribe":
                # 兼容两种格式：直接topic字段或data.topic字段
                topic = data.get("topic") or (data.get("data", {}).get("topic") if isinstance(data.get("data"), dict) else None)
                if topic:
                    await self.unsubscribe(connection_id, topic)
                    await self.send_personal_message(connection_id, {
                        "type": "unsubscription_confirmed",
                        "topic": topic
                    })
                    logger.info(f"✅ 取消订阅成功: {connection_id} -> {topic}")
                else:
                    logger.warning(f"⚠️ 取消订阅请求缺少topic: {data}")
            
            elif message_type == "ping":
                await self.send_personal_message(connection_id, {
                    "type": "pong",
                    "timestamp": datetime.now().isoformat()
                })
            
            else:
                logger.warning(f"⚠️ 未知消息类型: {message_type} from {connection_id}")
        
        except json.JSONDecodeError:
            logger.error(f"❌ 无效的JSON消息: {connection_id}")
        except Exception as e:
            logger.error(f"❌ 处理消息失败: {connection_id}, 错误: {e}")
    
    async def _heartbeat_loop(self):
        """心跳检查循环"""
        while self.is_running:
            try:
                await asyncio.sleep(30)  # 每30秒检查一次
                
                current_time = datetime.now()
                inactive_connections = []
                
                for connection_id, metadata in self.connection_metadata.items():
                    last_activity = metadata.get("last_activity")
                    if last_activity:
                        inactive_duration = (current_time - last_activity).total_seconds()
                        if inactive_duration > 300:  # 5分钟无活动
                            inactive_connections.append(connection_id)
                
                # 清理不活跃的连接
                for connection_id in inactive_connections:
                    logger.info(f"🧹 清理不活跃连接: {connection_id}")
                    await self.disconnect(connection_id)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"❌ 心跳检查失败: {e}")
    
    async def _close_all_connections(self):
        """关闭所有连接"""
        for connection_id in list(self.active_connections.keys()):
            try:
                websocket = self.active_connections[connection_id]
                if websocket.client_state == WebSocketState.CONNECTED:
                    await websocket.close()
            except Exception as e:
                logger.error(f"❌ 关闭连接失败: {connection_id}, 错误: {e}")
            finally:
                await self.disconnect(connection_id)
    
    def get_status(self) -> Dict[str, Any]:
        """获取管理器状态"""
        uptime = None
        if self.stats["start_time"]:
            uptime = (datetime.now() - self.stats["start_time"]).total_seconds()
        
        return {
            "status": "running" if self.is_running else "stopped",
            "active_connections": self.stats["active_connections"],
            "total_connections": self.stats["total_connections"],
            "messages_sent": self.stats["messages_sent"],
            "messages_received": self.stats["messages_received"],
            "topics": len(self.subscriptions),
            "uptime_seconds": uptime,
            "connection_details": {
                conn_id: {
                    "connected_at": meta["connected_at"].isoformat(),
                    "last_activity": meta["last_activity"].isoformat(),
                    "metadata": meta["metadata"]
                }
                for conn_id, meta in self.connection_metadata.items()
            }
        }


# 创建全局WebSocket管理器实例
websocket_manager = WebSocketManager() 