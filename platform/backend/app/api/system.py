#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
系统设置API接口
支持站点基本信息、AI服务配置、存储设置等功能
"""

import os
import json
import aiohttp
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import Dict, Any
from datetime import datetime

from ..database import get_db
from ..utils import log_system_event
from ..config import get_environment_config

router = APIRouter(prefix="/system", tags=["系统设置"])

# 配置目录
CONFIG_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config", "data")

@router.get("/settings")
async def get_system_settings():
    """
    获取系统设置
    包括站点基本信息、AI服务配置、存储设置等
    """
    try:
        settings_file = os.path.join(CONFIG_DIR, "system_settings.json")
        
        # 默认设置
        default_settings = {
            "site": {
                "siteName": "AI-Sound 智能语音平台",
                "siteSubtitle": "专业的AI语音合成解决方案", 
                "siteDescription": "基于最新AI技术的语音合成平台，支持多种语音模型、情感表达和个性化定制，为您提供专业的语音解决方案。",
                "adminEmail": "admin@ai-sound.com",
                "supportContact": "support@ai-sound.com",
                "logo": "",
                "favicon": ""
            },
            "ai": {
                "ttsServiceUrl": "http://localhost:7929",
                "concurrentLimit": 3,
                "ollamaServiceUrl": "http://localhost:11434", 
                "defaultLlmModel": "qwen:latest",
        
            },
            "storage": {
                "audioRetentionDays": 30,
                "maxFileSize": 100,  # MB
                "cleanupInterval": "weekly",
                "enableAutoBackup": True
            }
        }
        
        if os.path.exists(settings_file):
            try:
                with open(settings_file, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                # 合并默认设置确保所有字段都存在
                for category, defaults in default_settings.items():
                    if category not in settings:
                        settings[category] = defaults
                    else:
                        for key, default_value in defaults.items():
                            if key not in settings[category]:
                                settings[category][key] = default_value
            except json.JSONDecodeError:
                settings = default_settings
        else:
            settings = default_settings
            # 创建配置目录和默认配置文件
            os.makedirs(CONFIG_DIR, exist_ok=True)
            with open(settings_file, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=2, ensure_ascii=False)
        
        return {
            "success": True,
            "data": settings
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取系统设置失败: {str(e)}")

@router.put("/settings")
async def update_system_settings(
    settings_data: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """
    更新系统设置
    """
    try:
        # 验证设置数据结构
        required_categories = ["site", "ai", "storage"]
        for category in required_categories:
            if category not in settings_data:
                raise HTTPException(status_code=400, detail=f"缺少设置分类: {category}")
        
        # 保存到配置文件
        os.makedirs(CONFIG_DIR, exist_ok=True)
        settings_file = os.path.join(CONFIG_DIR, "system_settings.json")
        
        with open(settings_file, 'w', encoding='utf-8') as f:
            json.dump(settings_data, f, indent=2, ensure_ascii=False)
        
        # 记录系统事件
        await log_system_event(
            db=db,
            level="info",
            message="系统设置已更新",
            module="system",
            details={
                "updated_categories": list(settings_data.keys()),
                "updated_at": datetime.now().isoformat()
            }
        )
        
        return {
            "success": True,
            "message": "系统设置更新成功",
            "data": settings_data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新系统设置失败: {str(e)}")

@router.post("/test-tts")
async def test_tts_service():
    """
    测试TTS服务连接
    """
    try:
        # 获取TTS服务配置
        settings_file = os.path.join(CONFIG_DIR, "system_settings.json")
        if os.path.exists(settings_file):
            with open(settings_file, 'r', encoding='utf-8') as f:
                settings = json.load(f)
                tts_url = settings.get("ai", {}).get("ttsServiceUrl", "http://localhost:7929")
        else:
            tts_url = "http://localhost:7929"
        
        # 测试连接
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{tts_url}/health", timeout=10) as response:
                if response.status == 200:
                    return {
                        "success": True,
                        "message": "TTS服务连接正常",
                        "data": {
                            "url": tts_url,
                            "status": "healthy",
                            "response_time": "< 10s"
                        }
                    }
                else:
                    raise HTTPException(status_code=503, detail=f"TTS服务响应异常: {response.status}")
    
    except aiohttp.ClientTimeout:
        raise HTTPException(status_code=408, detail="TTS服务连接超时")
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"TTS服务测试失败: {str(e)}")

@router.post("/test-ollama")
async def test_ollama_service():
    """
    测试Ollama服务连接
    """
    try:
        # 获取Ollama服务配置
        settings_file = os.path.join(CONFIG_DIR, "system_settings.json")
        if os.path.exists(settings_file):
            with open(settings_file, 'r', encoding='utf-8') as f:
                settings = json.load(f)
                ollama_url = settings.get("ai", {}).get("ollamaServiceUrl", "http://localhost:11434")
        else:
            ollama_url = "http://localhost:11434"
        
        # 测试连接
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{ollama_url}/api/tags", timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    models = [model["name"] for model in data.get("models", [])]
                    return {
                        "success": True,
                        "message": "Ollama服务连接正常",
                        "data": {
                            "url": ollama_url,
                            "status": "healthy",
                            "available_models": models[:5]  # 只显示前5个模型
                        }
                    }
                else:
                    raise HTTPException(status_code=503, detail=f"Ollama服务响应异常: {response.status}")
    
    except aiohttp.ClientTimeout:
        raise HTTPException(status_code=408, detail="Ollama服务连接超时")
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Ollama服务测试失败: {str(e)}")

@router.post("/clear-cache")
async def clear_system_cache(db: Session = Depends(get_db)):
    """
    清理系统缓存
    """
    try:
        cache_cleared = []
        
        # 清理临时音频文件
        temp_audio_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "temp_audio")
        if os.path.exists(temp_audio_dir):
            import shutil
            file_count = len([f for f in os.listdir(temp_audio_dir) if os.path.isfile(os.path.join(temp_audio_dir, f))])
            shutil.rmtree(temp_audio_dir)
            os.makedirs(temp_audio_dir, exist_ok=True)
            cache_cleared.append(f"临时音频文件: {file_count}个")
        
        # 清理日志缓存（可选）
        log_cache_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs", "cache")
        if os.path.exists(log_cache_dir):
            import shutil
            cache_size = sum(os.path.getsize(os.path.join(log_cache_dir, f)) 
                           for f in os.listdir(log_cache_dir) 
                           if os.path.isfile(os.path.join(log_cache_dir, f)))
            shutil.rmtree(log_cache_dir)
            os.makedirs(log_cache_dir, exist_ok=True)
            cache_cleared.append(f"日志缓存: {cache_size // 1024}KB")
        
        # 记录清理事件
        await log_system_event(
            db=db,
            level="info",
            message="系统缓存清理完成",
            module="system",
            details={
                "cleared_items": cache_cleared,
                "cleared_at": datetime.now().isoformat()
            }
        )
        
        return {
            "success": True,
            "message": "系统缓存清理完成",
            "data": {
                "cleared_items": cache_cleared,
                "total_cleared": len(cache_cleared)
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"清理缓存失败: {str(e)}")

@router.get("/status")
async def get_system_status():
    """
    获取系统运行状态
    """
    try:
        status = {
            "database": "unknown",
            "tts_service": "unknown", 
            "ollama_service": "unknown",
            "last_check": datetime.now().isoformat()
        }
        
        # 检查数据库状态
        try:
            # 这里可以添加数据库连接测试
            status["database"] = "healthy"
        except:
            status["database"] = "unhealthy"
        
        # 检查TTS服务状态
        try:
            settings_file = os.path.join(CONFIG_DIR, "system_settings.json")
            if os.path.exists(settings_file):
                with open(settings_file, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                    tts_url = settings.get("ai", {}).get("ttsServiceUrl", "http://localhost:7929")
            else:
                tts_url = "http://localhost:7929"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{tts_url}/health", timeout=5) as response:
                    if response.status == 200:
                        status["tts_service"] = "healthy"
                    else:
                        status["tts_service"] = "degraded"
        except:
            status["tts_service"] = "unhealthy"
        
        # 检查Ollama服务状态
        try:
            settings_file = os.path.join(CONFIG_DIR, "system_settings.json")
            if os.path.exists(settings_file):
                with open(settings_file, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                    ollama_url = settings.get("ai", {}).get("ollamaServiceUrl", "http://localhost:11434")
            else:
                ollama_url = "http://localhost:11434"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{ollama_url}/api/tags", timeout=5) as response:
                    if response.status == 200:
                        status["ollama_service"] = "healthy"
                    else:
                        status["ollama_service"] = "degraded"
        except:
            status["ollama_service"] = "unhealthy"
        
        return {
            "success": True,
            "data": status
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取系统状态失败: {str(e)}")

@router.get("/version")
async def get_system_version():
    """
    获取系统版本信息
    """
    try:
        # 读取版本信息
        version_file = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "version.json")
        
        default_version = {
            "version": "2.0.0",
            "build_time": "2024-01-23 15:30:00",
            "git_commit": "unknown",
            "environment": "development"
        }
        
        if os.path.exists(version_file):
            try:
                with open(version_file, 'r', encoding='utf-8') as f:
                    version_info = json.load(f)
            except:
                version_info = default_version
        else:
            version_info = default_version
        
        # 计算运行时长（简化版）
        start_time = datetime.fromisoformat(version_info["build_time"].replace(" ", "T"))
        uptime = datetime.now() - start_time
        
        uptime_str = f"{uptime.days}天 {uptime.seconds // 3600}小时 {(uptime.seconds % 3600) // 60}分钟"
        
        return {
            "success": True,
            "data": {
                **version_info,
                "uptime": uptime_str
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取版本信息失败: {str(e)}")