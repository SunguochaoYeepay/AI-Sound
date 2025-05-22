"""
任务存储实现，支持内存和Redis存储
"""

import json
from typing import Dict, List, Any, Optional

class TaskStore:
    """任务存储基类"""
    def set_task(self, task_id: str, data: Dict[str, Any]) -> None:
        raise NotImplementedError()
    
    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        raise NotImplementedError()
    
    def update_task(self, task_id: str, data: Dict[str, Any]) -> None:
        raise NotImplementedError()
    
    def delete_task(self, task_id: str) -> None:
        raise NotImplementedError()

class TaskMemoryStore(TaskStore):
    """内存任务存储"""
    def __init__(self):
        self.tasks = {}
    
    def set_task(self, task_id: str, data: Dict[str, Any]) -> None:
        self.tasks[task_id] = data
    
    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        return self.tasks.get(task_id)
    
    def update_task(self, task_id: str, data: Dict[str, Any]) -> None:
        if task_id in self.tasks:
            self.tasks[task_id].update(data)
    
    def delete_task(self, task_id: str) -> None:
        if task_id in self.tasks:
            del self.tasks[task_id]

class TaskRedisStore(TaskStore):
    """Redis任务存储"""
    def __init__(self, redis_client):
        self.redis = redis_client
        self.prefix = "megatts:task:"
    
    def set_task(self, task_id: str, data: Dict[str, Any]) -> None:
        key = f"{self.prefix}{task_id}"
        self.redis.hset(key, mapping={k: json.dumps(v) for k, v in data.items()})
        # 设置过期时间（3天）
        self.redis.expire(key, 60 * 60 * 24 * 3)
    
    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        key = f"{self.prefix}{task_id}"
        if not self.redis.exists(key):
            return None
        
        data = self.redis.hgetall(key)
        if not data:
            return None
        
        # 转换回Python对象
        return {k.decode() if isinstance(k, bytes) else k: 
                json.loads(v.decode() if isinstance(v, bytes) else v) 
                for k, v in data.items()}
    
    def update_task(self, task_id: str, data: Dict[str, Any]) -> None:
        key = f"{self.prefix}{task_id}"
        if self.redis.exists(key):
            self.redis.hset(key, mapping={k: json.dumps(v) for k, v in data.items()})
            # 更新过期时间
            self.redis.expire(key, 60 * 60 * 24 * 3)
    
    def delete_task(self, task_id: str) -> None:
        key = f"{self.prefix}{task_id}"
        self.redis.delete(key)