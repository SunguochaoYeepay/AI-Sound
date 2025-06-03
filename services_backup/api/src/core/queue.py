"""
任务队列系统
支持优先级、重试、监控等功能
"""

import asyncio
import uuid
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, field
import logging

logger = logging.getLogger(__name__)


class TaskStatus(str, Enum):
    """任务状态"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskPriority(int, Enum):
    """任务优先级"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4


@dataclass
class Task:
    """任务对象"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    func: Optional[Callable] = None
    args: tuple = field(default_factory=tuple)
    kwargs: dict = field(default_factory=dict)
    priority: TaskPriority = TaskPriority.NORMAL
    status: TaskStatus = TaskStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Any = None
    error: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    timeout: Optional[float] = None
    
    def __lt__(self, other: 'Task') -> bool:
        """支持优先级队列排序"""
        return self.priority.value > other.priority.value


class TaskQueue:
    """任务队列"""
    
    def __init__(self, max_workers: int = 4):
        self.max_workers = max_workers
        self._queue: asyncio.PriorityQueue = asyncio.PriorityQueue()
        self._tasks: Dict[str, Task] = {}
        self._workers: List[asyncio.Task] = []
        self._running = False
        self._shutdown_event = asyncio.Event()
    
    async def start(self) -> None:
        """启动队列"""
        if self._running:
            return
        
        self._running = True
        self._shutdown_event.clear()
        
        # 启动工作者
        for i in range(self.max_workers):
            worker = asyncio.create_task(self._worker(f"worker-{i}"))
            self._workers.append(worker)
        
        logger.info(f"任务队列已启动，工作者数量: {self.max_workers}")
    
    async def stop(self) -> None:
        """停止队列"""
        if not self._running:
            return
        
        self._running = False
        self._shutdown_event.set()
        
        # 等待所有工作者完成
        if self._workers:
            await asyncio.gather(*self._workers, return_exceptions=True)
            self._workers.clear()
        
        logger.info("任务队列已停止")
    
    async def add_task(
        self,
        func: Callable,
        *args,
        name: str = "",
        priority: TaskPriority = TaskPriority.NORMAL,
        max_retries: int = 3,
        timeout: Optional[float] = None,
        **kwargs
    ) -> str:
        """添加任务"""
        task = Task(
            name=name or func.__name__,
            func=func,
            args=args,
            kwargs=kwargs,
            priority=priority,
            max_retries=max_retries,
            timeout=timeout
        )
        
        self._tasks[task.id] = task
        await self._queue.put(task)
        
        logger.info(f"任务已添加: {task.name} ({task.id})")
        return task.id
    
    async def get_task(self, task_id: str) -> Optional[Task]:
        """获取任务信息"""
        return self._tasks.get(task_id)
    
    async def cancel_task(self, task_id: str) -> bool:
        """取消任务"""
        task = self._tasks.get(task_id)
        if not task:
            return False
        
        if task.status in [TaskStatus.PENDING]:
            task.status = TaskStatus.CANCELLED
            logger.info(f"任务已取消: {task.name} ({task.id})")
            return True
        
        return False
    
    async def get_queue_status(self) -> Dict[str, Any]:
        """获取队列状态"""
        pending_count = sum(1 for t in self._tasks.values() if t.status == TaskStatus.PENDING)
        running_count = sum(1 for t in self._tasks.values() if t.status == TaskStatus.RUNNING)
        completed_count = sum(1 for t in self._tasks.values() if t.status == TaskStatus.COMPLETED)
        failed_count = sum(1 for t in self._tasks.values() if t.status == TaskStatus.FAILED)
        
        return {
            "running": self._running,
            "workers": len(self._workers),
            "queue_size": self._queue.qsize(),
            "total_tasks": len(self._tasks),
            "pending": pending_count,
            "running": running_count,
            "completed": completed_count,
            "failed": failed_count
        }
    
    async def _worker(self, worker_name: str) -> None:
        """工作者协程"""
        logger.info(f"工作者 {worker_name} 已启动")
        
        while self._running and not self._shutdown_event.is_set():
            try:
                # 等待任务，设置超时避免阻塞
                try:
                    task = await asyncio.wait_for(self._queue.get(), timeout=1.0)
                except asyncio.TimeoutError:
                    continue
                
                if task.status == TaskStatus.CANCELLED:
                    self._queue.task_done()
                    continue
                
                # 执行任务
                await self._execute_task(task, worker_name)
                self._queue.task_done()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"工作者 {worker_name} 异常: {e}")
        
        logger.info(f"工作者 {worker_name} 已停止")
    
    async def _execute_task(self, task: Task, worker_name: str) -> None:
        """执行任务"""
        logger.info(f"工作者 {worker_name} 开始执行任务: {task.name} ({task.id})")
        
        task.status = TaskStatus.RUNNING
        task.started_at = datetime.now()
        
        try:
            # 执行任务函数
            if asyncio.iscoroutinefunction(task.func):
                if task.timeout:
                    task.result = await asyncio.wait_for(
                        task.func(*task.args, **task.kwargs),
                        timeout=task.timeout
                    )
                else:
                    task.result = await task.func(*task.args, **task.kwargs)
            else:
                task.result = task.func(*task.args, **task.kwargs)
            
            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.now()
            logger.info(f"任务执行成功: {task.name} ({task.id})")
            
        except Exception as e:
            task.error = str(e)
            task.retry_count += 1
            
            if task.retry_count <= task.max_retries:
                # 重试任务
                task.status = TaskStatus.PENDING
                await self._queue.put(task)
                logger.warning(f"任务执行失败，将重试 ({task.retry_count}/{task.max_retries}): {task.name} - {e}")
            else:
                # 任务失败
                task.status = TaskStatus.FAILED
                task.completed_at = datetime.now()
                logger.error(f"任务执行失败: {task.name} ({task.id}) - {e}")


# 全局任务队列实例
task_queue = TaskQueue()