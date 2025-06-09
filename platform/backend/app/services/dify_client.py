"""
Dify API 客户端
提供与Dify平台的完整集成，支持工作流调用、对话管理、文件上传等功能
"""

import os
import json
import aiohttp
import asyncio
import hashlib
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timedelta
from dataclasses import dataclass
import logging

from ..exceptions import DifyAPIException, ServiceException

logger = logging.getLogger(__name__)


@dataclass
class DifyConfig:
    """Dify配置类"""
    base_url: str = "https://api.dify.ai/v1"
    api_key: str = ""
    timeout: int = 60
    max_retries: int = 3
    retry_delay: float = 1.0
    
    def __post_init__(self):
        # 从环境变量获取配置
        self.api_key = os.getenv("DIFY_API_KEY", self.api_key)
        self.base_url = os.getenv("DIFY_BASE_URL", self.base_url)


@dataclass
class WorkflowResponse:
    """工作流响应数据类"""
    request_id: str
    status: str
    data: Dict[str, Any]
    raw_response: Dict[str, Any]
    execution_time: float
    tokens_used: int = 0
    
    @classmethod
    def from_response(cls, response_data: Dict[str, Any], execution_time: float):
        return cls(
            request_id=response_data.get("task_id", ""),
            status=response_data.get("status", "unknown"),
            data=response_data.get("data", {}),
            raw_response=response_data,
            execution_time=execution_time,
            tokens_used=response_data.get("metadata", {}).get("usage", {}).get("total_tokens", 0)
        )


class DifyRetryManager:
    """重试管理器"""
    
    def __init__(self, max_retries: int = 3, base_delay: float = 1.0):
        self.max_retries = max_retries
        self.base_delay = base_delay
    
    async def execute_with_retry(self, func, *args, **kwargs):
        """带重试机制执行函数"""
        last_exception = None
        
        for attempt in range(self.max_retries + 1):
            try:
                return await func(*args, **kwargs)
            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                last_exception = e
                if attempt < self.max_retries:
                    delay = self.base_delay * (2 ** attempt)  # 指数退避
                    logger.warning(f"Dify API调用失败，{delay}秒后重试 (第{attempt + 1}次): {str(e)}")
                    await asyncio.sleep(delay)
                else:
                    logger.error(f"Dify API调用失败，已达最大重试次数: {str(e)}")
            except Exception as e:
                # 对于非网络错误，不进行重试
                logger.error(f"Dify API调用发生非网络错误: {str(e)}")
                raise DifyAPIException(f"API调用失败: {str(e)}")
        
        raise DifyAPIException(f"API调用失败，已重试{self.max_retries}次: {str(last_exception)}")


class DifyClient:
    """Dify API客户端主类"""
    
    def __init__(self, config: DifyConfig = None):
        self.config = config or DifyConfig()
        self.retry_manager = DifyRetryManager(
            max_retries=self.config.max_retries,
            base_delay=self.config.retry_delay
        )
        self.session = None
        
    async def __aenter__(self):
        """异步上下文管理器入口"""
        await self._ensure_session()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        await self.close()
    
    async def _ensure_session(self):
        """确保HTTP会话存在"""
        if self.session is None or self.session.closed:
            timeout = aiohttp.ClientTimeout(total=self.config.timeout)
            self.session = aiohttp.ClientSession(
                timeout=timeout,
                headers={
                    "Authorization": f"Bearer {self.config.api_key}",
                    "Content-Type": "application/json",
                    "User-Agent": "AI-Sound/1.0"
                }
            )
    
    async def close(self):
        """关闭HTTP会话"""
        if self.session and not self.session.closed:
            await self.session.close()
    
    async def _make_request(
        self, 
        method: str, 
        endpoint: str, 
        data: Dict[str, Any] = None,
        files: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """发起HTTP请求"""
        await self._ensure_session()
        
        url = f"{self.config.base_url}/{endpoint.lstrip('/')}"
        
        try:
            if files:
                # 文件上传请求
                form_data = aiohttp.FormData()
                for key, value in (data or {}).items():
                    form_data.add_field(key, str(value))
                for key, file_data in files.items():
                    form_data.add_field(key, file_data)
                
                async with self.session.request(method, url, data=form_data) as response:
                    return await self._handle_response(response)
            else:
                # JSON请求
                async with self.session.request(method, url, json=data) as response:
                    return await self._handle_response(response)
                    
        except asyncio.TimeoutError:
            raise DifyAPIException(f"请求超时: {url}")
        except aiohttp.ClientError as e:
            raise DifyAPIException(f"网络请求失败: {str(e)}")
    
    async def _handle_response(self, response: aiohttp.ClientResponse) -> Dict[str, Any]:
        """处理HTTP响应"""
        try:
            response_data = await response.json()
        except Exception:
            response_data = {"error": "无法解析响应JSON", "status_code": response.status}
        
        if response.status >= 400:
            error_msg = response_data.get("message", f"HTTP {response.status}")
            raise DifyAPIException(f"API请求失败: {error_msg}")
        
        return response_data
    
    async def analyze_text(
        self, 
        text: str, 
        workflow_id: str,
        user_id: str = "ai-sound-user",
        additional_params: Dict[str, Any] = None
    ) -> WorkflowResponse:
        """调用文本分析工作流"""
        if not workflow_id:
            raise DifyAPIException("工作流ID不能为空")
        
        if not text or len(text.strip()) == 0:
            raise DifyAPIException("分析文本不能为空")
        
        # 构建请求数据
        request_data = {
            "inputs": {
                "text": text,
                **(additional_params or {})
            },
            "response_mode": "blocking",
            "user": user_id
        }
        
        start_time = datetime.utcnow()
        
        try:
            response_data = await self.retry_manager.execute_with_retry(
                self._make_request,
                "POST",
                f"workflows/{workflow_id}/run",
                data=request_data
            )
            
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            
            # 验证响应格式
            if "data" not in response_data:
                raise DifyAPIException("工作流响应格式错误：缺少data字段")
            
            workflow_response = WorkflowResponse.from_response(response_data, execution_time)
            
            logger.info(f"文本分析完成，耗时 {execution_time:.2f}秒，tokens: {workflow_response.tokens_used}")
            
            return workflow_response
            
        except Exception as e:
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            logger.error(f"文本分析失败，耗时 {execution_time:.2f}秒: {str(e)}")
            raise
    
    async def batch_analyze_texts(
        self,
        texts: List[str],
        workflow_id: str,
        user_id: str = "ai-sound-user",
        concurrent_limit: int = 3,
        progress_callback=None
    ) -> List[WorkflowResponse]:
        """批量文本分析"""
        if not texts:
            return []
        
        semaphore = asyncio.Semaphore(concurrent_limit)
        results = []
        completed = 0
        
        async def analyze_single(text: str, index: int) -> WorkflowResponse:
            async with semaphore:
                try:
                    result = await self.analyze_text(text, workflow_id, f"{user_id}_{index}")
                    nonlocal completed
                    completed += 1
                    
                    if progress_callback:
                        await progress_callback(completed, len(texts), f"完成第{index + 1}个文本分析")
                    
                    return result
                except Exception as e:
                    logger.error(f"文本 {index + 1} 分析失败: {str(e)}")
                    raise
        
        # 创建所有任务
        tasks = [analyze_single(text, i) for i, text in enumerate(texts)]
        
        # 等待所有任务完成
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 处理异常结果
        success_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"文本 {i + 1} 分析失败: {str(result)}")
                # 可以选择抛出异常或返回错误标记
                success_results.append(None)
            else:
                success_results.append(result)
        
        return success_results
    
    async def create_conversation(
        self,
        name: str = None,
        user_id: str = "ai-sound-user"
    ) -> Dict[str, Any]:
        """创建对话会话"""
        request_data = {
            "user": user_id
        }
        
        if name:
            request_data["name"] = name
        
        return await self.retry_manager.execute_with_retry(
            self._make_request,
            "POST",
            "chat-messages",
            data=request_data
        )
    
    async def send_message(
        self,
        conversation_id: str,
        message: str,
        user_id: str = "ai-sound-user",
        auto_generate_name: bool = True
    ) -> Dict[str, Any]:
        """发送对话消息"""
        request_data = {
            "inputs": {},
            "query": message,
            "response_mode": "blocking",
            "conversation_id": conversation_id,
            "user": user_id,
            "auto_generate_name": auto_generate_name
        }
        
        return await self.retry_manager.execute_with_retry(
            self._make_request,
            "POST",
            "chat-messages",
            data=request_data
        )
    
    async def get_conversation_history(
        self,
        conversation_id: str,
        user_id: str = "ai-sound-user"
    ) -> Dict[str, Any]:
        """获取对话历史"""
        return await self.retry_manager.execute_with_retry(
            self._make_request,
            "GET",
            f"messages?conversation_id={conversation_id}&user={user_id}"
        )
    
    async def upload_file(
        self,
        file_content: bytes,
        filename: str,
        user_id: str = "ai-sound-user"
    ) -> Dict[str, Any]:
        """上传文件"""
        files = {
            "file": (filename, file_content)
        }
        
        data = {
            "user": user_id
        }
        
        return await self.retry_manager.execute_with_retry(
            self._make_request,
            "POST",
            "files/upload",
            data=data,
            files=files
        )
    
    async def get_workflows(self) -> List[Dict[str, Any]]:
        """获取可用工作流列表"""
        try:
            response = await self.retry_manager.execute_with_retry(
                self._make_request,
                "GET",
                "workflows"
            )
            return response.get("data", [])
        except Exception as e:
            logger.error(f"获取工作流列表失败: {str(e)}")
            return []
    
    async def health_check(self) -> bool:
        """健康检查"""
        try:
            await self.retry_manager.execute_with_retry(
                self._make_request,
                "GET",
                "workflows"
            )
            return True
        except Exception as e:
            logger.error(f"Dify健康检查失败: {str(e)}")
            return False
    
    def create_text_hash(self, text: str) -> str:
        """创建文本哈希值，用于缓存"""
        return hashlib.md5(text.encode('utf-8')).hexdigest()


# 全局Dify客户端实例
_global_dify_client = None

async def get_dify_client() -> DifyClient:
    """获取全局Dify客户端实例"""
    global _global_dify_client
    if _global_dify_client is None:
        _global_dify_client = DifyClient()
    return _global_dify_client

async def close_dify_client():
    """关闭全局Dify客户端"""
    global _global_dify_client
    if _global_dify_client:
        await _global_dify_client.close()
        _global_dify_client = None


# 工厂函数和便利方法
class DifyClientFactory:
    """Dify客户端工厂类"""
    
    @staticmethod
    def create_client(
        api_key: str = None,
        base_url: str = None,
        timeout: int = 60,
        max_retries: int = 3
    ) -> DifyClient:
        """创建Dify客户端实例"""
        config = DifyConfig(
            api_key=api_key or os.getenv("DIFY_API_KEY", ""),
            base_url=base_url or os.getenv("DIFY_BASE_URL", "https://api.dify.ai/v1"),
            timeout=timeout,
            max_retries=max_retries
        )
        
        if not config.api_key:
            raise DifyAPIException("Dify API密钥未配置，请设置DIFY_API_KEY环境变量")
        
        return DifyClient(config)
    
    @staticmethod
    async def test_connection(api_key: str = None, base_url: str = None) -> bool:
        """测试Dify连接"""
        try:
            client = DifyClientFactory.create_client(api_key, base_url)
            async with client:
                return await client.health_check()
        except Exception as e:
            logger.error(f"Dify连接测试失败: {str(e)}")
            return False 