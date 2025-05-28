"""
pytest配置文件
提供测试夹具和配置
"""

import pytest
import asyncio
from httpx import AsyncClient
from fastapi.testclient import TestClient
from motor.motor_asyncio import AsyncIOMotorClient
import os
from typing import AsyncGenerator, Generator

# 设置测试环境变量
os.environ.update({
    "DB_HOST": "localhost",
    "DB_PORT": "27017", 
    "DB_DATABASE": "ai_sound_test",
    "DB_USERNAME": "",
    "DB_PASSWORD": "",
    "API_HOST": "127.0.0.1",
    "API_PORT": "9930",
    "REDIS_HOST": "localhost",
    "REDIS_PORT": "6379",
    "LOG_LEVEL": "DEBUG"
})

from src.api.app import app
from src.core.config import settings
from src.core.database import get_database


@pytest.fixture(scope="session")
def event_loop():
    """创建事件循环"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def test_db():
    """测试数据库连接"""
    client = AsyncIOMotorClient(settings.database.url)
    db = client[settings.database.database]
    
    # 清理测试数据库
    await db.drop_collection("engines")
    await db.drop_collection("voices")
    await db.drop_collection("characters")
    await db.drop_collection("tasks")
    
    yield db
    
    # 测试结束后清理
    await db.drop_collection("engines")
    await db.drop_collection("voices")
    await db.drop_collection("characters")
    await db.drop_collection("tasks")
    client.close()


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    """同步测试客户端"""
    with TestClient(app) as c:
        yield c


@pytest.fixture
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    """异步测试客户端"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest.fixture
async def sample_engine_data():
    """示例引擎数据"""
    return {
        "name": "test-engine",
        "type": "megatts3",
        "description": "测试引擎",
        "url": "http://localhost:7929",
        "config": {
            "model_path": "/test/model.pth",
            "use_gpu": False,
            "batch_size": 1
        },
        "status": "active"
    }


@pytest.fixture
async def sample_voice_data():
    """示例声音数据"""
    return {
        "name": "test-voice",
        "display_name": "测试声音",
        "engine_id": "test-engine-id",
        "gender": "female",
        "style": "neutral",
        "language": "zh-CN",
        "description": "测试用声音",
        "config": {
            "speaker_id": "speaker_001",
            "emotion": "neutral"
        }
    }


@pytest.fixture
async def sample_character_data():
    """示例角色数据"""
    return {
        "name": "test-character",
        "display_name": "测试角色",
        "description": "测试用角色",
        "gender": "female",
        "type": "protagonist",
        "voice_mappings": []
    }


@pytest.fixture
async def sample_tts_request():
    """示例TTS请求"""
    return {
        "text": "这是一个测试文本",
        "voice_id": "test-voice-id",
        "engine_id": "test-engine-id",
        "format": "wav",
        "sample_rate": 22050,
        "speed": 1.0,
        "pitch": 1.0,
        "volume": 1.0
    }