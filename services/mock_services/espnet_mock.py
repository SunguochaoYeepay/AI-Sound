#!/usr/bin/env python3
"""
ESPnet 模拟服务，用于测试
提供与真实 ESPnet 服务兼容的 API
"""

import os
import time
import json
import random
import logging
import numpy as np
from typing import Dict, List, Any, Optional

from fastapi import FastAPI, HTTPException, File, UploadFile, Form
from fastapi.responses import FileResponse, Response
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger("espnet_mock")

# 创建 FastAPI 应用
app = FastAPI(
    title="ESPnet Mock API",
    description="ESPnet 模拟服务 API",
    version="1.0.0",
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 模拟数据
voices = {
    "espnet_female_1": {
        "id": "espnet_female_1",
        "name": "ESPnet女声1",
        "gender": "female",
        "age_group": "young",
        "description": "ESPnet标准女声，清亮自然",
        "language": "zh-CN",
        "version": "1.0.0",
    },
    "espnet_female_2": {
        "id": "espnet_female_2",
        "name": "ESPnet女声2",
        "gender": "female",
        "age_group": "middle",
        "description": "ESPnet成熟女声，优雅舒缓",
        "language": "zh-CN",
        "version": "1.0.0",
    },
    "espnet_male_1": {
        "id": "espnet_male_1",
        "name": "ESPnet男声1",
        "gender": "male",
        "age_group": "young",
        "description": "ESPnet标准男声，低沉有力",
        "language": "zh-CN",
        "version": "1.0.0",
    }
}

emotions = {
    "neutral": {
        "id": "neutral",
        "name": "中性",
        "description": "平静无明显情感",
    },
    "happy": {
        "id": "happy",
        "name": "愉快",
        "description": "愉快、开心的情绪",
    },
    "sad": {
        "id": "sad",
        "name": "悲伤",
        "description": "悲伤、沮丧的情绪",
    }
}

# 创建临时目录
os.makedirs("./temp", exist_ok=True)

# 创建音频样本
sample_rate = 24000  # ESPnet的采样率通常是24kHz
sample_audio = np.sin(2 * np.pi * 440 * np.arange(0, 3 * sample_rate) / sample_rate).astype(np.float32)

@app.get("/")
async def root():
    """根路径"""
    return {
        "name": "ESPnet Mock Service",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/health")
async def health():
    """健康检查"""
    return {
        "status": "ok",
        "version": "1.0.0",
        "uptime": 1000,  # 模拟运行时间
        "memory_usage": {
            "total": 1024 * 1024 * 1024,
            "used": 512 * 1024 * 1024,
            "free": 512 * 1024 * 1024,
        },
        "gpu": {
            "available": True,
            "id": 0,
            "name": "NVIDIA Mock GPU",
            "memory": {
                "total": 8 * 1024 * 1024 * 1024,
                "used": 2 * 1024 * 1024 * 1024,
                "free": 6 * 1024 * 1024 * 1024,
            }
        }
    }

@app.post("/api/tts")
async def tts(
    text: str = Form(...),
    voice_id: str = Form("espnet_female_1"),
    emotion_type: str = Form("neutral"),
    emotion_intensity: float = Form(0.5),
    speed_scale: float = Form(1.0),
    pitch_scale: float = Form(1.0),
    output_format: str = Form("wav"),
):
    """文本转语音"""
    logger.info(f"收到TTS请求：{text[:30]}... (voice={voice_id}, emotion={emotion_type})")
    
    # 检查参数
    if voice_id not in voices:
        raise HTTPException(status_code=400, detail=f"无效的音色ID: {voice_id}")
    
    if emotion_type not in emotions:
        raise HTTPException(status_code=400, detail=f"无效的情感类型: {emotion_type}")
    
    # 模拟处理延迟
    time.sleep(0.8)  # ESPnet稍快一些
    
    # 生成临时文件
    filename = f"espnet_mock_{int(time.time())}_{random.randint(1000, 9999)}.{output_format}"
    filepath = os.path.join("./temp", filename)
    
    # 保存模拟音频数据
    with open(filepath, "wb") as f:
        f.write(b"RIFF....WAVEfmt " + b"\x10\x00\x00\x00\x01\x00\x01\x00" + 
                (sample_rate).to_bytes(4, byteorder='little') + 
                (sample_rate * 2).to_bytes(4, byteorder='little') + 
                b"\x02\x00\x10\x00data" + 
                (len(sample_audio) * 2).to_bytes(4, byteorder='little'))
        
        # 添加一些模拟的音频数据
        sample_data = (sample_audio * 32767).astype(np.int16).tobytes()
        f.write(sample_data)
    
    # 返回结果
    return FileResponse(
        path=filepath,
        media_type=f"audio/{output_format}",
        filename=filename,
    )

@app.get("/api/voices")
async def get_voices():
    """获取可用音色列表"""
    return {
        "success": True,
        "voices": voices
    }

@app.get("/api/emotions")
async def get_emotions():
    """获取可用情感列表"""
    return {
        "success": True,
        "emotions": emotions
    }

@app.get("/api/config")
async def get_config():
    """获取配置信息"""
    return {
        "success": True,
        "config": {
            "sample_rate": 24000,
            "channels": 1,
            "bit_depth": 16,
            "supported_formats": ["wav", "mp3", "ogg"],
            "max_text_length": 800,  # 比MegaTTS3小一些
            "batch_size": 32,
        }
    }

if __name__ == "__main__":
    # 启动服务
    port = int(os.environ.get("PORT", 9932))
    host = os.environ.get("HOST", "0.0.0.0")
    
    logger.info(f"启动ESPnet模拟服务 {host}:{port}")
    uvicorn.run(app, host=host, port=port)