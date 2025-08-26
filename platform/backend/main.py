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

# 修复FFmpeg路径配置
ffmpeg_path = os.path.expanduser("~/AppData/Local/Microsoft/WinGet/Packages/Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe/ffmpeg-7.1.1-full_build/bin")
os.environ["PATH"] = ffmpeg_path + os.pathsep + os.environ.get("PATH", "")

# 设置pydub的FFmpeg路径
try:
    from pydub import AudioSegment
    AudioSegment.converter = os.path.join(ffmpeg_path, "ffmpeg.exe")
    AudioSegment.ffmpeg = os.path.join(ffmpeg_path, "ffmpeg.exe")
    AudioSegment.ffprobe = os.path.join(ffmpeg_path, "ffprobe.exe")
    print(f"✅ AI-Sound后端FFmpeg路径已设置: {ffmpeg_path}")
except ImportError:
    print("⚠️ pydub未安装，跳过FFmpeg配置")
except Exception as e:
    print(f"⚠️ FFmpeg配置失败: {e}")

# 加载环境变量
try:
    from dotenv import load_dotenv
    load_dotenv()  # 加载.env文件中的环境变量
except ImportError:
    pass  # 如果没有安装python-dotenv，忽略错误

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
from app.utils.logger import log_system_event, LogModule
from app.middleware.logging_middleware import LoggingMiddleware
from app.config.log_config import log_config
from app.exceptions import (
    AIServiceException,
    TTSServiceException,
    FileProcessingException,
    ValidationException
)

# 移除本地化SongGeneration服务，改用HTTP引擎客户端

# 初始化完整的日志系统
from app.config.logging_config import init_logging

# 从环境变量读取日志级别，默认为INFO
log_level = os.getenv("LOG_LEVEL", "INFO").upper()
init_logging(level=log_level)
logger = logging.getLogger(__name__)

# 如果是开发模式，显示额外提示
if os.getenv("LOCAL_DEV", "false").lower() == "true":
    logger.info("🔧 本地开发模式已启用 - 控制台将显示详细日志")

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

async def check_songgeneration_service():
    """检查SongGeneration HTTP引擎服务状态"""
    try:
        # 使用新的HTTP引擎客户端检查
        from app.clients.songgeneration_engine import get_songgeneration_engine
        
        engine = get_songgeneration_engine()
        is_healthy = await engine.health_check()
        
        if is_healthy:
            logger.info(f"✅ SongGeneration HTTP引擎服务正常: {engine.base_url}")
        else:
            logger.warning(f"⚠️ SongGeneration HTTP引擎服务不可用: {engine.base_url}")
            logger.warning("🎵 音乐生成功能将不可用")
                
    except Exception as e:
        logger.error(f"❌ SongGeneration引擎检查异常: {str(e)}")
        logger.warning("⚠️ 音乐生成功能将不可用")


async def check_ollama_service():
    """检查Ollama LLM服务状态"""
    try:
        # 导入LLM分析器
        from app.services.llm_scene_analyzer import llm_scene_analyzer
        
        # 检查Ollama服务状态
        ollama_url = llm_scene_analyzer.ollama_base_url
        model_name = llm_scene_analyzer.model_name
        
        logger.info(f"🔍 检查Ollama服务: {ollama_url}")
        logger.info(f"🔍 目标模型: {model_name}")
        
        # 检查服务可用性
        is_service_available = await llm_scene_analyzer.check_ollama_status()
        
        if is_service_available:
            # 检查特定模型
            is_model_available = await llm_scene_analyzer.check_model_available(model_name)
            
            if is_model_available:
                logger.info(f"✅ Ollama LLM服务正常: {ollama_url}")
                logger.info(f"✅ 模型可用: {model_name}")
            else:
                logger.warning(f"⚠️ Ollama服务可用但模型不存在: {model_name}")
                logger.warning(f"💡 请运行: ollama pull {model_name}")
        else:
            logger.error(f"❌ Ollama LLM服务不可用: {ollama_url}")
            logger.error("💥 环境音智能分析功能不可用，请检查Ollama服务状态！")
            logger.error("💡 启动方法: ollama serve")
            
    except Exception as e:
        logger.error(f"❌ Ollama服务检查失败: {str(e)}")

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
        logger.info("✅ 数据库初始化完成")
        
        # 检查TangoFlux核心引擎
        logger.info("🎼 检查TangoFlux环境音核心引擎...")
        tangoflux_status = await check_tangoflux_connection()
        
        if tangoflux_status["status"] == "healthy":
            logger.info(f"✅ TangoFlux核心引擎连接成功: {tangoflux_status['url']}")
        else:
            error_msg = f"❌ TangoFlux核心引擎连接失败: {tangoflux_status['url']} - {tangoflux_status.get('error', 'Unknown error')}"
            logger.error(error_msg)
            logger.error("💥 环境音生成功能不可用，请检查TangoFlux服务状态！")
            
            # 修改为宽松模式：即使核心引擎不可用也继续启动
            strict_mode = os.getenv("STRICT_ENGINE_CHECK", "false").lower() == "true"
            if strict_mode:
                logger.error("🚫 严格模式：核心引擎不可用，启动终止！")
                raise Exception(f"TangoFlux核心引擎不可用: {tangoflux_status.get('error')}")
            else:
                logger.warning("⚠️ 宽松模式：继续启动但环境音功能不可用")
        
        # 检查SongGeneration背景音乐服务
        logger.info("🎵 检查SongGeneration背景音乐服务...")
        await check_songgeneration_service()
        
        # 检查Ollama LLM服务状态
        logger.info("🤖 检查Ollama LLM服务...")
        await check_ollama_service()
        
        # 初始化WebSocket管理器
        logger.info("🔌 初始化WebSocket管理器...")
        await websocket_manager.start()
        logger.info("✅ WebSocket管理器启动完成")
        
        logger.info("✅ AI-Sound平台后端启动完成!")
        
    except Exception as e:
        logger.error(f"❌ 启动失败: {e}")
        raise
    
    yield
    
    # 关闭时执行
    logger.info("🛑 AI-Sound平台后端关闭中...")
    
    try:
        # 关闭音频处理器
        await audio_processor.close()
        logger.info("✅ 音频处理器已关闭")
        
        # 关闭WebSocket管理器
        await websocket_manager.stop()
        logger.info("✅ WebSocket管理器已关闭")
        
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

# 添加API日志记录中间件
if log_config.API_LOG_ENABLED:
    app.add_middleware(
        LoggingMiddleware, 
        skip_paths=log_config.API_LOG_SKIP_PATHS
    )

# 挂载静态文件目录 - 匹配API路径规范
app.mount("/api/v1/audio", StaticFiles(directory="data/audio"), name="audio")
app.mount("/api/v1/uploads", StaticFiles(directory="data/uploads"), name="uploads")
app.mount("/api/v1/voice_profiles", StaticFiles(directory="data/voice_profiles"), name="voice_profiles")
app.mount("/api/v1/avatars", StaticFiles(directory="data/avatars"), name="avatars")
app.mount("/api/v1/environment_sounds", StaticFiles(directory="data/environment_sounds"), name="environment_sounds")
app.mount("/api/v1/outputs", StaticFiles(directory="data/outputs"), name="outputs")

# 注册API路由
app.include_router(api_router, prefix="/api")


# WebSocket端点
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket实时通信端点"""
    import uuid
    from fastapi import WebSocketDisconnect
    
    connection_id = str(uuid.uuid4())
    logger.debug(f"🔌 新的WebSocket连接请求: {connection_id}")
    
    try:
        # 建立连接
        await websocket_manager.connect(websocket, connection_id)
        logger.debug(f"✅ WebSocket连接建立成功: {connection_id}")
        
        # 保持连接并处理消息
        while True:
            # 接收消息
            data = await websocket.receive_text()
            logger.debug(f"📨 收到WebSocket消息: {connection_id} -> {data}")
            
            # 处理消息
            await websocket_manager.handle_message(connection_id, data)
            
    except WebSocketDisconnect:
        # 正常断开连接
        logger.debug(f"🔌 WebSocket正常断开: {connection_id}")
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
        # 暂时返回基本状态
        return {
            "status": "healthy",
            "timestamp": asyncio.get_event_loop().time(),
            "services": {
                "status": "ok"
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
    # 开发环境运行配置 - 使用8001端口避免与Docker服务冲突
    import os
    dev_port = int(os.getenv("DEV_PORT", "8001"))  # 本地开发默认8001端口
    
    print(f"🚀 启动本地开发服务器: http://localhost:{dev_port}")
    print(f"📖 API文档: http://localhost:{dev_port}/docs")
    print(f"🔍 健康检查: http://localhost:{dev_port}/health")
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=dev_port,
        workers=1,      # 🔥 Windows兼容性：使用单进程模式
        reload=False,   # 🔥 稳定性考虑禁用reload
        log_level="info"
    )