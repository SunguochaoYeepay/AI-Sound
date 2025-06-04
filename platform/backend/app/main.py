"""
AI-Sound Platform Backend
FastAPI 主应用入口文件
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, Response
from starlette.requests import Request
import os
import logging
from datetime import datetime
import mimetypes

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

# CORS中间件配置 - 更宽松的设置解决跨域问题
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000", 
        "http://localhost:3001",
        "http://localhost:5173",            # Vite默认端口
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001", 
        "http://127.0.0.1:5173",
        "http://soundapi.cpolar.top",       # 添加固定的API域名
        "https://soundapi.cpolar.top",      # HTTPS版本
        "https://4924bf6a.r35.cpolar.top",  # 添加外网域名
        "http://4924bf6a.r35.cpolar.top",   # HTTP版本
        "https://*.cpolar.top",             # 支持所有cpolar域名
        "http://*.cpolar.top",              # HTTP版本
        "*"                                 # 临时允许所有源，调试用
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=[
        "Accept",
        "Accept-Language", 
        "Content-Language",
        "Content-Type",
        "Authorization",
        "X-Requested-With",
        "Origin",
        "Access-Control-Request-Method",
        "Access-Control-Request-Headers"
    ],
)

# 确保音频文件类型正确
mimetypes.add_type('audio/wav', '.wav')
mimetypes.add_type('audio/mpeg', '.mp3')
mimetypes.add_type('audio/ogg', '.ogg')

class CORSStaticFiles(StaticFiles):
    """支持CORS的静态文件服务"""
    async def __call__(self, scope, receive, send):
        """处理请求并添加CORS头"""
        if scope["type"] == "http":
            # 对OPTIONS请求直接返回CORS头
            if scope["method"] == "OPTIONS":
                response = Response(
                    status_code=200,
                    headers={
                        "Access-Control-Allow-Origin": "*",
                        "Access-Control-Allow-Methods": "GET, HEAD, OPTIONS",
                        "Access-Control-Allow-Headers": "*",
                        "Access-Control-Max-Age": "86400",  # 24小时
                        "Content-Length": "0",
                    },
                )
                await response(scope, receive, send)
                return
                
        # 对其他请求调用父类方法
        response = await super().__call__(scope, receive, send)
        return response
        
    def file_response(self, *args, **kwargs) -> Response:
        """添加CORS头到文件响应"""
        response = super().file_response(*args, **kwargs)
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "GET, HEAD, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "*"
        response.headers["Cache-Control"] = "public, max-age=3600"  # 一小时缓存
        return response

# 静态文件服务 - 使用支持CORS的版本
app.mount("/audio", CORSStaticFiles(directory="../data/audio"), name="audio")
app.mount("/uploads", CORSStaticFiles(directory="../data/uploads"), name="uploads")
app.mount("/voice_profiles", CORSStaticFiles(directory="../data/voice_profiles"), name="voice_profiles")

@app.on_event("startup")
async def startup_event():
    """应用启动时执行"""
    logger.info("[STARTUP] AI-Sound Platform Backend 启动中...")
    
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
    from database import init_db
    init_db()
    
    logger.info("[SUCCESS] AI-Sound Platform Backend 启动完成!")

@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭时执行"""
    logger.info("[SHUTDOWN] AI-Sound Platform Backend 正在关闭...")

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

@app.options("/{full_path:path}")
async def options_handler(full_path: str):
    """处理所有OPTIONS预检请求"""
    return {
        "message": "CORS preflight successful"
    }

@app.get("/health")
async def health_check():
    """健康检查接口"""
    try:
        # 检查MegaTTS3服务状态
        from tts_client import MegaTTS3Client
        tts_client = MegaTTS3Client()
        megatts3_status = await tts_client.health_check()
        
        # 检查数据库连接
        from database import get_db
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
from voice_clone import router as voice_router
from characters import router as characters_router
from novel_reader import router as reader_router
from monitor import router as monitor_router

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