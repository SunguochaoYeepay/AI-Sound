"""
数据库管理模块
提供MongoDB连接和基础操作
"""

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo.errors import ConnectionFailure
from typing import Optional
import logging

from .config import settings

logger = logging.getLogger(__name__)


class DatabaseManager:
    """数据库管理器"""
    
    def __init__(self):
        self.client: Optional[AsyncIOMotorClient] = None
        self.database: Optional[AsyncIOMotorDatabase] = None
        self._connected = False
    
    async def connect(self) -> None:
        """连接数据库"""
        try:
            self.client = AsyncIOMotorClient(settings.database.url)
            self.database = self.client[settings.database.database]
            
            # 测试连接
            await self.client.admin.command('ping')
            self._connected = True
            logger.info(f"数据库连接成功: {settings.database.host}:{settings.database.port}")
            
        except ConnectionFailure as e:
            logger.error(f"数据库连接失败: {e}")
            raise
    
    async def disconnect(self) -> None:
        """断开数据库连接"""
        if self.client:
            self.client.close()
            self._connected = False
            logger.info("数据库连接已断开")
    
    @property
    def is_connected(self) -> bool:
        """检查是否已连接"""
        return self._connected
    
    def get_database(self) -> AsyncIOMotorDatabase:
        """获取数据库实例"""
        if not self._connected or self.database is None:
            raise RuntimeError("数据库未连接")
        return self.database
    
    def get_collection(self, name: str):
        """获取集合"""
        return self.get_database()[name]


# 全局数据库管理器实例
db_manager = DatabaseManager()


async def get_database() -> AsyncIOMotorDatabase:
    """获取数据库实例（依赖注入用）"""
    return db_manager.get_database()


async def get_collection(name: str):
    """获取集合（依赖注入用）"""
    return db_manager.get_collection(name)