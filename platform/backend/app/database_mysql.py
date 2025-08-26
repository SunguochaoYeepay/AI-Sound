"""
MySQL数据库连接配置
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

# MySQL数据库配置
MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
MYSQL_PORT = os.getenv("MYSQL_PORT", "3306")
MYSQL_USER = os.getenv("MYSQL_USER", "ai_sound_user")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "ai_sound_password")
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "ai_sound")
MYSQL_CHARSET = os.getenv("MYSQL_CHARSET", "utf8mb4")

# 构建MySQL连接URL
DATABASE_URL = f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}?charset={MYSQL_CHARSET}"

ECHO_SQL = os.getenv("ECHO_SQL", "false").lower() == "true"

# 创建MySQL数据库引擎
engine = create_engine(
    DATABASE_URL,
    echo=ECHO_SQL,
    pool_pre_ping=True,
    pool_recycle=3600,  # MySQL连接超时时间
    pool_size=10,
    max_overflow=20,
    # MySQL特定配置
    connect_args={
        "charset": MYSQL_CHARSET,
        "autocommit": False,
        "sql_mode": "STRICT_TRANS_TABLES,NO_ZERO_DATE,NO_ZERO_IN_DATE,ERROR_FOR_DIVISION_BY_ZERO"
    }
)

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def create_tables():
    """创建数据库表"""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("MySQL数据库表创建成功")
    except Exception as e:
        logger.error(f"创建MySQL数据库表失败: {e}")
        raise


def drop_tables():
    """删除所有数据库表"""
    try:
        Base.metadata.drop_all(bind=engine)
        logger.info("MySQL数据库表删除成功")
    except Exception as e:
        logger.error(f"删除MySQL数据库表失败: {e}")
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
        logger.error(f"MySQL数据库会话错误: {e}")
        db.rollback()
        raise
    finally:
        db.close()


class MySQLDatabaseManager:
    """MySQL数据库管理器"""
    
    def __init__(self):
        self.engine = engine
        self.SessionLocal = SessionLocal
    
    def get_session(self) -> Session:
        """获取数据库会话"""
        return self.SessionLocal()
    
    def init_db(self):
        """初始化数据库"""
        create_tables()
        logger.info("MySQL数据库初始化完成")
    
    def reset_db(self):
        """重置数据库"""
        drop_tables()
        create_tables()
        logger.info("MySQL数据库重置完成")
    
    def check_connection(self) -> bool:
        """检查数据库连接"""
        try:
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return True
        except Exception as e:
            logger.error(f"MySQL数据库连接检查失败: {e}")
            return False
    
    def get_db_info(self) -> dict:
        """获取数据库信息"""
        return {
            "url": DATABASE_URL,
            "driver": "mysql+pymysql",
            "host": MYSQL_HOST,
            "port": MYSQL_PORT,
            "database": MYSQL_DATABASE,
            "charset": MYSQL_CHARSET,
            "pool_size": engine.pool.size() if hasattr(engine.pool, 'size') else None,
            "checked_out": engine.pool.checkedout() if hasattr(engine.pool, 'checkedout') else None,
            "echo": ECHO_SQL
        }
    
    def create_database_if_not_exists(self):
        """如果数据库不存在则创建"""
        try:
            # 创建不指定数据库的连接
            temp_url = f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}"
            temp_engine = create_engine(temp_url)
            
            with temp_engine.connect() as conn:
                # 创建数据库（如果不存在）
                conn.execute(text(f"CREATE DATABASE IF NOT EXISTS {MYSQL_DATABASE} CHARACTER SET {MYSQL_CHARSET} COLLATE {MYSQL_CHARSET}_unicode_ci"))
                conn.commit()
            
            temp_engine.dispose()
            logger.info(f"MySQL数据库 {MYSQL_DATABASE} 创建成功或已存在")
            
        except Exception as e:
            logger.error(f"创建MySQL数据库失败: {e}")
            raise


# 全局数据库管理器实例
db_manager = MySQLDatabaseManager()


# MySQL优化配置
@event.listens_for(engine, "connect")
def set_mysql_pragma(dbapi_connection, connection_record):
    """设置MySQL优化参数"""
    cursor = dbapi_connection.cursor()
    # 设置字符集
    cursor.execute(f"SET NAMES {MYSQL_CHARSET}")
    # 设置时区
    cursor.execute("SET time_zone = '+00:00'")
    # 设置SQL模式
    cursor.execute("SET sql_mode = 'STRICT_TRANS_TABLES,NO_ZERO_DATE,NO_ZERO_IN_DATE,ERROR_FOR_DIVISION_BY_ZERO'")
    cursor.close()


# 数据库健康检查
def health_check() -> dict:
    """MySQL数据库健康检查"""
    try:
        is_connected = db_manager.check_connection()
        db_info = db_manager.get_db_info()
        
        return {
            "status": "healthy" if is_connected else "unhealthy",
            "connected": is_connected,
            "database_info": db_info
        }
    except Exception as e:
        logger.error(f"MySQL数据库健康检查失败: {e}")
        return {
            "status": "unhealthy",
            "connected": False,
            "error": str(e)
        }


# 数据库初始化
def init_database():
    """应用启动时初始化MySQL数据库"""
    try:
        logger.info("开始初始化MySQL数据库...")
        
        # 创建数据库（如果不存在）
        db_manager.create_database_if_not_exists()
        
        # 检查连接
        if not db_manager.check_connection():
            raise Exception("无法连接到MySQL数据库")
        
        # 创建表
        create_tables()
        
        logger.info("MySQL数据库初始化完成")
        
    except Exception as e:
        logger.error(f"MySQL数据库初始化失败: {e}")
        raise
