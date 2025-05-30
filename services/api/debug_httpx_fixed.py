#!/usr/bin/env python3
"""
httpx修复配置测试脚本
"""

import asyncio
import httpx

async def test_fixed_httpx():
    """测试修复后的httpx配置"""
    print("=== 修复后的httpx配置测试 ===")
    
    urls = [
        "http://127.0.0.1:7929/health",
        "http://127.0.0.1:9001/health"
    ]
    
    for url in urls:
        try:
            print(f"\n测试URL: {url}")
            
            headers = {
                "Accept": "application/json",
                "User-Agent": "python-httpx/0.24.0"
            }
            
            async with httpx.AsyncClient(
                timeout=httpx.Timeout(30.0),
                headers=headers,
                http2=False,  # 禁用HTTP/2
                limits=httpx.Limits(max_keepalive_connections=0),  # 禁用连接池
                verify=False  # 禁用SSL验证
            ) as client:
                response = await client.get(url)
                
                print(f"状态码: {response.status_code}")
                print(f"响应内容: {response.text}")
                
        except Exception as e:
            print(f"❌ 请求失败: {e}")

if __name__ == "__main__":
    asyncio.run(test_fixed_httpx()) 