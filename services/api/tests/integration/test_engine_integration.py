"""
引擎集成测试
"""

import pytest
from httpx import AsyncClient
from fastapi.testclient import TestClient
import asyncio


@pytest.mark.integration
class TestEngineIntegration:
    """引擎集成测试类"""
    
    @pytest.mark.asyncio
    async def test_engine_lifecycle(self, async_client: AsyncClient, sample_engine_data):
        """测试引擎完整生命周期"""
        # 1. 创建引擎
        create_response = await async_client.post("/api/engines", json=sample_engine_data)
        assert create_response.status_code == 201
        engine = create_response.json()
        engine_id = engine["id"]
        
        # 2. 获取引擎详情
        get_response = await async_client.get(f"/api/engines/{engine_id}")
        assert get_response.status_code == 200
        assert get_response.json()["name"] == sample_engine_data["name"]
        
        # 3. 更新引擎
        update_data = {"description": "集成测试更新"}
        update_response = await async_client.put(f"/api/engines/{engine_id}", json=update_data)
        assert update_response.status_code == 200
        assert update_response.json()["description"] == "集成测试更新"
        
        # 4. 健康检查
        health_response = await async_client.get(f"/api/engines/{engine_id}/health")
        assert health_response.status_code == 200
        
        # 5. 删除引擎
        delete_response = await async_client.delete(f"/api/engines/{engine_id}")
        assert delete_response.status_code == 204
        
        # 6. 验证删除
        get_deleted_response = await async_client.get(f"/api/engines/{engine_id}")
        assert get_deleted_response.status_code == 404
    
    @pytest.mark.asyncio
    async def test_engine_voice_integration(self, async_client: AsyncClient, sample_engine_data, sample_voice_data):
        """测试引擎与声音的集成"""
        # 创建引擎
        engine_response = await async_client.post("/api/engines", json=sample_engine_data)
        engine_id = engine_response.json()["id"]
        
        # 创建关联声音
        voice_data = sample_voice_data.copy()
        voice_data["engine_id"] = engine_id
        voice_response = await async_client.post("/api/voices", json=voice_data)
        assert voice_response.status_code == 201
        voice_id = voice_response.json()["id"]
        
        # 获取引擎的声音列表
        engine_voices_response = await async_client.get(f"/api/voices/engine/{engine_id}")
        assert engine_voices_response.status_code == 200
        voices = engine_voices_response.json()["voices"]
        assert len(voices) >= 1
        assert any(v["id"] == voice_id for v in voices)
        
        # 清理
        await async_client.delete(f"/api/voices/{voice_id}")
        await async_client.delete(f"/api/engines/{engine_id}")
    
    @pytest.mark.asyncio
    async def test_engine_tts_integration(self, async_client: AsyncClient, sample_engine_data, sample_voice_data):
        """测试引擎与TTS的集成"""
        # 创建引擎和声音
        engine_response = await async_client.post("/api/engines", json=sample_engine_data)
        engine_id = engine_response.json()["id"]
        
        voice_data = sample_voice_data.copy()
        voice_data["engine_id"] = engine_id
        voice_response = await async_client.post("/api/voices", json=voice_data)
        voice_id = voice_response.json()["id"]
        
        # 创建TTS任务
        tts_request = {
            "text": "集成测试文本",
            "voice_id": voice_id,
            "engine_id": engine_id,
            "format": "wav"
        }
        tts_response = await async_client.post("/api/tts/synthesize", json=tts_request)
        assert tts_response.status_code == 200
        task_id = tts_response.json()["task_id"]
        
        # 检查任务状态
        status_response = await async_client.get(f"/api/tts/tasks/{task_id}")
        assert status_response.status_code == 200
        
        # 清理
        await async_client.delete(f"/api/tts/tasks/{task_id}")
        await async_client.delete(f"/api/voices/{voice_id}")
        await async_client.delete(f"/api/engines/{engine_id}")


@pytest.mark.integration
class TestEngineAdapterIntegration:
    """引擎适配器集成测试"""
    
    @pytest.mark.asyncio
    async def test_adapter_factory_integration(self, async_client: AsyncClient):
        """测试适配器工厂集成"""
        # 获取支持的引擎类型
        response = await async_client.get("/api/tts/engines")
        assert response.status_code == 200
        engines = response.json()["engines"]
        assert len(engines) > 0
        
        # 验证包含预期的引擎类型
        engine_types = [engine["type"] for engine in engines]
        assert "espnet" in engine_types
        assert "megatts3" in engine_types
    
    @pytest.mark.asyncio
    async def test_engine_config_validation(self, async_client: AsyncClient):
        """测试引擎配置验证"""
        # 测试无效配置
        invalid_engine_data = {
            "name": "invalid-engine",
            "type": "unknown_type",
            "url": "invalid-url"
        }
        
        response = await async_client.post("/api/engines", json=invalid_engine_data)
        assert response.status_code == 422  # 验证错误
    
    @pytest.mark.asyncio
    async def test_concurrent_engine_operations(self, async_client: AsyncClient, sample_engine_data):
        """测试并发引擎操作"""
        # 并发创建多个引擎
        tasks = []
        for i in range(3):
            engine_data = sample_engine_data.copy()
            engine_data["name"] = f"concurrent-engine-{i}"
            task = async_client.post("/api/engines", json=engine_data)
            tasks.append(task)
        
        responses = await asyncio.gather(*tasks)
        
        # 验证所有引擎都创建成功
        engine_ids = []
        for response in responses:
            assert response.status_code == 201
            engine_ids.append(response.json()["id"])
        
        # 并发删除引擎
        delete_tasks = [async_client.delete(f"/api/engines/{eid}") for eid in engine_ids]
        delete_responses = await asyncio.gather(*delete_tasks)
        
        for response in delete_responses:
            assert response.status_code == 204