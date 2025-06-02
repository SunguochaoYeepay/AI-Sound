"""
SQLite 数据库连接和会话管理
"""

from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.engine import Engine
import sqlite3
import os
import logging

logger = logging.getLogger(__name__)

# 数据库配置
DATABASE_DIR = "../data"
DATABASE_PATH = os.path.join(DATABASE_DIR, "database.db")
DATABASE_URL = f"sqlite:///{DATABASE_PATH}"

# 创建数据库引擎
engine = create_engine(
    DATABASE_URL,
    connect_args={
        "check_same_thread": False,  # SQLite多线程支持
        "timeout": 20  # 连接超时时间
    },
    echo=False,  # 设为True可以看到SQL日志
    pool_pre_ping=True  # 连接池预检查
)

# 启用SQLite外键约束
@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    if isinstance(dbapi_connection, sqlite3.Connection):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("PRAGMA journal_mode=WAL")  # 写前日志模式，提高并发性能
        cursor.execute("PRAGMA synchronous=NORMAL")  # 平衡性能和安全性
        cursor.execute("PRAGMA cache_size=10000")  # 增大缓存
        cursor.execute("PRAGMA temp_store=MEMORY")  # 临时表存储在内存
        cursor.close()

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
    初始化数据库
    创建所有表结构
    """
    try:
        # 确保数据库目录存在
        os.makedirs(DATABASE_DIR, exist_ok=True)
        
        # 导入所有模型以确保表被创建
        from . import models
        
        # 创建所有表
        Base.metadata.create_all(bind=engine)
        
        logger.info(f"✅ 数据库初始化完成: {DATABASE_PATH}")
        
        # 检查数据库连接
        with SessionLocal() as db:
            result = db.execute("SELECT sqlite_version()")
            version = result.fetchone()[0]
            logger.info(f"📊 SQLite版本: {version}")
            
    except Exception as e:
        logger.error(f"❌ 数据库初始化失败: {str(e)}")
        raise

def get_db_info():
    """
    获取数据库信息
    """
    try:
        with SessionLocal() as db:
            # 获取数据库大小
            db_size = os.path.getsize(DATABASE_PATH) if os.path.exists(DATABASE_PATH) else 0
            
            # 获取表信息
            tables_info = db.execute("""
                SELECT name, type FROM sqlite_master 
                WHERE type='table' AND name NOT LIKE 'sqlite_%'
                ORDER BY name
            """).fetchall()
            
            return {
                "database_path": DATABASE_PATH,
                "database_size_mb": round(db_size / (1024 * 1024), 2),
                "tables_count": len(tables_info),
                "tables": [{"name": table[0], "type": table[1]} for table in tables_info]
            }
    except Exception as e:
        logger.error(f"获取数据库信息失败: {str(e)}")
        return {"error": str(e)}

def backup_database(backup_path: str = None):
    """
    备份数据库
    """
    try:
        if not backup_path:
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = f"{DATABASE_DIR}/backup_database_{timestamp}.db"
        
        import shutil
        shutil.copy2(DATABASE_PATH, backup_path)
        
        logger.info(f"✅ 数据库备份完成: {backup_path}")
        return backup_path
    except Exception as e:
        logger.error(f"❌ 数据库备份失败: {str(e)}")
        raise

def reset_database():
    """
    重置数据库 - 谨慎使用!
    """
    try:
        if os.path.exists(DATABASE_PATH):
            # 先备份
            backup_path = backup_database()
            logger.info(f"🔄 重置前已备份到: {backup_path}")
            
            # 删除数据库文件
            os.remove(DATABASE_PATH)
            
        # 重新初始化
        init_db()
        
        logger.info("✅ 数据库重置完成")
    except Exception as e:
        logger.error(f"❌ 数据库重置失败: {str(e)}")
        raise 