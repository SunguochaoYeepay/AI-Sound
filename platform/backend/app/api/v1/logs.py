#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
日志监控API接口
支持日志查询、过滤、统计和导出功能
"""

import os
import json
import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Depends, Query, Request
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_, func, text
from pydantic import BaseModel

from ...database import get_db
from ...models.system import SystemLog
from ...utils.logger import LogLevel, LogModule

router = APIRouter(prefix="/logs", tags=["日志监控"])

# 配置日志
logger = logging.getLogger(__name__)


class LogQuery(BaseModel):
    """日志查询参数"""
    levels: Optional[List[str]] = None
    modules: Optional[List[str]] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    keyword: Optional[str] = None
    user_id: Optional[str] = None
    page: int = 1
    page_size: int = 50


class LogStats(BaseModel):
    """日志统计信息"""
    total: int
    by_level: Dict[str, int]
    by_module: Dict[str, int]
    recent_errors: int
    error_rate: float


@router.get("/list")
async def get_logs(
    level: Optional[str] = Query(None, description="日志级别过滤"),
    module: Optional[str] = Query(None, description="模块过滤"),
    start_time: Optional[str] = Query(None, description="开始时间 (ISO格式)"),
    end_time: Optional[str] = Query(None, description="结束时间 (ISO格式)"),
    keyword: Optional[str] = Query(None, description="关键词搜索"),
    user_id: Optional[str] = Query(None, description="用户ID过滤"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(50, ge=1, le=1000, description="每页数量"),
    db: Session = Depends(get_db)
):
    """
    获取日志列表
    支持多种过滤条件和分页
    """
    try:
        # 构建查询条件
        query = db.query(SystemLog)
        conditions = []
        
        # 级别过滤
        if level:
            try:
                log_level = LogLevel(level)
                conditions.append(SystemLog.level == log_level)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"无效的日志级别: {level}")
        
        # 模块过滤
        if module:
            try:
                log_module = LogModule(module)
                conditions.append(SystemLog.module == log_module)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"无效的模块名称: {module}")
        
        # 时间范围过滤
        if start_time:
            try:
                start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                conditions.append(SystemLog.created_at >= start_dt)
            except ValueError:
                raise HTTPException(status_code=400, detail="开始时间格式无效")
        
        if end_time:
            try:
                end_dt = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
                conditions.append(SystemLog.created_at <= end_dt)
            except ValueError:
                raise HTTPException(status_code=400, detail="结束时间格式无效")
        
        # 关键词搜索
        if keyword:
            keyword_filter = f"%{keyword}%"
            conditions.append(
                SystemLog.message.like(keyword_filter) |
                SystemLog.details.like(keyword_filter)
            )
        
        # 用户ID过滤
        if user_id:
            conditions.append(SystemLog.user_id == user_id)
        
        # 应用所有条件
        if conditions:
            query = query.filter(and_(*conditions))
        
        # 计算总数
        total = query.count()
        
        # 分页和排序
        logs = query.order_by(desc(SystemLog.created_at)) \
                   .offset((page - 1) * page_size) \
                   .limit(page_size) \
                   .all()
        
        # 转换为字典格式
        log_list = [log.to_dict() for log in logs]
        
        return {
            "success": True,
            "data": {
                "logs": log_list,
                "pagination": {
                    "page": page,
                    "page_size": page_size,
                    "total": total,
                    "total_pages": (total + page_size - 1) // page_size
                }
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取日志列表失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取日志列表失败: {str(e)}")


@router.get("/stats")
async def get_log_stats(
    hours: int = Query(24, ge=1, le=168, description="统计时间范围(小时)"),
    db: Session = Depends(get_db)
):
    """
    获取日志统计信息
    """
    try:
        # 计算时间范围
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=hours)
        
        # 总日志数
        total_logs = db.query(SystemLog).filter(
            SystemLog.created_at >= start_time
        ).count()
        
        # 按级别统计
        level_stats = db.query(
            SystemLog.level,
            func.count(SystemLog.id).label('count')
        ).filter(
            SystemLog.created_at >= start_time
        ).group_by(SystemLog.level).all()
        
        by_level = {level.value if hasattr(level, 'value') else str(level): count for level, count in level_stats}
        
        # 按模块统计
        module_stats = db.query(
            SystemLog.module,
            func.count(SystemLog.id).label('count')
        ).filter(
            SystemLog.created_at >= start_time
        ).group_by(SystemLog.module).all()
        
        by_module = {module.value if hasattr(module, 'value') else str(module): count for module, count in module_stats}
        
        # 最近错误数（最近1小时）
        recent_start = end_time - timedelta(hours=1)
        recent_errors = db.query(SystemLog).filter(
            and_(
                SystemLog.created_at >= recent_start,
                SystemLog.level.in_([LogLevel.ERROR, LogLevel.CRITICAL])
            )
        ).count()
        
        # 错误率计算
        error_count = by_level.get('ERROR', 0) + by_level.get('CRITICAL', 0)
        error_rate = (error_count / total_logs * 100) if total_logs > 0 else 0
        
        return {
            "success": True,
            "data": {
                "total": total_logs,
                "by_level": by_level,
                "by_module": by_module,
                "recent_errors": recent_errors,
                "error_rate": round(error_rate, 2),
                "time_range": {
                    "start_time": start_time.isoformat(),
                    "end_time": end_time.isoformat(),
                    "hours": hours
                }
            }
        }
        
    except Exception as e:
        logger.error(f"获取日志统计失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取日志统计失败: {str(e)}")


@router.get("/recent")
async def get_recent_logs(
    limit: int = Query(20, ge=1, le=100, description="返回数量"),
    level: Optional[str] = Query(None, description="级别过滤"),
    db: Session = Depends(get_db)
):
    """
    获取最近的日志记录
    """
    try:
        query = db.query(SystemLog)
        
        # 级别过滤
        if level:
            # 现在level是字符串字段，直接比较
            query = query.filter(SystemLog.level == level.upper())
        
        # 获取最近的日志
        recent_logs = query.order_by(desc(SystemLog.created_at)) \
                          .limit(limit) \
                          .all()
        
        return {
            "success": True,
            "data": [log.to_dict() for log in recent_logs]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取最近日志失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取最近日志失败: {str(e)}")


@router.get("/errors")
async def get_error_logs(
    hours: int = Query(24, ge=1, le=168, description="时间范围(小时)"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    db: Session = Depends(get_db)
):
    """
    获取错误日志
    """
    try:
        # 计算时间范围
        start_time = datetime.utcnow() - timedelta(hours=hours)
        
        # 查询错误和严重错误
        query = db.query(SystemLog).filter(
            and_(
                SystemLog.created_at >= start_time,
                SystemLog.level.in_(['ERROR', 'CRITICAL'])
            )
        )
        
        # 计算总数
        total = query.count()
        
        # 分页获取
        error_logs = query.order_by(desc(SystemLog.created_at)) \
                         .offset((page - 1) * page_size) \
                         .limit(page_size) \
                         .all()
        
        return {
            "success": True,
            "data": {
                "logs": [log.to_dict() for log in error_logs],
                "pagination": {
                    "page": page,
                    "page_size": page_size,
                    "total": total,
                    "total_pages": (total + page_size - 1) // page_size
                },
                "time_range": {
                    "hours": hours,
                    "start_time": start_time.isoformat()
                }
            }
        }
        
    except Exception as e:
        logger.error(f"获取错误日志失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取错误日志失败: {str(e)}")


@router.post("/clear")
async def clear_old_logs(
    days: int = Query(30, ge=1, le=365, description="保留天数"),
    db: Session = Depends(get_db)
):
    """
    清理旧日志
    保留指定天数内的日志，删除更早的记录
    """
    try:
        # 计算删除时间点
        cutoff_time = datetime.utcnow() - timedelta(days=days)
        
        # 查询要删除的日志数量
        delete_count = db.query(SystemLog).filter(
            SystemLog.created_at < cutoff_time
        ).count()
        
        # 执行删除
        deleted = db.query(SystemLog).filter(
            SystemLog.created_at < cutoff_time
        ).delete()
        
        db.commit()
        
        # 记录清理操作
        new_log = SystemLog(
            level=LogLevel.INFO,
            module=LogModule.SYSTEM,
            message=f"日志清理完成，删除了{deleted}条记录",
            details=json.dumps({
                "deleted_count": deleted,
                "cutoff_days": days,
                "cutoff_time": cutoff_time.isoformat()
            })
        )
        db.add(new_log)
        db.commit()
        
        return {
            "success": True,
            "message": f"日志清理完成，删除了{deleted}条记录",
            "data": {
                "deleted_count": deleted,
                "cutoff_days": days,
                "cutoff_time": cutoff_time.isoformat()
            }
        }
        
    except Exception as e:
        db.rollback()
        logger.error(f"清理日志失败: {e}")
        raise HTTPException(status_code=500, detail=f"清理日志失败: {str(e)}")


@router.get("/export")
async def export_logs(
    format: str = Query("json", description="导出格式: json, csv"),
    level: Optional[str] = Query(None, description="级别过滤"),
    module: Optional[str] = Query(None, description="模块过滤"),
    start_time: Optional[str] = Query(None, description="开始时间"),
    end_time: Optional[str] = Query(None, description="结束时间"),
    limit: int = Query(1000, ge=1, le=10000, description="最大导出数量"),
    db: Session = Depends(get_db)
):
    """
    导出日志
    支持JSON和CSV格式
    """
    try:
        from fastapi.responses import StreamingResponse
        import io
        import csv
        
        # 构建查询条件（复用list接口的逻辑）
        query = db.query(SystemLog)
        conditions = []
        
        if level:
            # 现在level是字符串字段，直接比较
            conditions.append(SystemLog.level == level.upper())
        
        if module:
            # 现在module是字符串字段，直接比较
            conditions.append(SystemLog.module == module.upper())
        
        if start_time:
            try:
                start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                conditions.append(SystemLog.created_at >= start_dt)
            except ValueError:
                raise HTTPException(status_code=400, detail="开始时间格式无效")
        
        if end_time:
            try:
                end_dt = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
                conditions.append(SystemLog.created_at <= end_dt)
            except ValueError:
                raise HTTPException(status_code=400, detail="结束时间格式无效")
        
        if conditions:
            query = query.filter(and_(*conditions))
        
        # 获取日志数据
        logs = query.order_by(desc(SystemLog.created_at)).limit(limit).all()
        log_data = [log.to_dict() for log in logs]
        
        if format.lower() == "csv":
            # CSV格式导出
            output = io.StringIO()
            if log_data:
                writer = csv.DictWriter(output, fieldnames=log_data[0].keys())
                writer.writeheader()
                writer.writerows(log_data)
            
            response = StreamingResponse(
                io.BytesIO(output.getvalue().encode('utf-8')),
                media_type="text/csv",
                headers={"Content-Disposition": f"attachment; filename=logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"}
            )
            
        else:
            # JSON格式导出
            json_data = json.dumps(log_data, indent=2, ensure_ascii=False)
            response = StreamingResponse(
                io.BytesIO(json_data.encode('utf-8')),
                media_type="application/json",
                headers={"Content-Disposition": f"attachment; filename=logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"}
            )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"导出日志失败: {e}")
        raise HTTPException(status_code=500, detail=f"导出日志失败: {str(e)}")


@router.get("/levels")
async def get_log_levels():
    """获取所有可用的日志级别"""
    return {
        "success": True,
        "data": [level.value for level in LogLevel]
    }


@router.get("/modules")
async def get_log_modules():
    """获取所有可用的日志模块"""
    return {
        "success": True,
        "data": [module.value for module in LogModule]
    }