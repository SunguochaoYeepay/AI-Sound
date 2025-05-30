#!/usr/bin/env python3
"""
测试所有修复后的适配器
"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from adapters.urllib_async import AsyncUrllibClient

async def test_all_adapters():
    """测试所有适配器连接"""
    print("=== 测试所有适配器连接 ===")
    
    endpoints = {
        'MegaTTS3': 'http://127.0.0.1:7929/health',
        'ESPnet': 'http://127.0.0.1:9001/health'
    }
    
    client = AsyncUrllibClient(
        timeout=30.0, 
        headers={'Accept': 'application/json', 'User-Agent': 'python-urllib/3.11'}
    )
    
    try:
        for name, url in endpoints.items():
            try:
                print(f"\n测试 {name}...")
                response = await client.get(url)
                response.raise_for_status()
                print(f"✅ {name}: {response.status_code} - 连接成功")
                print(f"响应: {response.text[:100]}...")
            except Exception as e:
                print(f"❌ {name}: {e}")
    finally:
        await client.aclose()
    
    print("\n🎉 所有适配器测试完成!")

if __name__ == "__main__":
    asyncio.run(test_all_adapters()) 