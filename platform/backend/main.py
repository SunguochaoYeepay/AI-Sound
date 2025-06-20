"""
AI-Sound Platform Backend
FastAPI主应用入口
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Dict, Any
import aiohttp
import os

from fastapi import FastAPI, Request, HTTPException, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
import uvicorn
import mimetypes

# 应用组件导入
from app.database import init_database, health_check as db_health_check
from app.api import api_router
from app.tts_client import get_tts_client
from app.clients.audio_processor import audio_processor
from app.clients.file_manager import file_manager
from app.websocket.manager import websocket_manager
from app.exceptions import (
    AIServiceException,
    TTSServiceException,
    FileProcessingException,
    ValidationException
)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# TangoFlux服务配置
TANGOFLUX_SERVICE_URL = os.getenv("TANGOFLUX_URL", "http://localhost:7930")

async def check_tangoflux_connection() -> Dict[str, Any]:
    """检查TangoFlux核心引擎连接状态"""
    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
            async with session.get(f"{TANGOFLUX_SERVICE_URL}/health") as response:
                if response.status == 200:
                    result = await response.json()
                    return {
                        "status": "healthy",
                        "url": TANGOFLUX_SERVICE_URL,
                        "data": result
                    }
                else:
                    return {
                        "status": "unhealthy",
                        "url": TANGOFLUX_SERVICE_URL,
                        "error": f"HTTP {response.status}"
                    }
    except Exception as e:
        return {
            "status": "error",
            "url": TANGOFLUX_SERVICE_URL,
            "error": str(e)
        }

# 确保必要的目录在应用创建前就存在
os.makedirs("data/audio", exist_ok=True)
os.makedirs("data/uploads", exist_ok=True)
os.makedirs("data/voice_profiles", exist_ok=True)
os.makedirs("data/logs", exist_ok=True)
os.makedirs("data/projects", exist_ok=True)
os.makedirs("data/texts", exist_ok=True)
os.makedirs("data/config", exist_ok=True)
os.makedirs("data/backups", exist_ok=True)
os.makedirs("data/environment_sounds", exist_ok=True)

# 配置音频文件类型
mimetypes.add_type('audio/wav', '.wav')
mimetypes.add_type('audio/mpeg', '.mp3')
mimetypes.add_type('audio/ogg', '.ogg')


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时执行
    logger.info("🚀 AI-Sound平台后端启动中...")
    
    try:
        # 初始化数据库
        logger.info("📊 初始化数据库...")
        init_database()
        
        # 检查TangoFlux核心引擎 - 关键检查！
        logger.info("🎼 检查TangoFlux环境音核心引擎...")
        tangoflux_status = await check_tangoflux_connection()
        
        if tangoflux_status["status"] == "healthy":
            logger.info(f"✅ TangoFlux核心引擎连接成功: {tangoflux_status['url']}")
        else:
            error_msg = f"❌ TangoFlux核心引擎连接失败: {tangoflux_status['url']} - {tangoflux_status.get('error', 'Unknown error')}"
            logger.error(error_msg)
            logger.error("💥 环境音生成功能不可用，请检查TangoFlux服务状态！")
            
            # 严格模式：如果核心引擎不可用，启动失败
            strict_mode = os.getenv("STRICT_ENGINE_CHECK", "true").lower() == "true"
            if strict_mode:
                logger.error("🚫 严格模式：核心引擎不可用，启动终止！")
                raise Exception(f"TangoFlux核心引擎不可用: {tangoflux_status.get('error')}")
            else:
                logger.warning("⚠️ 宽松模式：继续启动但环境音功能不可用")
        
        # 初始化TTS客户端
        logger.info("🎵 初始化TTS客户端...")
        # 使用旧版TTS客户端，无需特殊初始化
        
        # 初始化WebSocket管理器
        logger.info("🔌 初始化WebSocket管理器...")
        await websocket_manager.start()
        
        logger.info("✅ AI-Sound平台后端启动完成!")
        
    except Exception as e:
        logger.error(f"❌ 启动失败: {e}")
        raise
    
    yield
    
    # 关闭时执行
    logger.info("🛑 AI-Sound平台后端关闭中...")
    
    try:
        # 旧版TTS客户端无需特殊关闭逻辑
        
        # 关闭音频处理器
        await audio_processor.close()
        
        # 关闭WebSocket管理器
        await websocket_manager.stop()
        
        logger.info("✅ AI-Sound平台后端已安全关闭")
        
    except Exception as e:
        logger.error(f"❌ 关闭时出错: {e}")


# 创建FastAPI应用
app = FastAPI(
    title="AI-Sound Platform API",
    description="智能语音合成平台后端API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# 添加中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应该限制具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(GZipMiddleware, minimum_size=1000)

# 挂载静态文件目录
app.mount("/audio", StaticFiles(directory="data/audio"), name="audio")
app.mount("/uploads", StaticFiles(directory="data/uploads"), name="uploads")
app.mount("/voice_profiles", StaticFiles(directory="data/voice_profiles"), name="voice_profiles")
app.mount("/environment_sounds", StaticFiles(directory="data/environment_sounds"), name="environment_sounds")

# 注册API路由
app.include_router(api_router, prefix="/api")


# WebSocket端点
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket实时通信端点"""
    import uuid
    from fastapi import WebSocketDisconnect
    
    connection_id = str(uuid.uuid4())
    logger.info(f"🔌 新的WebSocket连接请求: {connection_id}")
    
    try:
        # 建立连接
        await websocket_manager.connect(websocket, connection_id)
        logger.info(f"✅ WebSocket连接建立成功: {connection_id}")
        
        # 保持连接并处理消息
        while True:
            # 接收消息
            data = await websocket.receive_text()
            logger.info(f"📨 收到WebSocket消息: {connection_id} -> {data}")
            
            # 处理消息
            await websocket_manager.handle_message(connection_id, data)
            
    except WebSocketDisconnect:
        # 正常断开连接
        logger.info(f"🔌 WebSocket正常断开: {connection_id}")
        await websocket_manager.disconnect(connection_id)
    except Exception as e:
        logger.error(f"❌ WebSocket连接异常: {connection_id} -> {e}")
        await websocket_manager.disconnect(connection_id)


# 异常处理器
@app.exception_handler(AIServiceException)
async def ai_service_exception_handler(request: Request, exc: AIServiceException):
    """AI服务异常处理"""
    logger.error(f"AI服务异常: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": "ai_service_error",
            "message": exc.detail,
            "details": exc.details
        }
    )


@app.exception_handler(TTSServiceException)
async def tts_service_exception_handler(request: Request, exc: TTSServiceException):
    """TTS服务异常处理"""
    logger.error(f"TTS服务异常: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": "tts_service_error", 
            "message": exc.detail,
            "details": exc.details
        }
    )


@app.exception_handler(FileProcessingException)
async def file_processing_exception_handler(request: Request, exc: FileProcessingException):
    """文件处理异常处理"""
    logger.error(f"文件处理异常: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": "file_processing_error",
            "message": exc.detail,
            "details": exc.details
        }
    )


@app.exception_handler(ValidationException)
async def validation_exception_handler(request: Request, exc: ValidationException):
    """验证异常处理"""
    logger.error(f"验证异常: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": "validation_error",
            "message": exc.detail,
            "details": exc.details
        }
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """HTTP异常处理"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": "http_error",
            "message": exc.detail
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """通用异常处理"""
    logger.error(f"未处理的异常: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "internal_server_error",
            "message": "服务器内部错误"
        }
    )


# 健康检查端点
@app.get("/health")
async def health_check() -> Dict[str, Any]:
    """系统健康检查"""
    try:
        # 数据库健康检查
        db_status = db_health_check()
        
        # TTS客户端健康检查
        tts_client = get_tts_client()
        tts_status = await tts_client.health_check()
        
        # TangoFlux核心引擎健康检查
        tangoflux_status = await check_tangoflux_connection()
        
        # WebSocket管理器状态
        ws_status = websocket_manager.get_status()
        
        # 文件管理器状态
        storage_stats = file_manager.get_storage_stats()
        
        all_healthy = (
            db_status.get("status") == "healthy" and
            tts_status.get("status") == "healthy" and
            tangoflux_status.get("status") == "healthy" and
            ws_status.get("status") == "running"
        )
        
        return {
            "status": "healthy" if all_healthy else "degraded",
            "timestamp": asyncio.get_event_loop().time(),
            "services": {
                "database": db_status,
                "tts_client": tts_status,
                "tangoflux_engine": tangoflux_status,
                "websocket_manager": ws_status,
                "storage": storage_stats
            }
        }
        
    except Exception as e:
        logger.error(f"健康检查失败: {e}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }


# API健康检查端点
@app.get("/api/health")
async def api_health_check() -> Dict[str, Any]:
    """前API健康检查"""
    return await health_check()


# 根端点
@app.get("/")
async def root():
    """根端点"""
    return {
        "name": "AI-Sound Platform API",
        "version": "1.0.0",
        "description": "智能语音合成平台后端API",
        "docs_url": "/docs",
        "health_url": "/health"
    }


if __name__ == "__main__":
    # 开发环境运行配置
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    ) 