"""
适配器单元测试
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from src.adapters.base import BaseTTSAdapter, SynthesisParams, SynthesisResult, EngineStatus
from src.adapters.factory import AdapterFactory
from src.adapters.espnet_adapter import ESPnetAdapter
from src.adapters.megatts3_adapter import MegaTTS3Adapter


class TestBaseTTSAdapter:
    """基础适配器测试"""
    
    def test_synthesis_params_creation(self):
        """测试合成参数创建"""
        params = SynthesisParams(
            text="测试文本",
            voice_id="test_voice",
            speed=1.2,
            pitch=0.8,
            volume=1.0
        )
        assert params.text == "测试文本"
        assert params.voice_id == "test_voice"
        assert params.speed == 1.2
        assert params.pitch == 0.8
        assert params.volume == 1.0
    
    def test_synthesis_result_creation(self):
        """测试合成结果创建"""
        result = SynthesisResult(
            audio_path="/path/to/audio.wav",
            duration=5.5,
            sample_rate=22050,
            format="wav"
        )
        assert result.audio_path == "/path/to/audio.wav"
        assert result.duration == 5.5
        assert result.sample_rate == 22050
        assert result.format == "wav"
    
    def test_engine_status_enum(self):
        """测试引擎状态枚举"""
        assert EngineStatus.ACTIVE == "active"
        assert EngineStatus.INACTIVE == "inactive"
        assert EngineStatus.ERROR == "error"
        assert EngineStatus.MAINTENANCE == "maintenance"


class TestAdapterFactory:
    """适配器工厂测试"""
    
    def test_register_adapter(self):
        """测试注册适配器"""
        factory = AdapterFactory()
        
        # 创建模拟适配器类
        class MockAdapter(BaseTTSAdapter):
            async def synthesize(self, params: SynthesisParams) -> SynthesisResult:
                pass
            
            async def get_voices(self):
                pass
            
            async def health_check(self):
                pass
        
        # 注册适配器
        factory.register("mock", MockAdapter)
        assert "mock" in factory._adapters
    
    def test_create_adapter(self):
        """测试创建适配器"""
        factory = AdapterFactory()
        
        # 测试创建ESPnet适配器
        config = {
            "url": "http://localhost:9932",
            "timeout": 30
        }
        adapter = factory.create("espnet", config)
        assert isinstance(adapter, ESPnetAdapter)
    
    def test_get_available_types(self):
        """测试获取可用类型"""
        factory = AdapterFactory()
        types = factory.get_available_types()
        assert "espnet" in types
        assert "megatts3" in types
    
    def test_create_unknown_adapter(self):
        """测试创建未知适配器"""
        factory = AdapterFactory()
        
        with pytest.raises(ValueError, match="Unknown adapter type"):
            factory.create("unknown_type", {})


class TestESPnetAdapter:
    """ESPnet适配器测试"""
    
    @pytest.fixture
    def adapter(self):
        """创建ESPnet适配器实例"""
        config = {
            "url": "http://localhost:9932",
            "timeout": 30,
            "max_retries": 3
        }
        return ESPnetAdapter(config)
    
    @pytest.mark.asyncio
    async def test_health_check_success(self, adapter):
        """测试健康检查成功"""
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"status": "healthy"}
            mock_get.return_value = mock_response
            
            result = await adapter.health_check()
            assert result["status"] == "healthy"
    
    @pytest.mark.asyncio
    async def test_health_check_failure(self, adapter):
        """测试健康检查失败"""
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_get.side_effect = Exception("Connection failed")
            
            result = await adapter.health_check()
            assert result["status"] == "error"
            assert "Connection failed" in result["error"]
    
    @pytest.mark.asyncio
    async def test_get_voices(self, adapter):
        """测试获取声音列表"""
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "voices": [
                    {"id": "voice1", "name": "Voice 1"},
                    {"id": "voice2", "name": "Voice 2"}
                ]
            }
            mock_get.return_value = mock_response
            
            voices = await adapter.get_voices()
            assert len(voices) == 2
            assert voices[0]["id"] == "voice1"
    
    @pytest.mark.asyncio
    async def test_synthesize(self, adapter):
        """测试语音合成"""
        with patch('httpx.AsyncClient.post') as mock_post:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "audio_path": "/tmp/output.wav",
                "duration": 3.5,
                "sample_rate": 22050
            }
            mock_post.return_value = mock_response
            
            params = SynthesisParams(
                text="测试文本",
                voice_id="voice1",
                speed=1.0
            )
            result = await adapter.synthesize(params)
            assert result.audio_path == "/tmp/output.wav"
            assert result.duration == 3.5


class TestMegaTTS3Adapter:
    """MegaTTS3适配器测试"""
    
    @pytest.fixture
    def adapter(self):
        """创建MegaTTS3适配器实例"""
        config = {
            "url": "http://localhost:7929",
            "timeout": 60,
            "max_retries": 3
        }
        return MegaTTS3Adapter(config)
    
    @pytest.mark.asyncio
    async def test_health_check(self, adapter):
        """测试健康检查"""
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"status": "ready"}
            mock_get.return_value = mock_response
            
            result = await adapter.health_check()
            assert result["status"] == "ready"
    
    @pytest.mark.asyncio
    async def test_synthesize_with_emotion(self, adapter):
        """测试带情感的语音合成"""
        with patch('httpx.AsyncClient.post') as mock_post:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "audio_path": "/tmp/emotional_output.wav",
                "duration": 4.2,
                "sample_rate": 24000
            }
            mock_post.return_value = mock_response
            
            params = SynthesisParams(
                text="情感测试文本",
                voice_id="emotional_voice",
                speed=1.0,
                emotion="happy"
            )
            result = await adapter.synthesize(params)
            assert result.audio_path == "/tmp/emotional_output.wav"
            assert result.duration == 4.2
    
    @pytest.mark.asyncio
    async def test_parameter_mapping(self, adapter):
        """测试参数映射"""
        # 测试速度映射
        mapped_speed = adapter._map_parameter("speed", 1.5, "speed")
        assert mapped_speed == 1.5
        
        # 测试音调映射
        mapped_pitch = adapter._map_parameter("pitch", 0.8, "pitch")
        assert mapped_pitch == 0.8