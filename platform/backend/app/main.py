"""
AI-Sound Platform Backend
FastAPI 主应用入口文件
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os
import logging
from datetime import datetime

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('../data/logs/app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 创建FastAPI应用
app = FastAPI(
    title="AI-Sound Platform API",
    description="基于MegaTTS3的语音克隆和多角色朗读平台",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS中间件配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],  # Vue前端地址
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 静态文件服务
app.mount("/audio", StaticFiles(directory="../data/audio"), name="audio")
app.mount("/uploads", StaticFiles(directory="../data/uploads"), name="uploads")

@app.on_event("startup")
async def startup_event():
    """应用启动时执行"""
    logger.info("🚀 AI-Sound Platform Backend 启动中...")
    
    # 创建必要的目录
    os.makedirs("../data/audio", exist_ok=True)
    os.makedirs("../data/uploads", exist_ok=True)
    os.makedirs("../data/voice_profiles", exist_ok=True)
    os.makedirs("../data/logs", exist_ok=True)
    os.makedirs("../data/projects", exist_ok=True)
    os.makedirs("../data/texts", exist_ok=True)
    os.makedirs("../data/config", exist_ok=True)
    os.makedirs("../data/backups", exist_ok=True)
    
    # 初始化数据库
    from .database import init_db
    init_db()
    
    logger.info("✅ AI-Sound Platform Backend 启动完成!")

@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭时执行"""
    logger.info("🛑 AI-Sound Platform Backend 正在关闭...")

@app.get("/")
async def root():
    """根路径 - API基本信息"""
    return {
        "name": "AI-Sound Platform API",
        "version": "1.0.0",
        "status": "running",
        "timestamp": datetime.now().isoformat(),
        "docs": "/docs",
        "health": "/health"
    }

@app.get("/health")
async def health_check():
    """健康检查接口"""
    try:
        # 检查MegaTTS3服务状态
        from .tts_client import MegaTTS3Client
        tts_client = MegaTTS3Client()
        megatts3_status = await tts_client.health_check()
        
        # 检查数据库连接
        from .database import get_db
        next(get_db())  # 测试数据库连接
        
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "version": "1.0.0",
            "services": {
                "database": "connected",
                "megatts3": megatts3_status.get("status", "unknown")
            }
        }
    except Exception as e:
        logger.error(f"健康检查失败: {str(e)}")
        raise HTTPException(status_code=503, detail=f"服务不健康: {str(e)}")

# 路由注册
from .voice_clone import router as voice_router
from .characters import router as characters_router
from .novel_reader import router as reader_router
from .monitor import router as monitor_router

app.include_router(voice_router)
app.include_router(characters_router)
app.include_router(reader_router)
app.include_router(monitor_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    ) 