"""
系统异常定义和处理工具
定义各种业务异常类型，提供统一的错误处理机制
"""

from typing import Dict, Any, Optional


class BaseServiceException(Exception):
    """服务异常基类"""
    
    def __init__(
        self, 
        message: str, 
        code: str = None, 
        details: Dict[str, Any] = None,
        status_code: int = 400
    ):
        self.message = message
        self.code = code or self.__class__.__name__
        self.details = details or {}
        self.status_code = status_code
        super().__init__(message)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "error": True,
            "code": self.code,
            "message": self.message,
            "details": self.details,
            "status_code": self.status_code
        }


class ServiceException(BaseServiceException):
    """通用服务异常"""
    pass


class ValidationException(BaseServiceException):
    """数据验证异常"""
    
    def __init__(self, message: str, field: str = None, details: Dict[str, Any] = None):
        super().__init__(message, "VALIDATION_ERROR", details, 422)
        self.field = field


class DifyAPIException(BaseServiceException):
    """Dify API 异常"""
    
    def __init__(self, message: str, details: Dict[str, Any] = None):
        super().__init__(message, "DIFY_API_ERROR", details, 503)


class TTSException(BaseServiceException):
    """TTS 服务异常"""
    
    def __init__(self, message: str, details: Dict[str, Any] = None):
        super().__init__(message, "TTS_ERROR", details, 503)


class DatabaseException(BaseServiceException):
    """数据库异常"""
    
    def __init__(self, message: str, details: Dict[str, Any] = None):
        super().__init__(message, "DATABASE_ERROR", details, 500)


class FileException(BaseServiceException):
    """文件处理异常"""
    
    def __init__(self, message: str, file_path: str = None, details: Dict[str, Any] = None):
        super().__init__(message, "FILE_ERROR", details, 500)
        self.file_path = file_path


class AuthenticationException(BaseServiceException):
    """认证异常"""
    
    def __init__(self, message: str = "认证失败", details: Dict[str, Any] = None):
        super().__init__(message, "AUTHENTICATION_ERROR", details, 401)


class AuthorizationException(BaseServiceException):
    """授权异常"""
    
    def __init__(self, message: str = "权限不足", details: Dict[str, Any] = None):
        super().__init__(message, "AUTHORIZATION_ERROR", details, 403)


class ResourceNotFoundException(BaseServiceException):
    """资源未找到异常"""
    
    def __init__(self, resource_type: str, resource_id: str = None, details: Dict[str, Any] = None):
        message = f"{resource_type}不存在"
        if resource_id:
            message += f": {resource_id}"
        super().__init__(message, "RESOURCE_NOT_FOUND", details, 404)
        self.resource_type = resource_type
        self.resource_id = resource_id


class RateLimitException(BaseServiceException):
    """频率限制异常"""
    
    def __init__(self, message: str = "请求过于频繁", retry_after: int = None, details: Dict[str, Any] = None):
        super().__init__(message, "RATE_LIMIT_ERROR", details, 429)
        self.retry_after = retry_after


class ConfigurationException(BaseServiceException):
    """配置异常"""
    
    def __init__(self, message: str, config_key: str = None, details: Dict[str, Any] = None):
        super().__init__(message, "CONFIGURATION_ERROR", details, 500)
        self.config_key = config_key


class BookNotFoundError(BaseServiceException):
    """书籍未找到异常"""
    
    def __init__(self, message: str = "书籍不存在", book_id: str = None, details: Dict[str, Any] = None):
        super().__init__(message, "BOOK_NOT_FOUND", details, 404)
        self.book_id = book_id


class ChapterProcessingError(BaseServiceException):
    """章节处理异常"""
    
    def __init__(self, message: str, chapter_id: str = None, details: Dict[str, Any] = None):
        super().__init__(message, "CHAPTER_PROCESSING_ERROR", details, 400)
        self.chapter_id = chapter_id


class AnalysisSessionNotFoundError(BaseServiceException):
    """分析会话未找到异常"""
    
    def __init__(self, message: str = "分析会话不存在", session_id: str = None, details: Dict[str, Any] = None):
        super().__init__(message, "ANALYSIS_SESSION_NOT_FOUND", details, 404)
        self.session_id = session_id


class AnalysisConfigError(BaseServiceException):
    """分析配置异常"""
    
    def __init__(self, message: str, config_field: str = None, details: Dict[str, Any] = None):
        super().__init__(message, "ANALYSIS_CONFIG_ERROR", details, 400)
        self.config_field = config_field


class LLMServiceError(BaseServiceException):
    """LLM服务异常"""
    
    def __init__(self, message: str, service_type: str = None, details: Dict[str, Any] = None):
        super().__init__(message, "LLM_SERVICE_ERROR", details, 503)
        self.service_type = service_type 