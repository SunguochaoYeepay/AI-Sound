"""
健康检查和系统API测试
"""

import pytest
from httpx import AsyncClient
from fastapi.testclient import TestClient


class TestHealthAPI:
    """健康检查API测试类"""
    
    def test_root_endpoint(self, client: TestClient):
        """测试根路径"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "version" in data
        assert "status" in data
        assert data["status"] == "running"
    
    def test_health_check(self, client: TestClient):
        """测试健康检查"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "timestamp" in data
        assert "services" in data
        assert data["status"] == "healthy"
    
    def test_websocket_stats(self, client: TestClient):
        """测试WebSocket统计"""
        response = client.get("/ws/stats")
        assert response.status_code == 200
        data = response.json()
        assert "connected_clients" in data
        assert "total_connections" in data
        assert "active_rooms" in data


class TestSystemAPI:
    """系统API测试类"""
    
    def test_system_info(self, client: TestClient):
        """测试系统信息"""
        response = client.get("/api/system/info")
        assert response.status_code == 200
        data = response.json()
        assert "version" in data
        assert "uptime" in data
        assert "memory_usage" in data
        assert "cpu_usage" in data
    
    def test_system_stats(self, client: TestClient):
        """测试系统统计"""
        response = client.get("/api/system/stats")
        assert response.status_code == 200
        data = response.json()
        assert "total_requests" in data
        assert "active_tasks" in data
        assert "total_engines" in data
        assert "total_voices" in data
    
    def test_system_logs(self, client: TestClient):
        """测试系统日志"""
        response = client.get("/api/system/logs")
        assert response.status_code == 200
        data = response.json()
        assert "logs" in data
        assert isinstance(data["logs"], list)
    
    def test_system_config(self, client: TestClient):
        """测试系统配置"""
        response = client.get("/api/system/config")
        assert response.status_code == 200
        data = response.json()
        assert "database" in data
        assert "api" in data
        assert "tts" in data


@pytest.mark.asyncio
class TestHealthAPIAsync:
    """健康检查API异步测试类"""
    
    async def test_async_health_check(self, async_client: AsyncClient):
        """异步测试健康检查"""
        response = await async_client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
    
    async def test_async_system_info(self, async_client: AsyncClient):
        """异步测试系统信息"""
        response = await async_client.get("/api/system/info")
        assert response.status_code == 200
        data = response.json()
        assert "version" in data