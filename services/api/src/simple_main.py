#!/usr/bin/env python3
"""
简化的API服务启动脚本
用于测试基本功能
"""

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 创建简单的FastAPI应用
app = FastAPI(
    title="AI-Sound TTS API (Simple)",
    version="2.0.0",
    description="简化版API用于测试"
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """根路径"""
    return {"message": "AI-Sound TTS API 简化版运行中"}

@app.get("/health")
async def health():
    """健康检查"""
    return {"status": "healthy", "version": "2.0.0"}

@app.get("/test")
async def test():
    """测试端点"""
    return {"test": "success", "message": "API服务正常运行"}

if __name__ == "__main__":
    uvicorn.run(
        "simple_main:app",
        host="0.0.0.0",
        port=9930,
        reload=False,
        log_level="info"
    )