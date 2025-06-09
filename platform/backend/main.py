"""
AI-Sound Platform Backend
FastAPI主应用入口
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Dict, Any

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
import uvicorn

# 应用组件导入
from app.database import init_database, health_check as db_health_check
from app.api import api_router
from app.clients.tts_client import init_tts_client, tts_client
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


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时执行
    logger.info("🚀 AI-Sound平台后端启动中...")
    
    try:
        # 初始化数据库
        logger.info("📊 初始化数据库...")
        init_database()
        
        # 初始化TTS客户端
        logger.info("🎵 初始化TTS客户端...")
        await init_tts_client()
        
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
        # 关闭TTS客户端
        await tts_client.close()
        
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

# 注册API路由
app.include_router(api_router, prefix="/api")


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
        tts_status = await tts_client.health_check()
        
        # WebSocket管理器状态
        ws_status = websocket_manager.get_status()
        
        # 文件管理器状态
        storage_stats = file_manager.get_storage_stats()
        
        all_healthy = (
            db_status.get("status") == "healthy" and
            all(tts_status.values()) and
            ws_status.get("status") == "running"
        )
        
        return {
            "status": "healthy" if all_healthy else "degraded",
            "timestamp": asyncio.get_event_loop().time(),
            "services": {
                "database": db_status,
                "tts_client": tts_status,
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