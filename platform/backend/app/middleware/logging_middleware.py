#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
日志记录中间件
自动记录API请求和响应
"""

import time
import json
import logging
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from ..utils.logger import log_api_request
from ..models.log import LogModule

logger = logging.getLogger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    API请求日志记录中间件
    自动记录所有API请求的详细信息
    """
    
    def __init__(self, app, skip_paths: list = None):
        super().__init__(app)
        # 跳过记录的路径（避免日志过多）
        self.skip_paths = skip_paths or [
            "/health",
            "/docs",
            "/redoc",
            "/openapi.json",
            "/favicon.ico",
            "/static/"
        ]
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """处理请求并记录日志"""
        start_time = time.time()
        
        # 获取请求信息
        method = request.method
        path = str(request.url.path)
        query_params = str(request.query_params) if request.query_params else None
        
        # 检查是否需要跳过日志记录
        should_skip = any(skip_path in path for skip_path in self.skip_paths)
        
        # 获取客户端信息
        client_ip = self._get_client_ip(request)
        user_agent = request.headers.get("user-agent", "")
        user_id = self._extract_user_id(request)
        session_id = self._extract_session_id(request)
        
        # 记录请求体（仅用于POST/PUT/PATCH请求）
        request_body = None
        if method in ["POST", "PUT", "PATCH"] and not should_skip:
            try:
                # 读取请求体
                body = await request.body()
                if body:
                    # 尝试解析JSON
                    try:
                        request_body = json.loads(body.decode())
                        # 移除敏感信息
                        request_body = self._sanitize_request_body(request_body)
                    except (json.JSONDecodeError, UnicodeDecodeError):
                        request_body = {"raw_body_size": len(body)}
                
                # 重新构建请求对象以便后续处理
                async def receive():
                    return {"type": "http.request", "body": body}
                
                request._receive = receive
                
            except Exception as e:
                logger.warning(f"读取请求体失败: {e}")
        
        try:
            # 处理请求
            response = await call_next(request)
            
            # 计算响应时间
            process_time = (time.time() - start_time) * 1000  # 转换为毫秒
            
            # 记录日志（如果不需要跳过）
            if not should_skip:
                try:
                    # 准备日志详情
                    log_details = {
                        "query_params": query_params,
                        "request_body": request_body,
                        "response_size": response.headers.get("content-length"),
                        "content_type": response.headers.get("content-type")
                    }
                    
                    # 记录API请求日志
                    log_api_request(
                        method=method,
                        path=path,
                        status_code=response.status_code,
                        response_time=process_time,
                        user_id=user_id,
                        ip_address=client_ip,
                        user_agent=user_agent,
                        **log_details
                    )
                    
                except Exception as e:
                    logger.error(f"记录API日志失败: {e}")
            
            # 添加响应头
            response.headers["X-Process-Time"] = str(process_time)
            
            return response
            
        except Exception as e:
            # 记录异常
            process_time = (time.time() - start_time) * 1000
            
            if not should_skip:
                try:
                    log_api_request(
                        method=method,
                        path=path,
                        status_code=500,
                        response_time=process_time,
                        user_id=user_id,
                        ip_address=client_ip,
                        user_agent=user_agent,
                        error_message=str(e),
                        exception_type=type(e).__name__
                    )
                except Exception as log_error:
                    logger.error(f"记录异常日志失败: {log_error}")
            
            # 重新抛出异常
            raise e
    
    def _get_client_ip(self, request: Request) -> str:
        """获取客户端IP地址"""
        # 优先从代理头获取真实IP
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        # 从连接信息获取
        if hasattr(request, "client") and request.client:
            return request.client.host
        
        return "unknown"
    
    def _extract_user_id(self, request: Request) -> str:
        """从请求中提取用户ID"""
        # 可以从Token、Session或其他认证信息中提取
        # 这里简化处理，实际项目中需要根据认证方式调整
        auth_header = request.headers.get("Authorization")
        if auth_header:
            # TODO: 解析JWT Token获取用户ID
            return "from_token"
        
        # 从Cookie中获取会话信息
        session_cookie = request.cookies.get("session_id")
        if session_cookie:
            # TODO: 从会话中获取用户ID
            return "from_session"
        
        return None
    
    def _extract_session_id(self, request: Request) -> str:
        """从请求中提取会话ID"""
        # 优先从自定义头获取
        session_id = request.headers.get("X-Session-ID")
        if session_id:
            return session_id
        
        # 从Cookie获取
        session_cookie = request.cookies.get("session_id")
        if session_cookie:
            return session_cookie
        
        return None
    
    def _sanitize_request_body(self, body: dict) -> dict:
        """清理请求体，移除敏感信息"""
        if not isinstance(body, dict):
            return body
        
        # 需要移除的敏感字段
        sensitive_fields = {
            "password", "passwd", "pwd",
            "token", "api_key", "secret",
            "private_key", "access_token",
            "refresh_token", "auth_token"
        }
        
        sanitized = {}
        for key, value in body.items():
            if key.lower() in sensitive_fields:
                sanitized[key] = "***REDACTED***"
            elif isinstance(value, dict):
                sanitized[key] = self._sanitize_request_body(value)
            elif isinstance(value, list):
                sanitized[key] = [
                    self._sanitize_request_body(item) if isinstance(item, dict) else item
                    for item in value
                ]
            else:
                sanitized[key] = value
        
        return sanitized