"""
服务层单元测试
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from motor.motor_asyncio import AsyncIOMotorDatabase
from src.services.engine_service import EngineService
from src.services.voice_service import VoiceService
from src.services.character_service import CharacterService
from src.services.tts_service import TTSService


class TestEngineService:
    """引擎服务测试"""
    
    @pytest.fixture
    def mock_db(self):
        """模拟数据库"""
        db = Mock(spec=AsyncIOMotorDatabase)
        collection = Mock()
        db.__getitem__.return_value = collection
        return db, collection
    
    @pytest.fixture
    def engine_service(self, mock_db):
        """创建引擎服务实例"""
        db, _ = mock_db
        return EngineService(db)
    
    @pytest.mark.asyncio
    async def test_create_engine(self, engine_service, mock_db):
        """测试创建引擎"""
        db, collection = mock_db
        
        # 模拟插入操作
        collection.insert_one = AsyncMock(return_value=Mock(inserted_id="engine_id_123"))
        collection.find_one = AsyncMock(return_value={
            "_id": "engine_id_123",
            "name": "test-engine",
            "type": "megatts3",
            "status": "active"
        })
        
        engine_data = {
            "name": "test-engine",
            "type": "megatts3",
            "description": "测试引擎",
            "url": "http://localhost:7929"
        }
        
        result = await engine_service.create_engine(engine_data)
        assert result["name"] == "test-engine"
        assert result["type"] == "megatts3"
        collection.insert_one.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_engine_by_id(self, engine_service, mock_db):
        """测试根据ID获取引擎"""
        db, collection = mock_db
        
        collection.find_one = AsyncMock(return_value={
            "_id": "engine_id_123",
            "name": "test-engine",
            "type": "megatts3"
        })
        
        result = await engine_service.get_engine("engine_id_123")
        assert result["name"] == "test-engine"
        collection.find_one.assert_called_once_with({"_id": "engine_id_123"})
    
    @pytest.mark.asyncio
    async def test_update_engine(self, engine_service, mock_db):
        """测试更新引擎"""
        db, collection = mock_db
        
        collection.find_one_and_update = AsyncMock(return_value={
            "_id": "engine_id_123",
            "name": "test-engine",
            "description": "更新后的描述"
        })
        
        update_data = {"description": "更新后的描述"}
        result = await engine_service.update_engine("engine_id_123", update_data)
        assert result["description"] == "更新后的描述"
    
    @pytest.mark.asyncio
    async def test_delete_engine(self, engine_service, mock_db):
        """测试删除引擎"""
        db, collection = mock_db
        
        collection.delete_one = AsyncMock(return_value=Mock(deleted_count=1))
        
        result = await engine_service.delete_engine("engine_id_123")
        assert result is True
        collection.delete_one.assert_called_once_with({"_id": "engine_id_123"})
    
    @pytest.mark.asyncio
    async def test_list_engines(self, engine_service, mock_db):
        """测试列出引擎"""
        db, collection = mock_db
        
        mock_cursor = Mock()
        mock_cursor.to_list = AsyncMock(return_value=[
            {"_id": "1", "name": "engine1"},
            {"_id": "2", "name": "engine2"}
        ])
        collection.find.return_value = mock_cursor
        collection.count_documents = AsyncMock(return_value=2)
        
        result = await engine_service.list_engines()
        assert len(result["engines"]) == 2
        assert result["total"] == 2


class TestVoiceService:
    """声音服务测试"""
    
    @pytest.fixture
    def mock_db(self):
        """模拟数据库"""
        db = Mock(spec=AsyncIOMotorDatabase)
        collection = Mock()
        db.__getitem__.return_value = collection
        return db, collection
    
    @pytest.fixture
    def voice_service(self, mock_db):
        """创建声音服务实例"""
        db, _ = mock_db
        return VoiceService(db)
    
    @pytest.mark.asyncio
    async def test_create_voice(self, voice_service, mock_db):
        """测试创建声音"""
        db, collection = mock_db
        
        collection.insert_one = AsyncMock(return_value=Mock(inserted_id="voice_id_123"))
        collection.find_one = AsyncMock(return_value={
            "_id": "voice_id_123",
            "name": "test-voice",
            "display_name": "测试声音",
            "gender": "female"
        })
        
        voice_data = {
            "name": "test-voice",
            "display_name": "测试声音",
            "engine_id": "engine_123",
            "gender": "female"
        }
        
        result = await voice_service.create_voice(voice_data)
        assert result["name"] == "test-voice"
        assert result["gender"] == "female"
    
    @pytest.mark.asyncio
    async def test_search_voices(self, voice_service, mock_db):
        """测试搜索声音"""
        db, collection = mock_db
        
        mock_cursor = Mock()
        mock_cursor.to_list = AsyncMock(return_value=[
            {"_id": "1", "name": "voice1", "gender": "female"},
            {"_id": "2", "name": "voice2", "gender": "female"}
        ])
        collection.find.return_value = mock_cursor
        collection.count_documents = AsyncMock(return_value=2)
        
        result = await voice_service.search_voices(
            query="测试",
            filters={"gender": "female"}
        )
        assert len(result["voices"]) == 2
        assert result["total"] == 2


class TestCharacterService:
    """角色服务测试"""
    
    @pytest.fixture
    def mock_db(self):
        """模拟数据库"""
        db = Mock(spec=AsyncIOMotorDatabase)
        collection = Mock()
        db.__getitem__.return_value = collection
        return db, collection
    
    @pytest.fixture
    def character_service(self, mock_db):
        """创建角色服务实例"""
        db, _ = mock_db
        return CharacterService(db)
    
    @pytest.mark.asyncio
    async def test_create_character(self, character_service, mock_db):
        """测试创建角色"""
        db, collection = mock_db
        
        collection.insert_one = AsyncMock(return_value=Mock(inserted_id="char_id_123"))
        collection.find_one = AsyncMock(return_value={
            "_id": "char_id_123",
            "name": "test-character",
            "display_name": "测试角色",
            "gender": "female"
        })
        
        character_data = {
            "name": "test-character",
            "display_name": "测试角色",
            "gender": "female",
            "type": "protagonist"
        }
        
        result = await character_service.create_character(character_data)
        assert result["name"] == "test-character"
        assert result["gender"] == "female"
    
    @pytest.mark.asyncio
    async def test_add_voice_mapping(self, character_service, mock_db):
        """测试添加声音映射"""
        db, collection = mock_db
        
        collection.find_one_and_update = AsyncMock(return_value={
            "_id": "char_id_123",
            "voice_mappings": [
                {
                    "id": "mapping_123",
                    "voice_id": "voice_123",
                    "emotion": "happy",
                    "priority": 1
                }
            ]
        })
        
        mapping_data = {
            "voice_id": "voice_123",
            "emotion": "happy",
            "priority": 1
        }
        
        result = await character_service.add_voice_mapping("char_id_123", mapping_data)
        assert len(result["voice_mappings"]) == 1
        assert result["voice_mappings"][0]["emotion"] == "happy"


class TestTTSService:
    """TTS服务测试"""
    
    @pytest.fixture
    def mock_db(self):
        """模拟数据库"""
        db = Mock(spec=AsyncIOMotorDatabase)
        collection = Mock()
        db.__getitem__.return_value = collection
        return db, collection
    
    @pytest.fixture
    def tts_service(self, mock_db):
        """创建TTS服务实例"""
        db, _ = mock_db
        return TTSService(db)
    
    @pytest.mark.asyncio
    async def test_create_synthesis_task(self, tts_service, mock_db):
        """测试创建合成任务"""
        db, collection = mock_db
        
        collection.insert_one = AsyncMock(return_value=Mock(inserted_id="task_id_123"))
        collection.find_one = AsyncMock(return_value={
            "_id": "task_id_123",
            "text": "测试文本",
            "voice_id": "voice_123",
            "status": "pending"
        })
        
        task_data = {
            "text": "测试文本",
            "voice_id": "voice_123",
            "engine_id": "engine_123"
        }
        
        result = await tts_service.create_synthesis_task(task_data)
        assert result["text"] == "测试文本"
        assert result["status"] == "pending"
    
    @pytest.mark.asyncio
    async def test_get_task_status(self, tts_service, mock_db):
        """测试获取任务状态"""
        db, collection = mock_db
        
        collection.find_one = AsyncMock(return_value={
            "_id": "task_id_123",
            "status": "completed",
            "progress": 100,
            "result": {"audio_path": "/tmp/output.wav"}
        })
        
        result = await tts_service.get_task_status("task_id_123")
        assert result["status"] == "completed"
        assert result["progress"] == 100
    
    @pytest.mark.asyncio
    async def test_cancel_task(self, tts_service, mock_db):
        """测试取消任务"""
        db, collection = mock_db
        
        collection.find_one_and_update = AsyncMock(return_value={
            "_id": "task_id_123",
            "status": "cancelled"
        })
        
        result = await tts_service.cancel_task("task_id_123")
        assert result["status"] == "cancelled"