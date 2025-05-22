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

# 创建TTS引擎单例
tts_engine = None

# 定义一个懒加载的TTS引擎获取函数
def get_tts_engine():
    """获取TTS引擎单例"""
    try:
        global tts_engine
        if tts_engine is None:
            # 使用绝对导入
            from src.tts.engine import MegaTTSEngine
            config = get_config()
            logger.info("初始化TTS引擎...")
            logger.info(f"模型路径: {config['model_path']}")
            logger.info(f"使用GPU: {config['use_gpu']}")
            logger.info(f"使用FP16: {config['fp16']}")
            
            # 检查环境变量
            sample_wav_path = os.environ.get("SAMPLE_WAV_PATH")
            logger.info(f"样本WAV路径: {sample_wav_path}")
            
            # 设置环境变量
            if sample_wav_path:
                os.environ["SAMPLE_WAV_PATH"] = sample_wav_path
            
            # 初始化引擎
            tts_engine = MegaTTSEngine(
                model_path=config["model_path"],
                use_gpu=config["use_gpu"],
                fp16=config["fp16"],
                batch_size=config["batch_size"]
            )
            
            # 验证引擎
            if hasattr(tts_engine, 'synthesize'):
                logger.info("TTS引擎初始化成功，有synthesize方法")
            else:
                logger.error("TTS引擎初始化失败，无synthesize方法")
                
            logger.info("TTS引擎初始化完成")
        return tts_engine
    except Exception as e:
        logger.error(f"TTS引擎初始化失败: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return None

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