"""
PostgreSQL数据库连接和会话管理
"""

from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
import os
import logging

logger = logging.getLogger(__name__)

# 数据库配置 - 统一使用PostgreSQL
DATABASE_URL = os.getenv('DATABASE_URL')

if not DATABASE_URL:
    # 默认使用Docker容器中的PostgreSQL
    DATABASE_URL = "postgresql://ai_sound_user:ai_sound_password@localhost:5432/ai_sound"
    logger.info("[CONFIG] 使用默认PostgreSQL配置 (Docker容器)")

logger.info(f"[CONFIG] 使用PostgreSQL数据库: {DATABASE_URL.split('@')[1] if '@' in DATABASE_URL else 'PostgreSQL'}")
IS_POSTGRES = True

# 创建PostgreSQL数据库引擎
engine = create_engine(
    DATABASE_URL,
    echo=False,  # 设为True可以看到SQL日志
    pool_pre_ping=True,  # 连接池预检查
    pool_size=10,
    max_overflow=20
)

# PostgreSQL连接事件处理（如需要可添加）

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 声明式基类
Base = declarative_base()

def get_db() -> Session:
    """
    获取数据库会话
    用于依赖注入
    """
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error(f"数据库会话错误: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()

def init_db():
    """
    初始化PostgreSQL数据库
    创建所有表结构
    """
    try:
        # 导入所有模型以确保表被创建
        import models
        
        # 创建所有表
        Base.metadata.create_all(bind=engine)
        
        logger.info("[SUCCESS] PostgreSQL数据库初始化完成")
        
        # 检查PostgreSQL连接
        with SessionLocal() as db:
            result = db.execute(text("SELECT version()"))
            version = result.fetchone()[0]
            logger.info(f"[INFO] PostgreSQL版本: {version.split()[0]} {version.split()[1]}")
            
    except Exception as e:
        logger.error(f"[ERROR] 数据库初始化失败: {str(e)}")
        raise

def get_db_info():
    """
    获取PostgreSQL数据库信息
    """
    try:
        with SessionLocal() as db:
            # PostgreSQL查询
            tables_info = db.execute(text("""
                SELECT table_name, table_type FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name
            """)).fetchall()
            
            # PostgreSQL数据库大小查询
            db_size_result = db.execute(text("""
                SELECT pg_size_pretty(pg_database_size(current_database()))
            """)).fetchone()
            
            return {
                "database_type": "PostgreSQL",
                "database_url": DATABASE_URL.split('@')[1] if '@' in DATABASE_URL else DATABASE_URL,
                "database_size": db_size_result[0] if db_size_result else "Unknown",
                "tables_count": len(tables_info),
                "tables": [{"name": table[0], "type": table[1]} for table in tables_info]
            }
    except Exception as e:
        logger.error(f"获取数据库信息失败: {str(e)}")
        return {"error": str(e)}

# PostgreSQL数据库备份和管理功能可通过Docker卷管理
# 生产环境建议使用pg_dump等专业工具 