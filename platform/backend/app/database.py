"""
数据库连接配置
管理SQLAlchemy连接、会话和依赖注入
"""

import os
from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from typing import Generator
import logging

from app.models.base import Base

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 数据库配置
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://ai_sound_user:ai_sound_password@localhost:5432/ai_sound")
ECHO_SQL = os.getenv("ECHO_SQL", "false").lower() == "true"

# 创建数据库引擎
if DATABASE_URL.startswith("sqlite"):
    # SQLite配置
    engine = create_engine(
        DATABASE_URL,
        echo=ECHO_SQL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
else:
    # PostgreSQL/MySQL配置
    engine = create_engine(
        DATABASE_URL,
        echo=ECHO_SQL,
        pool_pre_ping=True,
        pool_recycle=300,
        pool_size=10,
        max_overflow=20
    )

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def create_tables():
    """创建数据库表"""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("数据库表创建成功")
    except Exception as e:
        logger.error(f"创建数据库表失败: {e}")
        raise


def drop_tables():
    """删除所有数据库表"""
    try:
        Base.metadata.drop_all(bind=engine)
        logger.info("数据库表删除成功")
    except Exception as e:
        logger.error(f"删除数据库表失败: {e}")
        raise


def get_db() -> Generator[Session, None, None]:
    """
    数据库会话依赖注入
    用于FastAPI的依赖注入系统
    """
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error(f"数据库会话错误: {e}")
        db.rollback()
        raise
    finally:
        db.close()


class DatabaseManager:
    """数据库管理器"""
    
    def __init__(self):
        self.engine = engine
        self.SessionLocal = SessionLocal
    
    def get_session(self) -> Session:
        """获取数据库会话"""
        return self.SessionLocal()
    
    def init_db(self):
        """初始化数据库"""
        create_tables()
        logger.info("数据库初始化完成")
    
    def reset_db(self):
        """重置数据库"""
        drop_tables()
        create_tables()
        logger.info("数据库重置完成")
    
    def check_connection(self) -> bool:
        """检查数据库连接"""
        try:
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return True
        except Exception as e:
            logger.error(f"数据库连接检查失败: {e}")
            return False
    
    def get_db_info(self) -> dict:
        """获取数据库信息"""
        return {
            "url": DATABASE_URL,
            "driver": engine.dialect.name,
            "pool_size": engine.pool.size() if hasattr(engine.pool, 'size') else None,
            "checked_out": engine.pool.checkedout() if hasattr(engine.pool, 'checkedout') else None,
            "echo": ECHO_SQL
        }


# 全局数据库管理器实例
db_manager = DatabaseManager()


# SQLite优化配置
if DATABASE_URL.startswith("sqlite"):
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        """设置SQLite优化参数"""
        cursor = dbapi_connection.cursor()
        # 启用外键约束
        cursor.execute("PRAGMA foreign_keys=ON")
        # 设置WAL模式提高并发性能
        cursor.execute("PRAGMA journal_mode=WAL")
        # 设置同步模式
        cursor.execute("PRAGMA synchronous=NORMAL")
        # 设置缓存大小
        cursor.execute("PRAGMA cache_size=10000")
        # 设置临时存储
        cursor.execute("PRAGMA temp_store=memory")
        cursor.close()


# 数据库健康检查
def health_check() -> dict:
    """数据库健康检查"""
    try:
        is_connected = db_manager.check_connection()
        db_info = db_manager.get_db_info()
        
        return {
            "status": "healthy" if is_connected else "unhealthy",
            "connected": is_connected,
            "database_info": db_info
        }
    except Exception as e:
        logger.error(f"数据库健康检查失败: {e}")
        return {
            "status": "unhealthy",
            "connected": False,
            "error": str(e)
        }


# 数据库初始化
def init_database():
    """应用启动时初始化数据库"""
    try:
        logger.info("开始初始化数据库...")
        
        # 检查连接
        if not db_manager.check_connection():
            raise Exception("无法连接到数据库")
        
        # 创建表
        create_tables()
        
        logger.info("数据库初始化完成")
        
    except Exception as e:
        logger.error(f"数据库初始化失败: {e}")
        raise 