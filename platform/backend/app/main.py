"""
AI-Sound Platform 后端主应用
FastAPI 应用程序入口点
"""

import os
import uvicorn
import logging
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager

from app.api import api_router
from app.database import create_tables, engine, get_db
from app.models import Base
from app.websocket.manager import websocket_manager
from app.config import settings

# 配置日志
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def ensure_database_schema():
    """确保数据库表结构正确"""
    import psycopg2
    from sqlalchemy import text
    
    try:
        # 检查text_segments表是否存在且结构正确
        with engine.connect() as conn:
            # 检查表是否存在
            result = conn.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'text_segments'
                );
            """))
            table_exists = result.fetchone()[0]
            
            if not table_exists:
                print("🔨 创建text_segments表...")
                conn.execute(text("""
                    CREATE TABLE text_segments (
                        id SERIAL PRIMARY KEY,
                        project_id INTEGER NOT NULL REFERENCES novel_projects(id) ON DELETE CASCADE,
                        text_content TEXT NOT NULL,
                        detected_speaker VARCHAR(100),
                        emotion VARCHAR(50),
                        voice_profile_id INTEGER REFERENCES voice_profiles(id),
                        chapter_number INTEGER,
                        segment_order INTEGER,
                        audio_file_path VARCHAR(500),
                        processing_time INTEGER,
                        completed_at TIMESTAMP,
                        error_message TEXT,
                        status VARCHAR(20) DEFAULT 'pending',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                """))
                conn.commit()
                print("✅ text_segments表创建成功")
            else:
                # 检查关键列是否存在
                result = conn.execute(text("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'text_segments' 
                    AND table_schema = 'public'
                    AND column_name IN ('text_content', 'detected_speaker', 'segment_order');
                """))
                existing_cols = [row[0] for row in result.fetchall()]
                
                required_cols = ['text_content', 'detected_speaker', 'segment_order']
                missing_cols = [col for col in required_cols if col not in existing_cols]
                
                if missing_cols:
                    print(f"🔧 添加缺失的列: {missing_cols}")
                    
                    for col in missing_cols:
                        if col == 'text_content':
                            conn.execute(text("ALTER TABLE text_segments ADD COLUMN text_content TEXT NOT NULL DEFAULT '';"))
                        elif col == 'detected_speaker':
                            conn.execute(text("ALTER TABLE text_segments ADD COLUMN detected_speaker VARCHAR(100);"))
                        elif col == 'segment_order':
                            conn.execute(text("ALTER TABLE text_segments ADD COLUMN segment_order INTEGER;"))
                    
                    conn.commit()
                    print("✅ 缺失列添加完成")
                else:
                    print("✅ text_segments表结构正确")
            
            # 创建必要的索引
            try:
                conn.execute(text("CREATE INDEX IF NOT EXISTS idx_text_segments_project_id ON text_segments(project_id);"))
                conn.execute(text("CREATE INDEX IF NOT EXISTS idx_text_segments_speaker ON text_segments(detected_speaker);"))
                conn.execute(text("CREATE INDEX IF NOT EXISTS idx_text_segments_order ON text_segments(segment_order);"))
                conn.commit()
                print("✅ 索引创建完成")
            except Exception as idx_error:
                print(f"⚠️ 索引创建警告: {idx_error}")
                
    except Exception as e:
        print(f"❌ 数据库结构检查失败: {str(e)}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时执行
    print("🚀 AI-Sound Platform 后端启动中...")
    
    # 创建数据库表
    create_tables()
    
    # 确保数据库结构正确
    await ensure_database_schema()
    
    # 启动WebSocket管理器
    await websocket_manager.start()
    
    print("✅ AI-Sound Platform 后端启动完成!")
    
    yield
    
    # 关闭时执行
    print("🛑 AI-Sound Platform 后端关闭中...")
    await websocket_manager.stop()
    print("👋 AI-Sound Platform 后端已关闭")

# 创建FastAPI应用
app = FastAPI(
    title="AI-Sound Platform API",
    description="智能音频合成平台API",
    version="1.0.0",
    lifespan=lifespan
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应该限制具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册API路由
app.include_router(api_router, prefix="/api")

# 全局异常处理
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """全局异常处理器"""
    logger.error(f"未处理异常: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"error": "internal_server_error", "message": "服务器内部错误"}
    )

# 健康检查端点
@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy", "service": "AI-Sound Platform"}

# 根路径
@app.get("/")
async def root():
    """根路径"""
    return {"message": "AI-Sound Platform API", "version": "1.0.0"}

# 运行脚本
if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    ) 