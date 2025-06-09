"""
自定义异常类
定义应用特有的异常类型
"""

from typing import Any, Dict, Optional


class BaseAIException(Exception):
    """基础异常类"""
    
    def __init__(
        self, 
        message: str, 
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None
    ):
        self.detail = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(message)


class ServiceException(BaseAIException):
    """通用服务异常"""
    
    def __init__(
        self, 
        message: str = "服务异常", 
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, status_code, details)


class DifyAPIException(BaseAIException):
    """Dify API异常"""
    
    def __init__(
        self, 
        message: str = "Dify API调用异常", 
        status_code: int = 503,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, status_code, details)


class TTSException(BaseAIException):
    """TTS异常"""
    
    def __init__(
        self, 
        message: str = "TTS服务异常", 
        status_code: int = 503,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, status_code, details)


class AIServiceException(BaseAIException):
    """AI服务异常"""
    
    def __init__(
        self, 
        message: str = "AI服务异常", 
        status_code: int = 503,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, status_code, details)


class TTSServiceException(BaseAIException):
    """TTS服务异常"""
    
    def __init__(
        self, 
        message: str = "TTS服务异常", 
        status_code: int = 503,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, status_code, details)


class FileProcessingException(BaseAIException):
    """文件处理异常"""
    
    def __init__(
        self, 
        message: str = "文件处理异常", 
        status_code: int = 422,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, status_code, details)


class ValidationException(BaseAIException):
    """验证异常"""
    
    def __init__(
        self, 
        message: str = "数据验证失败", 
        status_code: int = 400,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, status_code, details)


class DatabaseException(BaseAIException):
    """数据库异常"""
    
    def __init__(
        self, 
        message: str = "数据库操作异常", 
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, status_code, details)


class AuthenticationException(BaseAIException):
    """认证异常"""
    
    def __init__(
        self, 
        message: str = "认证失败", 
        status_code: int = 401,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, status_code, details)


class AuthorizationException(BaseAIException):
    """授权异常"""
    
    def __init__(
        self, 
        message: str = "权限不足", 
        status_code: int = 403,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, status_code, details)


class ResourceNotFoundException(BaseAIException):
    """资源不存在异常"""
    
    def __init__(
        self, 
        message: str = "资源不存在", 
        status_code: int = 404,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, status_code, details)


class RateLimitException(BaseAIException):
    """频率限制异常"""
    
    def __init__(
        self, 
        message: str = "请求过于频繁", 
        status_code: int = 429,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, status_code, details)


class ServiceUnavailableException(BaseAIException):
    """服务不可用异常"""
    
    def __init__(
        self, 
        message: str = "服务暂时不可用", 
        status_code: int = 503,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, status_code, details) 