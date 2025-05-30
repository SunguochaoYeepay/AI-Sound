#!/usr/bin/env python3
"""
测试urllib异步客户端
"""

import asyncio
import sys
import os

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from adapters.urllib_async import AsyncUrllibClient

async def test_urllib_client():
    """测试urllib异步客户端"""
    print("=== urllib异步客户端测试 ===")
    
    urls = [
        "http://127.0.0.1:7929/health",
        "http://127.0.0.1:9001/health"
    ]
    
    headers = {
        "Accept": "application/json",
        "User-Agent": "python-urllib/3.11"
    }
    
    client = AsyncUrllibClient(timeout=30.0, headers=headers)
    
    try:
        for url in urls:
            print(f"\n测试URL: {url}")
            
            try:
                response = await client.get(url)
                response.raise_for_status()
                
                print(f"状态码: {response.status_code}")
                print(f"响应内容: {response.text}")
                
            except Exception as e:
                print(f"❌ 请求失败: {e}")
    
    finally:
        await client.aclose()
    
    print("\n✅ urllib客户端测试完成")

if __name__ == "__main__":
    asyncio.run(test_urllib_client()) 