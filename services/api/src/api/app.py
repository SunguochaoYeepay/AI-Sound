"""
FastAPI应用创建和配置
集成任务队列和WebSocket功能
"""

import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
import logging

from ..core.config import settings
from ..core.logging import setup_logging
from ..core.dependencies import dependency_manager
from ..core.queue import task_queue
from ..core.websocket import websocket_manager, MessageType

# 导入路由
from .routes import engines, voices, characters, tts

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时初始化
    logger.info("正在启动AI-Sound TTS系统...")
    
    try:
        # 初始化依赖服务
        await dependency_manager.initialize()
        
        # 启动任务队列
        await task_queue.start()
        
        logger.info("AI-Sound TTS系统启动完成")
        
        yield
        
    finally:
        # 关闭时清理
        logger.info("正在关闭AI-Sound TTS系统...")
        
        # 停止任务队列
        await task_queue.stop()
        
        # 清理依赖服务
        await dependency_manager.cleanup()
        
        logger.info("AI-Sound TTS系统已关闭")


def create_app() -> FastAPI:
    """创建FastAPI应用"""
    
    # 初始化日志
    setup_logging()
    
    # 创建应用实例
    app = FastAPI(
        title=settings.app_name,
        version=settings.version,
        description="AI-Sound TTS系统 - 集成多种TTS引擎的语音合成平台",
        docs_url="/docs" if settings.debug else None,
        redoc_url="/redoc" if settings.debug else None,
        lifespan=lifespan
    )
    
    # 添加中间件
    setup_middleware(app)
    
    # 注册路由
    register_routes(app)
    
    # 注册WebSocket路由
    register_websocket_routes(app)
    
    # 注册异常处理器
    register_exception_handlers(app)
    
    # 挂载静态文件
    setup_static_files(app)
    
    return app


def setup_middleware(app: FastAPI) -> None:
    """设置中间件"""
    
    # CORS中间件
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.api.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Gzip压缩中间件
    app.add_middleware(GZipMiddleware, minimum_size=1000)
    
    # 请求日志中间件
    @app.middleware("http")
    async def log_requests(request, call_next):
        start_time = asyncio.get_event_loop().time()
        
        response = await call_next(request)
        
        process_time = asyncio.get_event_loop().time() - start_time
        logger.info(
            f"{request.method} {request.url.path} - "
            f"{response.status_code} - {process_time:.3f}s"
        )
        
        return response


def register_routes(app: FastAPI) -> None:
    """注册API路由"""
    
    # 健康检查
    @app.get("/health")
    async def health_check():
        """健康检查端点"""
        try:
            # 检查数据库连接
            db_status = dependency_manager._initialized
            
            # 检查任务队列状态
            queue_status = await task_queue.get_queue_status()
            
            # 检查WebSocket状态
            ws_stats = websocket_manager.get_stats()
            
            return {
                "status": "healthy",
                "timestamp": asyncio.get_event_loop().time(),
                "services": {
                    "database": "healthy" if db_status else "error",
                    "task_queue": "healthy" if queue_status["running"] else "error",
                    "websocket": "healthy",
                },
                "stats": {
                    "queue": queue_status,
                    "websocket": ws_stats
                }
            }
        except Exception as e:
            logger.error(f"健康检查失败: {e}")
            return JSONResponse(
                status_code=503,
                content={
                    "status": "unhealthy",
                    "error": str(e)
                }
            )
    
    # 系统信息
    @app.get("/info")
    async def system_info():
        """系统信息端点"""
        return {
            "name": settings.app_name,
            "version": settings.version,
            "debug": settings.debug,
            "features": [
                "multi_engine_tts",
                "voice_management", 
                "character_mapping",
                "batch_synthesis",
                "real_time_monitoring"
            ]
        }
    
    # 注册业务路由
    app.include_router(engines.router)
    app.include_router(voices.router)
    app.include_router(characters.router)
    app.include_router(tts.router)


def register_websocket_routes(app: FastAPI) -> None:
    """注册WebSocket路由"""
    
    @app.websocket("/ws/{client_id}")
    async def websocket_endpoint(websocket: WebSocket, client_id: str):
        """WebSocket连接端点"""
        try:
            await websocket_manager.connect(websocket, client_id)
            
            while True:
                try:
                    # 接收客户端消息
                    data = await websocket.receive_json()
                    await handle_websocket_message(client_id, data)
                    
                except WebSocketDisconnect:
                    break
                except Exception as e:
                    logger.error(f"WebSocket消息处理错误 {client_id}: {e}")
                    await websocket_manager.send_to_client(client_id, {
                        "type": "error",
                        "message": str(e)
                    })
                    
        except Exception as e:
            logger.error(f"WebSocket连接错误 {client_id}: {e}")
        finally:
            await websocket_manager.disconnect(client_id)
    
    async def handle_websocket_message(client_id: str, data: dict) -> None:
        """处理WebSocket消息"""
        message_type = data.get("type")
        
        if message_type == "subscribe":
            # 订阅消息类型
            message_types = [MessageType(t) for t in data.get("message_types", [])]
            await websocket_manager.subscribe(client_id, message_types)
            
        elif message_type == "unsubscribe":
            # 取消订阅
            message_types = [MessageType(t) for t in data.get("message_types", [])]
            await websocket_manager.unsubscribe(client_id, message_types)
            
        elif message_type == "join_room":
            # 加入房间
            room = data.get("room")
            if room:
                await websocket_manager.join_room(client_id, room)
                
        elif message_type == "leave_room":
            # 离开房间
            room = data.get("room")
            if room:
                await websocket_manager.leave_room(client_id, room)
                
        elif message_type == "ping":
            # 心跳检测
            await websocket_manager.send_to_client(client_id, {
                "type": "pong",
                "timestamp": asyncio.get_event_loop().time()
            })


def register_exception_handlers(app: FastAPI) -> None:
    """注册异常处理器"""
    
    @app.exception_handler(ValueError)
    async def value_error_handler(request, exc):
        """参数错误处理"""
        logger.warning(f"参数错误: {exc}")
        return JSONResponse(
            status_code=400,
            content={"error": "参数错误", "detail": str(exc)}
        )
    
    @app.exception_handler(FileNotFoundError)
    async def file_not_found_handler(request, exc):
        """文件未找到处理"""
        logger.warning(f"文件未找到: {exc}")
        return JSONResponse(
            status_code=404,
            content={"error": "文件未找到", "detail": str(exc)}
        )
    
    @app.exception_handler(ConnectionError)
    async def connection_error_handler(request, exc):
        """连接错误处理"""
        logger.error(f"连接错误: {exc}")
        return JSONResponse(
            status_code=503,
            content={"error": "服务不可用", "detail": str(exc)}
        )
    
    @app.exception_handler(Exception)
    async def general_exception_handler(request, exc):
        """通用异常处理"""
        logger.error(f"未处理的异常: {exc}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"error": "内部服务器错误", "detail": "请联系管理员"}
        )


def setup_static_files(app: FastAPI) -> None:
    """设置静态文件服务"""
    try:
        # 音频文件服务
        audio_path = settings.tts.output_path
        if not audio_path.exists():
            audio_path.mkdir(parents=True, exist_ok=True)
        
        app.mount("/audio", StaticFiles(directory=str(audio_path)), name="audio")
        
        # 模型文件服务（仅在调试模式下）
        if settings.debug:
            model_path = settings.tts.model_path
            if model_path.exists():
                app.mount("/models", StaticFiles(directory=str(model_path)), name="models")
        
        logger.info("静态文件服务已配置")
        
    except Exception as e:
        logger.warning(f"配置静态文件服务失败: {e}")


# 创建应用实例
app = create_app()