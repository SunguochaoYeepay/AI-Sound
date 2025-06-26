"""
音频编辑器单元测试
验证MoviePy集成和API功能
"""

import pytest
import asyncio
import os
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock
import json

from fastapi.testclient import TestClient
from httpx import AsyncClient

# 导入待测试的模块
from app.services.moviepy_service import (
    MoviePyService,
    AudioMixConfig,
    AudioEffectConfig,
    ChapterAudioConfig
)
from app.schemas.audio_editor import (
    AudioMixRequest,
    ChapterAudioRequest,
    AudioEffectRequest
)
from main import app

class TestMoviePyService:
    """MoviePy服务单元测试"""
    
    @pytest.fixture
    def service(self):
        """创建服务实例"""
        return MoviePyService()
    
    @pytest.fixture
    def temp_dir(self):
        """创建临时目录"""
        temp_dir = Path(tempfile.mkdtemp())
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def mock_audio_files(self, temp_dir):
        """创建模拟音频文件"""
        dialogue_file = temp_dir / "dialogue.wav"
        environment_file = temp_dir / "environment.wav"
        
        # 创建空文件作为模拟
        dialogue_file.touch()
        environment_file.touch()
        
        return {
            "dialogue": str(dialogue_file),
            "environment": str(environment_file)
        }
    
    @pytest.mark.asyncio
    async def test_get_audio_info_file_not_exists(self, service):
        """测试获取不存在文件的音频信息"""
        with pytest.raises(Exception) as exc_info:
            await service.get_audio_info("nonexistent_file.wav")
        
        assert "音频文件不存在" in str(exc_info.value)
    
    def test_audio_mix_config_validation(self):
        """测试音频混合配置验证"""
        # 正常配置
        config = AudioMixConfig(
            dialogue_volume=1.0,
            environment_volume=0.3,
            fadein_duration=0.5,
            fadeout_duration=0.5
        )
        assert config.dialogue_volume == 1.0
        assert config.environment_volume == 0.3
        
        # 测试边界值
        config = AudioMixConfig(dialogue_volume=2.0)
        assert config.dialogue_volume == 2.0
    
    def test_chapter_audio_config_validation(self):
        """测试章节音频配置验证"""
        config = ChapterAudioConfig(
            silence_duration=1.0,
            normalize_volume=True,
            apply_fade=True,
            fade_duration=0.3
        )
        assert config.silence_duration == 1.0
        assert config.normalize_volume is True
    
    def test_audio_effect_config_validation(self):
        """测试音频效果配置验证"""
        config = AudioEffectConfig(
            volume=1.2,
            fadein=0.5,
            fadeout=1.0,
            normalize=True
        )
        assert config.volume == 1.2
        assert config.fadein == 0.5
        assert config.normalize is True
    
    @patch('app.services.moviepy_service.AudioFileClip')
    @pytest.mark.asyncio
    async def test_get_audio_info_success(self, mock_audio_clip, service, mock_audio_files):
        """测试成功获取音频信息"""
        # 模拟AudioFileClip
        mock_clip = MagicMock()
        mock_clip.duration = 120.5
        mock_clip.fps = 44100
        mock_clip.nchannels = 2
        mock_audio_clip.return_value = mock_clip
        
        # 测试获取音频信息
        info = await service.get_audio_info(mock_audio_files["dialogue"])
        
        assert info["duration"] == 120.5
        assert info["fps"] == 44100
        assert info["channels"] == 2
        assert "file_path" in info
        assert "file_size" in info
    
    def test_service_initialization(self, service):
        """测试服务初始化"""
        assert service.executor is not None
        assert service.temp_dir.exists()
    
    def test_cleanup_temp_files(self, service):
        """测试临时文件清理"""
        # 创建临时文件
        temp_file = service.temp_dir / "test_file.txt"
        temp_file.write_text("test content")
        assert temp_file.exists()
        
        # 清理临时文件
        service.cleanup_temp_files()
        
        # 验证文件已删除
        assert not temp_file.exists()

class TestAudioEditorAPI:
    """音频编辑器API测试"""
    
    @pytest.fixture
    def client(self):
        """创建测试客户端"""
        return TestClient(app)
    
    @pytest.fixture
    def async_client(self):
        """创建异步测试客户端"""
        return AsyncClient(app=app, base_url="http://test")
    
    def test_health_check(self, client):
        """测试健康检查端点"""
        response = client.get("/api/v1/audio-editor/health")
        assert response.status_code == 200
        
        data = response.json()
        assert "status" in data
        assert "moviepy_version" in data
        assert "timestamp" in data
    
    @pytest.mark.asyncio
    async def test_get_audio_info_invalid_file(self, async_client):
        """测试获取无效文件的音频信息"""
        async with async_client as ac:
            response = await ac.get(
                "/api/v1/audio-editor/audio-info",
                params={"audio_path": "nonexistent_file.wav"}
            )
        
        assert response.status_code == 400
        data = response.json()
        assert "音频文件不存在或格式不支持" in data["detail"]
    
    def test_upload_invalid_file_format(self, client):
        """测试上传无效格式文件"""
        # 创建一个文本文件作为无效格式
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as temp_file:
            temp_file.write(b"This is not an audio file")
            temp_file_path = temp_file.name
        
        try:
            with open(temp_file_path, "rb") as f:
                response = client.post(
                    "/api/v1/audio-editor/upload",
                    files={"file": ("test.txt", f, "text/plain")}
                )
            
            assert response.status_code == 400
            data = response.json()
            assert "不支持的文件格式" in data["detail"]
        
        finally:
            os.unlink(temp_file_path)
    
    def test_mix_audio_missing_files(self, client):
        """测试混合不存在的音频文件"""
        request_data = {
            "dialogue_path": "nonexistent_dialogue.wav",
            "environment_path": "nonexistent_environment.wav",
            "output_filename": "mixed_output.mp3"
        }
        
        response = client.post(
            "/api/v1/audio-editor/mix-audio",
            json=request_data
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "对话音频文件不存在或格式不支持" in data["detail"]
    
    def test_create_chapter_empty_files(self, client):
        """测试用空文件列表创建章节音频"""
        request_data = {
            "audio_files": [],
            "output_filename": "chapter_output.mp3"
        }
        
        response = client.post(
            "/api/v1/audio-editor/create-chapter",
            json=request_data
        )
        
        assert response.status_code == 422  # Validation error
    
    def test_apply_effects_invalid_file(self, client):
        """测试对无效文件应用音频效果"""
        request_data = {
            "input_path": "nonexistent_input.wav",
            "output_filename": "effects_output.mp3",
            "effects": {
                "volume": 1.5,
                "normalize": True
            }
        }
        
        response = client.post(
            "/api/v1/audio-editor/apply-effects",
            json=request_data
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "输入音频文件不存在或格式不支持" in data["detail"]
    
    def test_download_nonexistent_file(self, client):
        """测试下载不存在的文件"""
        response = client.get("/api/v1/audio-editor/download/nonexistent_file.mp3")
        assert response.status_code == 404
        
        data = response.json()
        assert "文件不存在" in data["detail"]
    
    def test_cleanup_temp_files(self, client):
        """测试清理临时文件"""
        response = client.delete("/api/v1/audio-editor/cleanup-temp")
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert "临时文件清理完成" in data["message"]

class TestAudioEditorSchemas:
    """音频编辑器数据模型测试"""
    
    def test_audio_mix_request_validation(self):
        """测试音频混合请求验证"""
        # 正常请求
        request = AudioMixRequest(
            dialogue_path="/path/to/dialogue.wav",
            environment_path="/path/to/environment.wav",
            output_filename="mixed_output.mp3"
        )
        assert request.dialogue_path == "/path/to/dialogue.wav"
        assert request.output_filename == "mixed_output.mp3"
        
        # 测试文件名验证
        with pytest.raises(ValueError) as exc_info:
            AudioMixRequest(
                dialogue_path="/path/to/dialogue.wav",
                environment_path="/path/to/environment.wav",
                output_filename=""  # 空文件名
            )
        assert "输出文件名不能为空" in str(exc_info.value)
        
        # 测试非法字符
        with pytest.raises(ValueError) as exc_info:
            AudioMixRequest(
                dialogue_path="/path/to/dialogue.wav",
                environment_path="/path/to/environment.wav",
                output_filename="output*.mp3"  # 包含非法字符
            )
        assert "文件名包含非法字符" in str(exc_info.value)
    
    def test_chapter_audio_request_validation(self):
        """测试章节音频请求验证"""
        # 正常请求
        request = ChapterAudioRequest(
            audio_files=["/path/to/audio1.wav", "/path/to/audio2.wav"],
            output_filename="chapter_output.mp3"
        )
        assert len(request.audio_files) == 2
        
        # 测试空文件列表
        with pytest.raises(ValueError):
            ChapterAudioRequest(
                audio_files=[],
                output_filename="chapter_output.mp3"
            )
    
    def test_audio_effect_request_validation(self):
        """测试音频效果请求验证"""
        request = AudioEffectRequest(
            input_path="/path/to/input.wav",
            output_filename="effects_output.mp3",
            effects=AudioEffectConfig(
                volume=1.2,
                normalize=True
            )
        )
        assert request.input_path == "/path/to/input.wav"
        assert request.effects.volume == 1.2
        assert request.effects.normalize is True

class TestIntegration:
    """集成测试"""
    
    @pytest.mark.asyncio
    async def test_moviepy_service_integration(self):
        """测试MoviePy服务集成"""
        service = MoviePyService()
        
        # 验证服务可以正常初始化
        assert service is not None
        assert service.executor is not None
        
        # 测试临时目录创建
        assert service.temp_dir.exists()
        
        # 清理测试
        service.cleanup_temp_files()
    
    def test_api_routing_integration(self, client):
        """测试API路由集成"""
        # 测试健康检查
        response = client.get("/api/v1/audio-editor/health")
        assert response.status_code == 200
        
        # 测试API文档是否包含新的路由
        response = client.get("/docs")
        assert response.status_code == 200

# 运行测试的辅助函数
def run_tests():
    """运行所有测试"""
    pytest.main([
        __file__,
        "-v",
        "--tb=short",
        "--capture=no"
    ])

if __name__ == "__main__":
    run_tests() 