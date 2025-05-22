"""
缓存工具
"""

import logging

logger = logging.getLogger("utils.cache")

def has_redis() -> bool:
    """
    检查是否可以使用Redis
    
    Returns:
        bool: Redis是否可用
    """
    try:
        import redis
        return True
    except ImportError:
        return False

def get_redis_client(redis_url: str = "redis://localhost:6379/0"):
    """
    获取Redis客户端
    
    Args:
        redis_url: Redis连接URL
        
    Returns:
        Redis客户端或None
    """
    if not has_redis():
        logger.warning("Redis包未安装，无法使用Redis")
        return None
    
    try:
        import redis
        return redis.from_url(redis_url)
    except Exception as e:
        logger.error(f"连接Redis失败: {e}")
        return None