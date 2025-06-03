"""
角色管理API测试
"""

import pytest
from httpx import AsyncClient
from fastapi.testclient import TestClient


class TestCharactersAPI:
    """角色API测试类"""
    
    def test_get_characters_list(self, client: TestClient):
        """测试获取角色列表"""
        response = client.get("/api/characters")
        assert response.status_code == 200
        data = response.json()
        assert "characters" in data
        assert isinstance(data["characters"], list)
        assert "total" in data
        assert "page" in data
        assert "size" in data
    
    def test_create_character(self, client: TestClient, sample_character_data):
        """测试创建角色"""
        response = client.post("/api/characters", json=sample_character_data)
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == sample_character_data["name"]
        assert data["display_name"] == sample_character_data["display_name"]
        assert "id" in data
        assert "created_at" in data
    
    def test_get_character_by_id(self, client: TestClient, sample_character_data):
        """测试根据ID获取角色"""
        # 先创建角色
        create_response = client.post("/api/characters", json=sample_character_data)
        character_id = create_response.json()["id"]
        
        # 获取角色
        response = client.get(f"/api/characters/{character_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == character_id
        assert data["name"] == sample_character_data["name"]
    
    def test_update_character(self, client: TestClient, sample_character_data):
        """测试更新角色"""
        # 先创建角色
        create_response = client.post("/api/characters", json=sample_character_data)
        character_id = create_response.json()["id"]
        
        # 更新角色
        update_data = {"description": "更新后的角色描述"}
        response = client.put(f"/api/characters/{character_id}", json=update_data)
        assert response.status_code == 200
        data = response.json()
        assert data["description"] == update_data["description"]
    
    def test_delete_character(self, client: TestClient, sample_character_data):
        """测试删除角色"""
        # 先创建角色
        create_response = client.post("/api/characters", json=sample_character_data)
        character_id = create_response.json()["id"]
        
        # 删除角色
        response = client.delete(f"/api/characters/{character_id}")
        assert response.status_code == 204
        
        # 验证已删除
        get_response = client.get(f"/api/characters/{character_id}")
        assert get_response.status_code == 404
    
    def test_add_voice_mapping(self, client: TestClient, sample_character_data):
        """测试添加声音映射"""
        # 先创建角色
        create_response = client.post("/api/characters", json=sample_character_data)
        character_id = create_response.json()["id"]
        
        # 添加声音映射
        mapping_data = {
            "voice_id": "test-voice-id",
            "emotion": "happy",
            "priority": 1,
            "conditions": {
                "text_type": "dialogue"
            }
        }
        response = client.post(f"/api/characters/{character_id}/voice-mappings", json=mapping_data)
        assert response.status_code == 201
        data = response.json()
        assert data["voice_id"] == mapping_data["voice_id"]
        assert data["emotion"] == mapping_data["emotion"]
    
    def test_get_voice_mappings(self, client: TestClient, sample_character_data):
        """测试获取声音映射"""
        # 先创建角色
        create_response = client.post("/api/characters", json=sample_character_data)
        character_id = create_response.json()["id"]
        
        # 获取声音映射
        response = client.get(f"/api/characters/{character_id}/voice-mappings")
        assert response.status_code == 200
        data = response.json()
        assert "mappings" in data
        assert isinstance(data["mappings"], list)
    
    def test_update_voice_mapping(self, client: TestClient, sample_character_data):
        """测试更新声音映射"""
        # 先创建角色和映射
        create_response = client.post("/api/characters", json=sample_character_data)
        character_id = create_response.json()["id"]
        
        mapping_data = {
            "voice_id": "test-voice-id",
            "emotion": "happy",
            "priority": 1
        }
        mapping_response = client.post(f"/api/characters/{character_id}/voice-mappings", json=mapping_data)
        mapping_id = mapping_response.json()["id"]
        
        # 更新映射
        update_data = {"priority": 2, "emotion": "sad"}
        response = client.put(f"/api/characters/{character_id}/voice-mappings/{mapping_id}", json=update_data)
        assert response.status_code == 200
        data = response.json()
        assert data["priority"] == 2
        assert data["emotion"] == "sad"
    
    def test_delete_voice_mapping(self, client: TestClient, sample_character_data):
        """测试删除声音映射"""
        # 先创建角色和映射
        create_response = client.post("/api/characters", json=sample_character_data)
        character_id = create_response.json()["id"]
        
        mapping_data = {
            "voice_id": "test-voice-id",
            "emotion": "happy",
            "priority": 1
        }
        mapping_response = client.post(f"/api/characters/{character_id}/voice-mappings", json=mapping_data)
        mapping_id = mapping_response.json()["id"]
        
        # 删除映射
        response = client.delete(f"/api/characters/{character_id}/voice-mappings/{mapping_id}")
        assert response.status_code == 204
    
    def test_character_voice_test(self, client: TestClient, sample_character_data):
        """测试角色声音测试"""
        # 先创建角色
        create_response = client.post("/api/characters", json=sample_character_data)
        character_id = create_response.json()["id"]
        
        # 测试角色声音
        test_data = {
            "text": "这是角色声音测试",
            "emotion": "happy",
            "scene_type": "dialogue"
        }
        response = client.post(f"/api/characters/{character_id}/voice-test", json=test_data)
        assert response.status_code == 200
        data = response.json()
        assert "audio_url" in data
        assert "voice_id" in data
        assert "emotion" in data
    
    def test_search_characters(self, client: TestClient):
        """测试搜索角色"""
        search_params = {
            "q": "测试",
            "gender": "female",
            "type": "protagonist"
        }
        response = client.get("/api/characters/search", params=search_params)
        assert response.status_code == 200
        data = response.json()
        assert "characters" in data
        assert "total" in data
    
    def test_character_stats(self, client: TestClient, sample_character_data):
        """测试角色统计"""
        # 先创建角色
        create_response = client.post("/api/characters", json=sample_character_data)
        character_id = create_response.json()["id"]
        
        # 获取统计
        response = client.get(f"/api/characters/{character_id}/stats")
        assert response.status_code == 200
        data = response.json()
        assert "total_usage" in data
        assert "voice_mappings_count" in data
        assert "most_used_emotion" in data
    
    def test_batch_update_characters(self, client: TestClient, sample_character_data):
        """测试批量更新角色"""
        # 创建多个角色
        character_ids = []
        for i in range(3):
            char_data = sample_character_data.copy()
            char_data["name"] = f"test-character-{i}"
            response = client.post("/api/characters", json=char_data)
            character_ids.append(response.json()["id"])
        
        # 批量更新
        update_data = {
            "character_ids": character_ids,
            "updates": {"type": "supporting"}
        }
        response = client.put("/api/characters/batch", json=update_data)
        assert response.status_code == 200
        data = response.json()
        assert data["updated_count"] == 3


@pytest.mark.asyncio
class TestCharactersAPIAsync:
    """角色API异步测试类"""
    
    async def test_async_get_characters(self, async_client: AsyncClient):
        """异步测试获取角色列表"""
        response = await async_client.get("/api/characters")
        assert response.status_code == 200
        data = response.json()
        assert "characters" in data
    
    async def test_async_create_character(self, async_client: AsyncClient, sample_character_data):
        """异步测试创建角色"""
        response = await async_client.post("/api/characters", json=sample_character_data)
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == sample_character_data["name"]