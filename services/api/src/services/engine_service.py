"""
引擎服务
提供引擎管理和监控的核心业务逻辑
"""

import asyncio
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
import logging

from ..models.engine import (
    Engine, EngineCreate, EngineUpdate, EngineHealthCheck,
    EngineStatus, EngineType
)
from ..adapters.factory import AdapterFactory
from ..core.database import get_collection
from ..core.config import settings

logger = logging.getLogger(__name__)


class EngineService:
    """引擎服务"""
    
    def __init__(self, db):
        self.db = db
        self.collection = db["engines"]
        self.adapter_factory = AdapterFactory()
        self._health_check_interval = 60  # 健康检查间隔(秒)
        self._health_check_task = None
    
    async def list_engines(
        self, 
        skip: int = 0, 
        limit: int = 50,
        status: Optional[EngineStatus] = None,
        engine_type: Optional[EngineType] = None,
        enabled_only: bool = False
    ) -> List[Engine]:
        """获取引擎列表"""
        try:
            # 构建查询条件
            query = {}
            if status:
                query["status"] = status.value
            if engine_type:
                query["type"] = engine_type.value
            if enabled_only:
                query["is_enabled"] = True
            
            cursor = self.collection.find(query).skip(skip).limit(limit)
            engines = []
            async for doc in cursor:
                doc["_id"] = str(doc["_id"])  # 转换ObjectId
                engines.append(Engine(**doc))
            
            return engines
        except Exception as e:
            logger.error(f"获取引擎列表失败: {e}")
            raise
    
    async def get_engine(self, engine_id: str) -> Optional[Engine]:
        """获取指定引擎"""
        try:
            doc = await self.collection.find_one({"id": engine_id})
            if doc:
                doc["_id"] = str(doc["_id"])
                return Engine(**doc)
            return None
        except Exception as e:
            logger.error(f"获取引擎失败: {e}")
            raise
    
    async def create_engine(self, engine_data: EngineCreate) -> Engine:
        """创建新引擎"""
        try:
            # 生成引擎ID
            engine_id = f"{engine_data.type.value}_{int(datetime.now().timestamp())}"
            
            # 创建引擎对象
            engine = Engine(
                id=engine_id,
                **engine_data.dict()
            )
            
            # 保存到数据库
            await self.collection.insert_one(engine.dict())
            
            # 尝试初始化适配器
            try:
                await self._initialize_engine_adapter(engine)
                engine.status = EngineStatus.READY
            except Exception as e:
                engine.status = EngineStatus.ERROR
                engine.error_message = str(e)
                logger.warning(f"引擎适配器初始化失败: {e}")
            
            # 更新状态
            await self.collection.update_one(
                {"id": engine_id},
                {"$set": {"status": engine.status.value, "error_message": engine.error_message}}
            )
            
            logger.info(f"引擎已创建: {engine_id}")
            return engine
        except Exception as e:
            logger.error(f"创建引擎失败: {e}")
            raise
    
    async def update_engine(self, engine_id: str, engine_data: EngineUpdate) -> Optional[Engine]:
        """更新引擎"""
        try:
            # 检查引擎是否存在
            existing = await self.get_engine(engine_id)
            if not existing:
                return None
            
            # 准备更新数据
            update_data = {k: v for k, v in engine_data.dict().items() if v is not None}
            update_data["updated_at"] = datetime.now()
            
            # 更新数据库
            result = await self.collection.update_one(
                {"id": engine_id},
                {"$set": update_data}
            )
            
            if result.modified_count > 0:
                # 如果配置有变化，重新初始化适配器
                if "config" in update_data:
                    try:
                        updated_engine = await self.get_engine(engine_id)
                        await self._initialize_engine_adapter(updated_engine)
                        await self.collection.update_one(
                            {"id": engine_id},
                            {"$set": {"status": EngineStatus.READY.value, "error_message": None}}
                        )
                    except Exception as e:
                        await self.collection.update_one(
                            {"id": engine_id},
                            {"$set": {"status": EngineStatus.ERROR.value, "error_message": str(e)}}
                        )
                
                logger.info(f"引擎已更新: {engine_id}")
                return await self.get_engine(engine_id)
            
            return existing
        except Exception as e:
            logger.error(f"更新引擎失败: {e}")
            raise
    
    async def delete_engine(self, engine_id: str) -> bool:
        """删除引擎"""
        try:
            # 先从适配器工厂移除
            await self.adapter_factory.remove_adapter(engine_id)
            
            # 从数据库删除
            result = await self.collection.delete_one({"id": engine_id})
            
            if result.deleted_count > 0:
                logger.info(f"引擎已删除: {engine_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"删除引擎失败: {e}")
            raise
    
    async def enable_engine(self, engine_id: str) -> bool:
        """启用引擎"""
        try:
            engine = await self.get_engine(engine_id)
            if not engine:
                return False
            
            # 尝试初始化适配器
            try:
                await self._initialize_engine_adapter(engine)
                status = EngineStatus.READY
                error_message = None
            except Exception as e:
                status = EngineStatus.ERROR
                error_message = str(e)
            
            # 更新状态
            result = await self.collection.update_one(
                {"id": engine_id},
                {"$set": {
                    "is_enabled": True,
                    "status": status.value,
                    "error_message": error_message,
                    "updated_at": datetime.now()
                }}
            )
            
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"启用引擎失败: {e}")
            raise
    
    async def disable_engine(self, engine_id: str) -> bool:
        """禁用引擎"""
        try:
            # 从适配器工厂移除
            await self.adapter_factory.remove_adapter(engine_id)
            
            # 更新状态
            result = await self.collection.update_one(
                {"id": engine_id},
                {"$set": {
                    "is_enabled": False,
                    "status": EngineStatus.OFFLINE.value,
                    "updated_at": datetime.now()
                }}
            )
            
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"禁用引擎失败: {e}")
            raise
    
    async def health_check_engine(self, engine_id: str) -> EngineHealthCheck:
        """引擎健康检查"""
        try:
            start_time = datetime.now()
            
            # 获取适配器
            adapter = await self.adapter_factory.get_adapter(engine_id)
            
            if not adapter:
                return EngineHealthCheck(
                    engine_id=engine_id,
                    status=EngineStatus.ERROR,
                    response_time=0.0,
                    error_message="适配器未找到"
                )
            
            # 执行健康检查
            try:
                health_result = await adapter.health_check()
                end_time = datetime.now()
                response_time = (end_time - start_time).total_seconds() * 1000
                
                # 更新引擎状态
                await self.collection.update_one(
                    {"id": engine_id},
                    {"$set": {
                        "status": EngineStatus.READY.value,
                        "last_health_check": datetime.now(),
                        "error_message": None
                    }}
                )
                
                return EngineHealthCheck(
                    engine_id=engine_id,
                    status=EngineStatus.READY,
                    response_time=response_time,
                    details=health_result
                )
            
            except Exception as e:
                end_time = datetime.now()
                response_time = (end_time - start_time).total_seconds() * 1000
                
                # 更新引擎状态
                await self.collection.update_one(
                    {"id": engine_id},
                    {"$set": {
                        "status": EngineStatus.ERROR.value,
                        "last_health_check": datetime.now(),
                        "error_message": str(e)
                    }}
                )
                
                return EngineHealthCheck(
                    engine_id=engine_id,
                    status=EngineStatus.ERROR,
                    response_time=response_time,
                    error_message=str(e)
                )
        
        except Exception as e:
            logger.error(f"引擎健康检查失败: {e}")
            raise
    
    async def get_engine_stats(self) -> Dict[str, Any]:
        """获取引擎统计信息"""
        try:
            # 从数据库获取统计
            total = await self.collection.count_documents({})
            enabled = await self.collection.count_documents({"is_enabled": True})
            ready = await self.collection.count_documents({"status": EngineStatus.READY.value})
            error = await self.collection.count_documents({"status": EngineStatus.ERROR.value})
            
            # 从适配器工厂获取运行时统计
            adapter_stats = self.adapter_factory.get_adapter_stats()
            
            # 按类型统计
            type_stats = {}
            for engine_type in EngineType:
                count = await self.collection.count_documents({"type": engine_type.value})
                type_stats[engine_type.value] = count
            
            # 最近活动
            recent_activity = []
            cursor = self.collection.find({}).sort("updated_at", -1).limit(5)
            async for doc in cursor:
                recent_activity.append({
                    "engine_id": doc["id"],
                    "name": doc["name"],
                    "action": "updated",
                    "timestamp": doc.get("updated_at", doc["created_at"])
                })
            
            return {
                "total_engines": total,
                "enabled_engines": enabled,
                "ready_engines": ready,
                "error_engines": error,
                "type_distribution": type_stats,
                "adapter_stats": adapter_stats,
                "recent_activity": recent_activity,
                "health_check_interval": self._health_check_interval
            }
        except Exception as e:
            logger.error(f"获取引擎统计失败: {e}")
            raise

    async def check_all_health(self) -> Dict[str, Any]:
        """检查所有引擎的健康状态"""
        try:
            # 获取所有启用的引擎
            engines = await self.list_engines(enabled_only=True)
            
            health_results = {}
            total_checked = 0
            healthy_count = 0
            
            # 并发检查所有引擎
            tasks = []
            for engine in engines:
                tasks.append(self._check_single_engine_health(engine))
            
            if tasks:
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                for i, result in enumerate(results):
                    engine = engines[i]
                    total_checked += 1
                    
                    if isinstance(result, Exception):
                        health_results[engine.id] = {
                            "engine_id": engine.id,
                            "name": engine.name,
                            "healthy": False,
                            "status": "error",
                            "error": str(result),
                            "checked_at": datetime.now()
                        }
                    else:
                        health_results[engine.id] = result
                        if result.get("healthy", False):
                            healthy_count += 1
            
            # 更新数据库中的健康状态
            for engine_id, health_data in health_results.items():
                await self.collection.update_one(
                    {"id": engine_id},
                    {"$set": {
                        "last_health_check": health_data["checked_at"],
                        "status": EngineStatus.READY.value if health_data["healthy"] else EngineStatus.ERROR.value
                    }}
                )
            
            return {
                "summary": {
                    "total_checked": total_checked,
                    "healthy_count": healthy_count,
                    "unhealthy_count": total_checked - healthy_count,
                    "health_rate": (healthy_count / total_checked * 100) if total_checked > 0 else 0
                },
                "details": health_results,
                "checked_at": datetime.now()
            }
        except Exception as e:
            logger.error(f"批量健康检查失败: {e}")
            raise

    async def get_engines_summary(self) -> Dict[str, Any]:
        """获取引擎摘要信息"""
        try:
            # 获取基础统计
            stats = await self.get_engine_stats()
            
            # 获取引擎列表（简化信息）
            engines = await self.list_engines(limit=100)
            engine_summary = []
            
            for engine in engines:
                # 获取适配器状态
                adapter = await self.adapter_factory.get_adapter(engine.id)
                adapter_status = "unknown"
                if adapter:
                    adapter_status = adapter.status.value
                
                engine_summary.append({
                    "id": engine.id,
                    "name": engine.name,
                    "type": engine.type.value,
                    "status": engine.status.value,
                    "adapter_status": adapter_status,
                    "is_enabled": engine.is_enabled,
                    "last_health_check": engine.last_health_check,
                    "created_at": engine.created_at
                })
            
            # 获取性能指标
            performance_metrics = await self._get_performance_metrics()
            
            return {
                "statistics": stats,
                "engines": engine_summary,
                "performance": performance_metrics,
                "system_info": {
                    "monitoring_enabled": self._health_check_task is not None,
                    "check_interval": self._health_check_interval,
                    "adapter_factory_stats": self.adapter_factory.get_adapter_stats()
                }
            }
        except Exception as e:
            logger.error(f"获取引擎摘要失败: {e}")
            raise

    async def _check_single_engine_health(self, engine: Engine) -> Dict[str, Any]:
        """检查单个引擎的健康状态"""
        try:
            adapter = await self.adapter_factory.get_adapter(engine.id)
            if not adapter:
                return {
                    "engine_id": engine.id,
                    "name": engine.name,
                    "healthy": False,
                    "status": "adapter_not_found",
                    "error": "适配器未找到",
                    "checked_at": datetime.now()
                }
            
            # 执行健康检查
            health_data = await adapter.health_check()
            
            return {
                "engine_id": engine.id,
                "name": engine.name,
                "healthy": adapter.is_ready,
                "status": adapter.status.value,
                "details": health_data,
                "checked_at": datetime.now()
            }
        except Exception as e:
            return {
                "engine_id": engine.id,
                "name": engine.name,
                "healthy": False,
                "status": "check_failed",
                "error": str(e),
                "checked_at": datetime.now()
            }

    async def _get_performance_metrics(self) -> Dict[str, Any]:
        """获取性能指标"""
        try:
            # 这里可以添加更多性能指标
            # 例如：响应时间、吞吐量、错误率等
            
            return {
                "avg_response_time": 0.0,  # 平均响应时间(秒)
                "total_requests": 0,       # 总请求数
                "success_rate": 100.0,     # 成功率(%)
                "error_rate": 0.0,         # 错误率(%)
                "uptime": "100%"           # 运行时间
            }
        except Exception as e:
            logger.warning(f"获取性能指标失败: {e}")
            return {}
    
    async def start_health_monitoring(self):
        """启动健康监控"""
        if self._health_check_task:
            return
        
        self._health_check_task = asyncio.create_task(self._health_monitor_loop())
        logger.info("引擎健康监控已启动")
    
    async def stop_health_monitoring(self):
        """停止健康监控"""
        if self._health_check_task:
            self._health_check_task.cancel()
            try:
                await self._health_check_task
            except asyncio.CancelledError:
                pass
            self._health_check_task = None
            logger.info("引擎健康监控已停止")
    
    async def _health_monitor_loop(self):
        """健康监控循环"""
        while True:
            try:
                # 获取所有启用的引擎
                engines = await self.list_engines(enabled_only=True)
                
                # 对每个引擎进行健康检查
                for engine in engines:
                    try:
                        await self.health_check_engine(engine.id)
                    except Exception as e:
                        logger.error(f"引擎健康检查失败 {engine.id}: {e}")
                
                # 等待下次检查
                await asyncio.sleep(self._health_check_interval)
            
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"健康监控循环异常: {e}")
                await asyncio.sleep(10)  # 异常后短暂等待
    
    async def _initialize_engine_adapter(self, engine: Engine):
        """初始化引擎适配器"""
        try:
            # 注册适配器
            await self.adapter_factory.register_adapter(
                engine_id=engine.id,
                engine_type=engine.type,
                config=engine.config.dict()
            )
            
            # 测试适配器
            adapter = await self.adapter_factory.get_adapter(engine.id)
            if adapter:
                await adapter.health_check()
            
            logger.info(f"引擎适配器初始化成功: {engine.id}")
        except Exception as e:
            logger.error(f"引擎适配器初始化失败 {engine.id}: {e}")
            raise