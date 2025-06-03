"""
TTS工作流集成测试
"""

import pytest
from httpx import AsyncClient
import asyncio


@pytest.mark.integration
class TestTTSWorkflow:
    """TTS工作流集成测试"""
    
    @pytest.mark.asyncio
    async def test_complete_tts_workflow(self, async_client: AsyncClient, sample_engine_data, sample_voice_data, sample_character_data):
        """测试完整的TTS工作流"""
        # 1. 创建引擎
        engine_response = await async_client.post("/api/engines", json=sample_engine_data)
        assert engine_response.status_code == 201
        engine_id = engine_response.json()["id"]
        
        # 2. 创建声音
        voice_data = sample_voice_data.copy()
        voice_data["engine_id"] = engine_id
        voice_response = await async_client.post("/api/voices", json=voice_data)
        assert voice_response.status_code == 201
        voice_id = voice_response.json()["id"]
        
        # 3. 创建角色
        character_response = await async_client.post("/api/characters", json=sample_character_data)
        assert character_response.status_code == 201
        character_id = character_response.json()["id"]
        
        # 4. 添加角色声音映射
        mapping_data = {
            "voice_id": voice_id,
            "emotion": "neutral",
            "priority": 1
        }
        mapping_response = await async_client.post(f"/api/characters/{character_id}/voice-mappings", json=mapping_data)
        assert mapping_response.status_code == 201
        
        # 5. 执行TTS合成
        tts_request = {
            "text": "这是一个完整的工作流测试",
            "voice_id": voice_id,
            "engine_id": engine_id,
            "character_id": character_id,
            "format": "wav",
            "sample_rate": 22050
        }
        tts_response = await async_client.post("/api/tts/synthesize", json=tts_request)
        assert tts_response.status_code == 200
        task_id = tts_response.json()["task_id"]
        
        # 6. 监控任务进度
        max_attempts = 10
        for _ in range(max_attempts):
            status_response = await async_client.get(f"/api/tts/tasks/{task_id}")
            assert status_response.status_code == 200
            status = status_response.json()["status"]
            
            if status in ["completed", "failed"]:
                break
            
            await asyncio.sleep(1)
        
        # 7. 获取任务结果
        result_response = await async_client.get(f"/api/tts/tasks/{task_id}/result")
        # 结果可能还在处理中或已完成
        assert result_response.status_code in [200, 202]
        
        # 清理资源
        await async_client.delete(f"/api/tts/tasks/{task_id}")
        await async_client.delete(f"/api/characters/{character_id}")
        await async_client.delete(f"/api/voices/{voice_id}")
        await async_client.delete(f"/api/engines/{engine_id}")
    
    @pytest.mark.asyncio
    async def test_batch_tts_workflow(self, async_client: AsyncClient, sample_engine_data, sample_voice_data):
        """测试批量TTS工作流"""
        # 创建引擎和声音
        engine_response = await async_client.post("/api/engines", json=sample_engine_data)
        engine_id = engine_response.json()["id"]
        
        voice_data = sample_voice_data.copy()
        voice_data["engine_id"] = engine_id
        voice_response = await async_client.post("/api/voices", json=voice_data)
        voice_id = voice_response.json()["id"]
        
        # 批量合成请求
        batch_request = {
            "texts": [
                {"text": "第一段测试文本", "voice_id": voice_id},
                {"text": "第二段测试文本", "voice_id": voice_id},
                {"text": "第三段测试文本", "voice_id": voice_id}
            ],
            "format": "wav",
            "merge_output": False
        }
        
        batch_response = await async_client.post("/api/tts/batch-synthesize", json=batch_request)
        assert batch_response.status_code == 200
        batch_data = batch_response.json()
        batch_id = batch_data["batch_id"]
        task_ids = [task["id"] for task in batch_data["tasks"]]
        
        # 监控批量任务
        completed_tasks = 0
        max_attempts = 20
        
        for _ in range(max_attempts):
            batch_status_response = await async_client.get(f"/api/tts/batches/{batch_id}")
            if batch_status_response.status_code == 200:
                batch_status = batch_status_response.json()
                completed_tasks = batch_status.get("completed_tasks", 0)
                
                if completed_tasks == len(task_ids):
                    break
            
            await asyncio.sleep(1)
        
        # 清理
        for task_id in task_ids:
            await async_client.delete(f"/api/tts/tasks/{task_id}")
        await async_client.delete(f"/api/voices/{voice_id}")
        await async_client.delete(f"/api/engines/{engine_id}")
    
    @pytest.mark.asyncio
    async def test_character_voice_selection_workflow(self, async_client: AsyncClient, sample_engine_data, sample_character_data):
        """测试角色声音选择工作流"""
        # 创建引擎
        engine_response = await async_client.post("/api/engines", json=sample_engine_data)
        engine_id = engine_response.json()["id"]
        
        # 创建多个声音
        voice_ids = []
        emotions = ["happy", "sad", "angry", "neutral"]
        
        for i, emotion in enumerate(emotions):
            voice_data = {
                "name": f"voice-{emotion}",
                "display_name": f"声音-{emotion}",
                "engine_id": engine_id,
                "gender": "female",
                "style": emotion,
                "language": "zh-CN"
            }
            voice_response = await async_client.post("/api/voices", json=voice_data)
            voice_ids.append(voice_response.json()["id"])
        
        # 创建角色
        character_response = await async_client.post("/api/characters", json=sample_character_data)
        character_id = character_response.json()["id"]
        
        # 为角色添加多个声音映射
        for i, (voice_id, emotion) in enumerate(zip(voice_ids, emotions)):
            mapping_data = {
                "voice_id": voice_id,
                "emotion": emotion,
                "priority": i + 1,
                "conditions": {
                    "text_type": "dialogue" if emotion != "neutral" else "narration"
                }
            }
            mapping_response = await async_client.post(f"/api/characters/{character_id}/voice-mappings", json=mapping_data)
            assert mapping_response.status_code == 201
        
        # 测试不同情感的声音选择
        for emotion in emotions:
            test_request = {
                "text": f"这是{emotion}情感的测试文本",
                "character_id": character_id,
                "emotion": emotion,
                "scene_type": "dialogue"
            }
            
            test_response = await async_client.post(f"/api/characters/{character_id}/voice-test", json=test_request)
            assert test_response.status_code == 200
            result = test_response.json()
            assert result["emotion"] == emotion
        
        # 清理
        await async_client.delete(f"/api/characters/{character_id}")
        for voice_id in voice_ids:
            await async_client.delete(f"/api/voices/{voice_id}")
        await async_client.delete(f"/api/engines/{engine_id}")
    
    @pytest.mark.asyncio
    async def test_error_handling_workflow(self, async_client: AsyncClient):
        """测试错误处理工作流"""
        # 测试使用不存在的引擎
        invalid_tts_request = {
            "text": "测试文本",
            "voice_id": "nonexistent-voice",
            "engine_id": "nonexistent-engine"
        }
        
        response = await async_client.post("/api/tts/synthesize", json=invalid_tts_request)
        assert response.status_code == 404
        
        # 测试无效的文本格式
        invalid_text_request = {
            "text": "",  # 空文本
            "voice_id": "test-voice",
            "engine_id": "test-engine"
        }
        
        response = await async_client.post("/api/tts/synthesize", json=invalid_text_request)
        assert response.status_code == 422
    
    @pytest.mark.asyncio
    async def test_concurrent_tts_requests(self, async_client: AsyncClient, sample_engine_data, sample_voice_data):
        """测试并发TTS请求"""
        # 创建引擎和声音
        engine_response = await async_client.post("/api/engines", json=sample_engine_data)
        engine_id = engine_response.json()["id"]
        
        voice_data = sample_voice_data.copy()
        voice_data["engine_id"] = engine_id
        voice_response = await async_client.post("/api/voices", json=voice_data)
        voice_id = voice_response.json()["id"]
        
        # 并发发送多个TTS请求
        tasks = []
        for i in range(5):
            tts_request = {
                "text": f"并发测试文本 {i}",
                "voice_id": voice_id,
                "engine_id": engine_id,
                "format": "wav"
            }
            task = async_client.post("/api/tts/synthesize", json=tts_request)
            tasks.append(task)
        
        responses = await asyncio.gather(*tasks)
        task_ids = []
        
        # 验证所有请求都成功
        for response in responses:
            assert response.status_code == 200
            task_ids.append(response.json()["task_id"])
        
        # 清理
        for task_id in task_ids:
            await async_client.delete(f"/api/tts/tasks/{task_id}")
        await async_client.delete(f"/api/voices/{voice_id}")
        await async_client.delete(f"/api/engines/{engine_id}")