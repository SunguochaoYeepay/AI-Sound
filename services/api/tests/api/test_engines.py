"""
引擎管理API测试
"""

import pytest
from httpx import AsyncClient
from fastapi.testclient import TestClient


class TestEnginesAPI:
    """引擎API测试类"""
    
    def test_get_engines_list(self, client: TestClient):
        """测试获取引擎列表"""
        response = client.get("/api/engines")
        assert response.status_code == 200
        data = response.json()
        assert "engines" in data
        assert isinstance(data["engines"], list)
    
    def test_create_engine(self, client: TestClient, sample_engine_data):
        """测试创建引擎"""
        response = client.post("/api/engines", json=sample_engine_data)
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == sample_engine_data["name"]
        assert data["type"] == sample_engine_data["type"]
        assert "id" in data
        assert "created_at" in data
    
    def test_get_engine_by_id(self, client: TestClient, sample_engine_data):
        """测试根据ID获取引擎"""
        # 先创建引擎
        create_response = client.post("/api/engines", json=sample_engine_data)
        engine_id = create_response.json()["id"]
        
        # 获取引擎
        response = client.get(f"/api/engines/{engine_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == engine_id
        assert data["name"] == sample_engine_data["name"]
    
    def test_update_engine(self, client: TestClient, sample_engine_data):
        """测试更新引擎"""
        # 先创建引擎
        create_response = client.post("/api/engines", json=sample_engine_data)
        engine_id = create_response.json()["id"]
        
        # 更新引擎
        update_data = {"description": "更新后的描述"}
        response = client.put(f"/api/engines/{engine_id}", json=update_data)
        assert response.status_code == 200
        data = response.json()
        assert data["description"] == update_data["description"]
    
    def test_delete_engine(self, client: TestClient, sample_engine_data):
        """测试删除引擎"""
        # 先创建引擎
        create_response = client.post("/api/engines", json=sample_engine_data)
        engine_id = create_response.json()["id"]
        
        # 删除引擎
        response = client.delete(f"/api/engines/{engine_id}")
        assert response.status_code == 204
        
        # 验证已删除
        get_response = client.get(f"/api/engines/{engine_id}")
        assert get_response.status_code == 404
    
    def test_engine_health_check(self, client: TestClient, sample_engine_data):
        """测试引擎健康检查"""
        # 先创建引擎
        create_response = client.post("/api/engines", json=sample_engine_data)
        engine_id = create_response.json()["id"]
        
        # 健康检查
        response = client.get(f"/api/engines/{engine_id}/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "timestamp" in data
    
    def test_engine_test(self, client: TestClient, sample_engine_data):
        """测试引擎测试接口"""
        # 先创建引擎
        create_response = client.post("/api/engines", json=sample_engine_data)
        engine_id = create_response.json()["id"]
        
        # 测试引擎
        test_data = {
            "text": "测试文本",
            "voice_id": "test_voice"
        }
        response = client.post(f"/api/engines/{engine_id}/test", json=test_data)
        assert response.status_code == 200
        data = response.json()
        assert "result" in data
    
    def test_get_engine_config(self, client: TestClient, sample_engine_data):
        """测试获取引擎配置"""
        # 先创建引擎
        create_response = client.post("/api/engines", json=sample_engine_data)
        engine_id = create_response.json()["id"]
        
        # 获取配置
        response = client.get(f"/api/engines/{engine_id}/config")
        assert response.status_code == 200
        data = response.json()
        assert "config" in data
    
    def test_update_engine_config(self, client: TestClient, sample_engine_data):
        """测试更新引擎配置"""
        # 先创建引擎
        create_response = client.post("/api/engines", json=sample_engine_data)
        engine_id = create_response.json()["id"]
        
        # 更新配置
        new_config = {
            "model_path": "/new/model.pth",
            "batch_size": 2
        }
        response = client.put(f"/api/engines/{engine_id}/config", json=new_config)
        assert response.status_code == 200
        data = response.json()
        assert data["config"]["batch_size"] == 2
    
    def test_get_engine_stats(self, client: TestClient, sample_engine_data):
        """测试获取引擎统计"""
        # 先创建引擎
        create_response = client.post("/api/engines", json=sample_engine_data)
        engine_id = create_response.json()["id"]
        
        # 获取统计
        response = client.get(f"/api/engines/{engine_id}/stats")
        assert response.status_code == 200
        data = response.json()
        assert "total_requests" in data
        assert "success_rate" in data


@pytest.mark.asyncio
class TestEnginesAPIAsync:
    """引擎API异步测试类"""
    
    async def test_async_get_engines(self, async_client: AsyncClient):
        """异步测试获取引擎列表"""
        response = await async_client.get("/api/engines")
        assert response.status_code == 200
        data = response.json()
        assert "engines" in data
    
    async def test_async_create_engine(self, async_client: AsyncClient, sample_engine_data):
        """异步测试创建引擎"""
        response = await async_client.post("/api/engines", json=sample_engine_data)
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == sample_engine_data["name"]