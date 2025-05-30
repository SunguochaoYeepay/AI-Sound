"""
数据库管理模块
提供MongoDB连接和基础操作
"""

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo.errors import ConnectionFailure
from typing import Optional
import logging
from datetime import datetime

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


async def init_database():
    """初始化数据库连接和基础结构"""
    try:
        if not db_manager.is_connected:
            await db_manager.connect()
        
        db = db_manager.get_database()
        
        # 确保索引存在（如果需要的话）
        # 这里可以添加创建索引的代码，但不插入任何数据
        
        logger.info("数据库初始化完成")
        
    except Exception as e:
        logger.error(f"数据库初始化失败: {e}")
        raise


async def init_test_data_manual():
    """手动初始化测试数据（仅用于开发环境）"""
    try:
        if not db_manager.is_connected:
            await db_manager.connect()
        
        db = db_manager.get_database()
        
        logger.info("开始手动初始化测试数据...")
        
        # 初始化引擎数据
        engines_collection = db["engines"]
        test_engines = [
            {
                "id": "megatts3_001",
                "name": "MegaTTS3 中文引擎",
                "type": "megatts3",
                "version": "3.0.0",
                "description": "高质量中文语音合成引擎",
                "status": "ready",
                "config": {
                    "model_path": "/models/megatts3_base.pth",
                    "device": "cpu",
                    "device_id": 0,
                    "batch_size": 1,
                    "max_workers": 1,
                    "timeout": 30,
                    "custom_params": {}
                },
                "capabilities": {
                    "languages": ["zh-CN"],
                    "sample_rates": [16000, 22050, 44100],
                    "audio_formats": ["wav", "mp3"],
                    "max_text_length": 1000,
                    "supports_speed_control": True,
                    "supports_pitch_control": True,
                    "supports_emotion": False
                },
                "parameters": [],
                "is_enabled": True,
                "created_at": datetime.now(),
                "updated_at": datetime.now(),
                "last_health_check": None,
                "error_message": None
            }
        ]
        
        await engines_collection.insert_many(test_engines)
        logger.info("已初始化测试引擎数据")
        
        # 初始化声音数据
        voices_collection = db["voices"]
        test_voices = [
            {
                "id": "voice_001",
                "name": "xiaoxiao",
                "display_name": "小小",
                "engine_id": "megatts3_001",
                "engine_voice_id": "xiaoxiao",
                "language": "zh-CN",
                "gender": "female",
                "style": "neutral",
                "source": "builtin",
                "description": "温柔的女声",
                "tags": ["中文", "女声", "温柔"],
                "is_active": True,
                "usage_count": 0,
                "created_at": datetime.now(),
                "updated_at": datetime.now()
            }
        ]
        
        await voices_collection.insert_many(test_voices)
        logger.info("已初始化测试声音数据")
        
        # 初始化角色数据
        characters_collection = db["characters"]
        test_characters = [
            {
                "id": "char_001",
                "name": "小助手",
                "display_name": "智能小助手",
                "description": "智能助手角色",
                "type": "main",
                "gender": "unknown",
                "personality": "friendly",
                "tags": ["助手", "友好"],
                "category": "general",
                "is_active": True,
                "usage_count": 0,
                "default_speed": 1.0,
                "default_pitch": 0.0,
                "default_volume": 1.0,
                "voice_mappings": [],
                "default_voice_id": "voice_001",
                "created_at": datetime.now(),
                "updated_at": datetime.now()
            }
        ]
        
        await characters_collection.insert_many(test_characters)
        logger.info("已初始化测试角色数据")
            
    except Exception as e:
        logger.error(f"初始化测试数据失败: {e}")
        raise


async def cleanup_test_data():
    """清理测试数据"""
    try:
        if not db_manager.is_connected:
            await db_manager.connect()
        
        db = db_manager.get_database()
        
        # 删除测试引擎
        result_engines = await db["engines"].delete_many({"id": {"$in": ["megatts3_001"]}})
        logger.info(f"已删除 {result_engines.deleted_count} 个测试引擎")
        
        # 删除测试声音
        result_voices = await db["voices"].delete_many({"id": {"$in": ["voice_001"]}, "name": "xiaoxiao"})
        logger.info(f"已删除 {result_voices.deleted_count} 个测试声音")
        
        # 删除测试角色
        result_characters = await db["characters"].delete_many({"id": {"$in": ["char_001"]}})
        logger.info(f"已删除 {result_characters.deleted_count} 个测试角色")
        
        logger.info("测试数据清理完成")
        
    except Exception as e:
        logger.error(f"清理测试数据失败: {e}")
        raise


async def reset_database():
    """重置数据库（危险操作，会删除所有数据）"""
    try:
        if not db_manager.is_connected:
            await db_manager.connect()
        
        db = db_manager.get_database()
        
        # 删除所有数据
        await db["engines"].delete_many({})
        await db["voices"].delete_many({})
        await db["characters"].delete_many({})
        
        logger.warning("数据库已重置，所有数据已删除")
        
        # 重新初始化测试数据
        await init_test_data_manual()
        
    except Exception as e:
        logger.error(f"重置数据库失败: {e}")
        raise