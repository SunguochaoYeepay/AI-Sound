"""
声音管理API测试
"""

import pytest
from httpx import AsyncClient
from fastapi.testclient import TestClient
import io


class TestVoicesAPI:
    """声音API测试类"""
    
    def test_get_voices_list(self, client: TestClient):
        """测试获取声音列表"""
        response = client.get("/api/voices")
        assert response.status_code == 200
        data = response.json()
        assert "voices" in data
        assert isinstance(data["voices"], list)
        assert "total" in data
        assert "page" in data
        assert "size" in data
    
    def test_create_voice(self, client: TestClient, sample_voice_data):
        """测试创建声音"""
        response = client.post("/api/voices", json=sample_voice_data)
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == sample_voice_data["name"]
        assert data["display_name"] == sample_voice_data["display_name"]
        assert "id" in data
        assert "created_at" in data
    
    def test_get_voice_by_id(self, client: TestClient, sample_voice_data):
        """测试根据ID获取声音"""
        # 先创建声音
        create_response = client.post("/api/voices", json=sample_voice_data)
        voice_id = create_response.json()["id"]
        
        # 获取声音
        response = client.get(f"/api/voices/{voice_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == voice_id
        assert data["name"] == sample_voice_data["name"]
    
    def test_update_voice(self, client: TestClient, sample_voice_data):
        """测试更新声音"""
        # 先创建声音
        create_response = client.post("/api/voices", json=sample_voice_data)
        voice_id = create_response.json()["id"]
        
        # 更新声音
        update_data = {"description": "更新后的声音描述"}
        response = client.put(f"/api/voices/{voice_id}", json=update_data)
        assert response.status_code == 200
        data = response.json()
        assert data["description"] == update_data["description"]
    
    def test_delete_voice(self, client: TestClient, sample_voice_data):
        """测试删除声音"""
        # 先创建声音
        create_response = client.post("/api/voices", json=sample_voice_data)
        voice_id = create_response.json()["id"]
        
        # 删除声音
        response = client.delete(f"/api/voices/{voice_id}")
        assert response.status_code == 204
        
        # 验证已删除
        get_response = client.get(f"/api/voices/{voice_id}")
        assert get_response.status_code == 404
    
    def test_voice_preview(self, client: TestClient, sample_voice_data):
        """测试声音预览"""
        # 先创建声音
        create_response = client.post("/api/voices", json=sample_voice_data)
        voice_id = create_response.json()["id"]
        
        # 预览声音
        preview_data = {
            "text": "这是声音预览测试",
            "duration": 5
        }
        response = client.post(f"/api/voices/{voice_id}/preview", json=preview_data)
        assert response.status_code == 200
        data = response.json()
        assert "audio_url" in data
        assert "duration" in data
    
    def test_upload_voice_file(self, client: TestClient):
        """测试上传声音文件"""
        # 创建模拟音频文件
        audio_content = b"fake audio content"
        files = {
            "file": ("test_voice.wav", io.BytesIO(audio_content), "audio/wav")
        }
        data = {
            "name": "uploaded_voice",
            "display_name": "上传的声音",
            "engine_id": "test-engine"
        }
        
        response = client.post("/api/voices/upload", files=files, data=data)
        assert response.status_code == 201
        result = response.json()
        assert result["name"] == "uploaded_voice"
        assert "id" in result
    
    def test_voice_analysis(self, client: TestClient, sample_voice_data):
        """测试声音分析"""
        # 先创建声音
        create_response = client.post("/api/voices", json=sample_voice_data)
        voice_id = create_response.json()["id"]
        
        # 分析声音
        response = client.post(f"/api/voices/{voice_id}/analyze")
        assert response.status_code == 200
        data = response.json()
        assert "features" in data
        assert "quality_score" in data
    
    def test_search_voices(self, client: TestClient):
        """测试搜索声音"""
        search_params = {
            "q": "测试",
            "gender": "female",
            "language": "zh-CN"
        }
        response = client.get("/api/voices/search", params=search_params)
        assert response.status_code == 200
        data = response.json()
        assert "voices" in data
        assert "total" in data
    
    def test_get_voices_by_engine(self, client: TestClient):
        """测试根据引擎获取声音"""
        engine_id = "test-engine-id"
        response = client.get(f"/api/voices/engine/{engine_id}")
        assert response.status_code == 200
        data = response.json()
        assert "voices" in data
        assert isinstance(data["voices"], list)
    
    def test_voice_stats(self, client: TestClient, sample_voice_data):
        """测试声音统计"""
        # 先创建声音
        create_response = client.post("/api/voices", json=sample_voice_data)
        voice_id = create_response.json()["id"]
        
        # 获取统计
        response = client.get(f"/api/voices/{voice_id}/stats")
        assert response.status_code == 200
        data = response.json()
        assert "usage_count" in data
        assert "total_duration" in data
    
    def test_batch_delete_voices(self, client: TestClient, sample_voice_data):
        """测试批量删除声音"""
        # 创建多个声音
        voice_ids = []
        for i in range(3):
            voice_data = sample_voice_data.copy()
            voice_data["name"] = f"test-voice-{i}"
            response = client.post("/api/voices", json=voice_data)
            voice_ids.append(response.json()["id"])
        
        # 批量删除
        delete_data = {"voice_ids": voice_ids}
        response = client.delete("/api/voices/batch", json=delete_data)
        assert response.status_code == 200
        data = response.json()
        assert data["deleted_count"] == 3


@pytest.mark.asyncio
class TestVoicesAPIAsync:
    """声音API异步测试类"""
    
    async def test_async_get_voices(self, async_client: AsyncClient):
        """异步测试获取声音列表"""
        response = await async_client.get("/api/voices")
        assert response.status_code == 200
        data = response.json()
        assert "voices" in data
    
    async def test_async_create_voice(self, async_client: AsyncClient, sample_voice_data):
        """异步测试创建声音"""
        response = await async_client.post("/api/voices", json=sample_voice_data)
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == sample_voice_data["name"]