#!/usr/bin/env python3
"""
基于urllib的异步HTTP客户端包装器
解决httpx兼容性问题
"""

import asyncio
import urllib.request
import urllib.error
import urllib.parse
import json
from typing import Dict, Any, Optional

class AsyncUrllibClient:
    """异步urllib客户端包装器"""
    
    def __init__(self, timeout: float = 30.0, headers: Optional[Dict[str, str]] = None):
        self.timeout = timeout
        self.default_headers = headers or {}
    
    async def get(self, url: str, headers: Optional[Dict[str, str]] = None) -> 'AsyncResponse':
        """异步GET请求"""
        return await self._request('GET', url, headers=headers)
    
    async def post(self, url: str, json_data: Optional[Dict[str, Any]] = None, 
                   headers: Optional[Dict[str, str]] = None) -> 'AsyncResponse':
        """异步POST请求"""
        data = None
        if json_data:
            data = json.dumps(json_data).encode('utf-8')
            if headers is None:
                headers = {}
            headers['Content-Type'] = 'application/json'
        
        return await self._request('POST', url, data=data, headers=headers)
    
    async def _request(self, method: str, url: str, data: Optional[bytes] = None, 
                      headers: Optional[Dict[str, str]] = None) -> 'AsyncResponse':
        """执行HTTP请求"""
        loop = asyncio.get_event_loop()
        
        # 在线程池中执行同步请求
        response = await loop.run_in_executor(
            None, self._sync_request, method, url, data, headers
        )
        
        return response
    
    def _sync_request(self, method: str, url: str, data: Optional[bytes] = None, 
                     headers: Optional[Dict[str, str]] = None) -> 'AsyncResponse':
        """同步HTTP请求"""
        try:
            # 合并请求头
            request_headers = self.default_headers.copy()
            if headers:
                request_headers.update(headers)
            
            # 创建请求
            request = urllib.request.Request(url, data=data, method=method)
            for key, value in request_headers.items():
                request.add_header(key, value)
            
            # 发送请求
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                status_code = response.status
                content = response.read()
                response_headers = dict(response.headers)
                
                return AsyncResponse(status_code, content, response_headers)
                
        except urllib.error.HTTPError as e:
            # HTTP错误（如404, 500等）
            content = e.read() if hasattr(e, 'read') else b''
            headers = dict(e.headers) if hasattr(e, 'headers') else {}
            return AsyncResponse(e.code, content, headers)
            
        except Exception as e:
            # 其他错误（连接超时等）
            raise ConnectionError(f"请求失败: {e}")
    
    async def aclose(self):
        """关闭客户端（兼容性方法）"""
        pass

class AsyncResponse:
    """异步响应包装器"""
    
    def __init__(self, status_code: int, content: bytes, headers: Dict[str, str]):
        self.status_code = status_code
        self.content = content
        self.headers = headers
        self._text = None
        self._json_data = None
    
    @property
    def text(self) -> str:
        """获取文本内容"""
        if self._text is None:
            self._text = self.content.decode('utf-8')
        return self._text
    
    def json(self) -> Dict[str, Any]:
        """解析JSON内容"""
        if self._json_data is None:
            self._json_data = json.loads(self.text)
        return self._json_data
    
    def raise_for_status(self):
        """检查HTTP状态码"""
        if self.status_code >= 400:
            raise urllib.error.HTTPError(
                url=None, code=self.status_code, 
                msg=f"HTTP {self.status_code}", 
                hdrs=self.headers, fp=None
            ) 