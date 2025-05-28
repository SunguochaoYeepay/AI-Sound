"""
TTS合成API测试
"""

import pytest
from httpx import AsyncClient
from fastapi.testclient import TestClient
import io


class TestTTSAPI:
    """TTS API测试类"""
    
    def test_synthesize_text(self, client: TestClient, sample_tts_request):
        """测试文本合成"""
        response = client.post("/api/tts/synthesize", json=sample_tts_request)
        assert response.status_code == 200
        data = response.json()
        assert "task_id" in data
        assert "status" in data
        assert data["status"] == "pending"
    
    def test_batch_synthesize(self, client: TestClient):
        """测试批量合成"""
        batch_data = {
            "texts": [
                {"text": "第一段文本", "voice_id": "voice1"},
                {"text": "第二段文本", "voice_id": "voice2"},
                {"text": "第三段文本", "voice_id": "voice1"}
            ],
            "format": "wav",
            "sample_rate": 22050,
            "merge_output": True
        }
        response = client.post("/api/tts/batch-synthesize", json=batch_data)
        assert response.status_code == 200
        data = response.json()
        assert "batch_id" in data
        assert "tasks" in data
        assert len(data["tasks"]) == 3
    
    def test_get_task_status(self, client: TestClient, sample_tts_request):
        """测试获取任务状态"""
        # 先创建任务
        response = client.post("/api/tts/synthesize", json=sample_tts_request)
        task_id = response.json()["task_id"]
        
        # 获取任务状态
        status_response = client.get(f"/api/tts/tasks/{task_id}")
        assert status_response.status_code == 200
        data = status_response.json()
        assert data["id"] == task_id
        assert "status" in data
        assert "progress" in data
    
    def test_get_task_result(self, client: TestClient, sample_tts_request):
        """测试获取任务结果"""
        # 先创建任务
        response = client.post("/api/tts/synthesize", json=sample_tts_request)
        task_id = response.json()["task_id"]
        
        # 获取任务结果
        result_response = client.get(f"/api/tts/tasks/{task_id}/result")
        # 注意：实际测试中任务可能还在处理中，所以可能返回202或200
        assert result_response.status_code in [200, 202]
    
    def test_cancel_task(self, client: TestClient, sample_tts_request):
        """测试取消任务"""
        # 先创建任务
        response = client.post("/api/tts/synthesize", json=sample_tts_request)
        task_id = response.json()["task_id"]
        
        # 取消任务
        cancel_response = client.post(f"/api/tts/tasks/{task_id}/cancel")
        assert cancel_response.status_code == 200
        data = cancel_response.json()
        assert data["status"] == "cancelled"
    
    def test_get_tasks_list(self, client: TestClient):
        """测试获取任务列表"""
        response = client.get("/api/tts/tasks")
        assert response.status_code == 200
        data = response.json()
        assert "tasks" in data
        assert "total" in data
        assert "page" in data
        assert "size" in data
    
    def test_delete_task(self, client: TestClient, sample_tts_request):
        """测试删除任务"""
        # 先创建任务
        response = client.post("/api/tts/synthesize", json=sample_tts_request)
        task_id = response.json()["task_id"]
        
        # 删除任务
        delete_response = client.delete(f"/api/tts/tasks/{task_id}")
        assert delete_response.status_code == 204
        
        # 验证已删除
        get_response = client.get(f"/api/tts/tasks/{task_id}")
        assert get_response.status_code == 404
    
    def test_get_supported_formats(self, client: TestClient):
        """测试获取支持的音频格式"""
        response = client.get("/api/tts/formats")
        assert response.status_code == 200
        data = response.json()
        assert "formats" in data
        assert isinstance(data["formats"], list)
        assert len(data["formats"]) > 0
    
    def test_get_supported_engines(self, client: TestClient):
        """测试获取支持的引擎"""
        response = client.get("/api/tts/engines")
        assert response.status_code == 200
        data = response.json()
        assert "engines" in data
        assert isinstance(data["engines"], list)
    
    def test_estimate_duration(self, client: TestClient):
        """测试估算合成时长"""
        estimate_data = {
            "text": "这是一个用于估算时长的测试文本，包含多个句子。",
            "voice_id": "test-voice",
            "speed": 1.0
        }
        response = client.post("/api/tts/estimate", json=estimate_data)
        assert response.status_code == 200
        data = response.json()
        assert "estimated_duration" in data
        assert "character_count" in data
        assert "word_count" in data
    
    def test_validate_text(self, client: TestClient):
        """测试文本验证"""
        validate_data = {
            "text": "这是一个测试文本",
            "engine_id": "test-engine"
        }
        response = client.post("/api/tts/validate", json=validate_data)
        assert response.status_code == 200
        data = response.json()
        assert "is_valid" in data
        assert "issues" in data
    
    def test_get_queue_status(self, client: TestClient):
        """测试获取队列状态"""
        response = client.get("/api/tts/queue/status")
        assert response.status_code == 200
        data = response.json()
        assert "pending_tasks" in data
        assert "running_tasks" in data
        assert "completed_tasks" in data
    
    def test_clear_completed_tasks(self, client: TestClient):
        """测试清理已完成任务"""
        response = client.delete("/api/tts/tasks/completed")
        assert response.status_code == 200
        data = response.json()
        assert "deleted_count" in data
    
    def test_retry_failed_task(self, client: TestClient, sample_tts_request):
        """测试重试失败任务"""
        # 先创建任务
        response = client.post("/api/tts/synthesize", json=sample_tts_request)
        task_id = response.json()["task_id"]
        
        # 重试任务
        retry_response = client.post(f"/api/tts/tasks/{task_id}/retry")
        assert retry_response.status_code == 200
        data = retry_response.json()
        assert "new_task_id" in data
    
    def test_download_audio(self, client: TestClient, sample_tts_request):
        """测试下载音频文件"""
        # 先创建任务
        response = client.post("/api/tts/synthesize", json=sample_tts_request)
        task_id = response.json()["task_id"]
        
        # 尝试下载音频（可能需要等待任务完成）
        download_response = client.get(f"/api/tts/tasks/{task_id}/download")
        # 任务可能还在处理中，所以可能返回202
        assert download_response.status_code in [200, 202, 404]


@pytest.mark.asyncio
class TestTTSAPIAsync:
    """TTS API异步测试类"""
    
    async def test_async_synthesize(self, async_client: AsyncClient, sample_tts_request):
        """异步测试文本合成"""
        response = await async_client.post("/api/tts/synthesize", json=sample_tts_request)
        assert response.status_code == 200
        data = response.json()
        assert "task_id" in data
    
    async def test_async_batch_synthesize(self, async_client: AsyncClient):
        """异步测试批量合成"""
        batch_data = {
            "texts": [
                {"text": "异步测试文本1", "voice_id": "voice1"},
                {"text": "异步测试文本2", "voice_id": "voice2"}
            ],
            "format": "wav"
        }
        response = await async_client.post("/api/tts/batch-synthesize", json=batch_data)
        assert response.status_code == 200
        data = response.json()
        assert "batch_id" in data
        assert "tasks" in data


class TestTTSWebSocket:
    """TTS WebSocket测试类"""
    
    def test_websocket_connection(self, client: TestClient):
        """测试WebSocket连接"""
        with client.websocket_connect("/ws/test-client") as websocket:
            # 发送订阅消息
            websocket.send_json({
                "type": "subscribe",
                "message_types": ["task_progress", "task_completed"]
            })
            
            # 发送心跳
            websocket.send_json({"type": "ping"})
            response = websocket.receive_json()
            assert response["type"] == "pong"
    
    def test_websocket_task_notifications(self, client: TestClient, sample_tts_request):
        """测试WebSocket任务通知"""
        with client.websocket_connect("/ws/test-client") as websocket:
            # 订阅任务通知
            websocket.send_json({
                "type": "subscribe",
                "message_types": ["task_progress", "task_completed"]
            })
            
            # 创建TTS任务
            response = client.post("/api/tts/synthesize", json=sample_tts_request)
            task_id = response.json()["task_id"]
            
            # 等待WebSocket通知（在实际测试中可能需要模拟）
            # 这里只是验证连接正常
            assert task_id is not None