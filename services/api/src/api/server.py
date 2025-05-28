"""
MegaTTS API服务
提供HTTP接口用于文本转语音
"""

import os
import time
import uuid
import base64
import json
import logging
import tempfile
from typing import Dict, List, Any, Optional
from fastapi import FastAPI, HTTPException, BackgroundTasks, UploadFile, File, Form, Depends, Request
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# 全局启动时间记录
start_time = time.time()

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("api.server")

# 创建FastAPI应用
app = FastAPI(
    title="MegaTTS API",
    description="基于MegaTTS3的文本转语音API服务",
    version="1.0.0",
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有源，生产环境应限制
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 加载配置
def get_config() -> Dict[str, Any]:
    """获取API配置"""
    return {
        "model_path": os.environ.get("MODEL_PATH", "D:/AI-Sound/data/checkpoints/megatts3_base.pth"),
        "style_model_path": os.environ.get("STYLE_MODEL_PATH", "./checkpoints/style_transfer.pth"),
        "output_dir": os.environ.get("OUTPUT_DIR", "./output"),
        "use_gpu": os.environ.get("USE_GPU", "true").lower() == "true",
        "fp16": os.environ.get("FP16", "true").lower() == "true",
        "batch_size": int(os.environ.get("BATCH_SIZE", "64")),
        "processing": {
            "batch_size": int(os.environ.get("BATCH_SIZE", "64")),
            "num_workers": int(os.environ.get("NUM_WORKERS", "8")),
            "fp16": os.environ.get("FP16", "true").lower() == "true",
        },
        "voice_mapping": {
            "narrator": "female_mature",
            "character_default": "male_young",
            "characters": {
                "李明": "male_young",
                "张华": "male_middle",
                "王芳": "female_young"
            }
        },
        "use_redis": os.environ.get("USE_REDIS", "false").lower() == "true",
        "redis_url": os.environ.get("REDIS_URL", "redis://localhost:6379/0")
    }

# 导入TTS引擎路由器和适配器
from src.tts.engine import TTSEngineRouter, TTSEngineType
from src.tts.adapters import MegaTTS3Adapter, ESPnetAdapter
from src.tts.engine_selector import EngineSelector
from src.monitor.service_monitor import ServiceMonitor

# 创建TTS引擎路由器单例
tts_router = None
engine_selector = None
service_monitor = None

# 定义一个懒加载的TTS引擎路由器获取函数
def get_tts_router():
    """获取TTS引擎路由器单例"""
    try:
        global tts_router, engine_selector, service_monitor
        if tts_router is None:
            config = get_config()
            logger.info("初始化TTS引擎路由器...")
            
            # 创建引擎路由器
            tts_router = TTSEngineRouter()
            
            # 获取服务URL
            # 使用host.docker.internal访问宿主机上的服务
            megatts3_url = os.environ.get("MEGATTS3_URL", "http://host.docker.internal:9931")
            espnet_url = os.environ.get("ESPNET_URL", "http://host.docker.internal:9932")
            
            logger.info(f"MegaTTS3服务URL: {megatts3_url}")
            logger.info(f"ESPnet服务URL: {espnet_url}")
            
            # 注册引擎适配器
            try:
                megatts3_adapter = MegaTTS3Adapter(megatts3_url)
                tts_router.register_engine(TTSEngineType.MEGATTS3, megatts3_adapter)
                logger.info("MegaTTS3引擎注册成功")
            except Exception as e:
                logger.error(f"注册MegaTTS3引擎失败: {str(e)}")
                
            try:
                espnet_adapter = ESPnetAdapter(espnet_url)
                tts_router.register_engine(TTSEngineType.ESPNET, espnet_adapter)
                logger.info("ESPnet引擎注册成功")
            except Exception as e:
                logger.error(f"注册ESPnet引擎失败: {str(e)}")
            
            # 创建引擎选择器
            engine_selector = EngineSelector()
            
            # 创建服务监控器
            service_monitor = ServiceMonitor(tts_router, check_interval=30)
            
            # 启动监控（在应用启动时启动）
            logger.info("TTS引擎路由器初始化完成")
        return tts_router
    except Exception as e:
        logger.error(f"TTS引擎路由器初始化失败: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return None

# 为了兼容性保留的函数，返回MegaTTS3适配器
def get_tts_engine():
    """获取默认TTS引擎（向后兼容）"""
    router = get_tts_router()
    if router:
        return router.get_engine(TTSEngineType.MEGATTS3)
    return None

# 获取引擎选择器
def get_engine_selector():
    """获取引擎选择器"""
    if engine_selector is None:
        get_tts_router()  # 确保初始化
    return engine_selector

# 获取服务监控器
def get_service_monitor():
    """获取服务监控器"""
    if service_monitor is None:
        get_tts_router()  # 确保初始化
    return service_monitor

# 任务存储实现
task_store = {}

def get_task_store():
    """获取任务存储"""
    global task_store
    return task_store

# 定义启动服务的函数，这样可以避免循环导入问题
def setup_routes():
    """设置路由"""
    try:
        # 这里在函数内部导入routes，避免循环导入
        from .routes import router
        app.include_router(router)
        
        # 导入引擎路由
        try:
            import importlib
            from src.api.engine_routes import engine_router
            app.include_router(engine_router)
            logger.info("引擎API路由注册成功")
        except Exception as e:
            logger.error(f"引擎API路由注册失败: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            
        logger.info("API路由注册成功")
    except Exception as e:
        logger.error(f"API路由注册失败: {str(e)}")
        
        # 如果路由导入失败，添加一个简单的健康检查路由
        @app.get("/health")
        async def fallback_health_check():
            """应急健康检查"""
            return {
                "status": "warning",
                "message": "路由加载失败，但API服务正在运行",
                "uptime": time.time() - start_time
            }

# 调用路由设置函数
setup_routes()

# 添加全局异常处理
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"全局异常: {str(exc)}")
    return {"error": str(exc), "detail": "服务器内部错误"}

# 添加一个直接的测试路由
@app.get("/test")
async def test_route():
    """测试路由"""
    return {"message": "API服务正常运行", "time": time.time()}

# 添加TTS API路由
@app.post("/api/tts")
async def text_to_speech_direct(request: Request):
    """直接的文本转语音API"""
    try:
        # 获取请求数据
        data = await request.json()
        
        # 获取TTS引擎
        engine = get_tts_engine()
        
        # 提取参数
        text = data.get("text", "这是默认测试文本")
        voice_id = data.get("voice_id", "female_young")
        emotion_type = data.get("emotion_type", "neutral")
        emotion_intensity = data.get("emotion_intensity", 0.5)
        
        logger.info(f"合成请求: text={text}, voice_id={voice_id}")
        
        # 合成语音
        audio = engine.synthesize(
            text=text,
            voice_id=voice_id,
            emotion_type=emotion_type,
            emotion_intensity=emotion_intensity
        )
        
        # 保存到临时文件并返回
        audio_id = f"audio_{uuid.uuid4().hex[:8]}"
        output_dir = os.path.join(get_config()["output_dir"], "single")
        os.makedirs(output_dir, exist_ok=True)
        
        # 使用绝对导入
        from src.utils.audio import save_audio
        output_path = os.path.join(output_dir, f"{audio_id}.wav")
        save_audio(output_path, audio, format="wav")
        
        # 返回结果
        return FileResponse(output_path)
        
    except Exception as e:
        logger.error(f"语音合成失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"语音合成失败: {str(e)}"
        )

# 打印启动信息
logger.info("API服务已初始化完成，路由已注册")

# 在应用启动时初始化路由器和监控（异步）
@app.on_event("startup")
async def startup_event():
    # 初始化TTS路由器
    router = get_tts_router()
    if not router:
        logger.error("TTS引擎路由器初始化失败")
        return
    
    # 初始检查引擎健康状态
    logger.info("启动服务监控...")
    monitor = get_service_monitor()
    if monitor:
        await monitor.start_monitoring()
        logger.info("服务监控已启动")
    else:
        logger.error("服务监控初始化失败")

# 在应用关闭时停止监控
@app.on_event("shutdown")
async def shutdown_event():
    logger.info("停止服务监控...")
    monitor = get_service_monitor()
    if monitor:
        await monitor.stop_monitoring()
        logger.info("服务监控已停止")
    else:
        logger.warning("服务监控不存在，无需停止")