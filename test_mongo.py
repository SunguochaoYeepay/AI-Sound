#!/usr/bin/env python3
"""
测试MongoDB连接
"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

async def test_connection():
    # 测试不同的连接字符串
    urls = [
        "mongodb://admin:admin123@localhost:27017/ai_sound?authSource=admin",
        "mongodb://admin:admin123@localhost:27017/ai_sound",
        "mongodb://localhost:27017/ai_sound"
    ]
    
    for url in urls:
        print(f"测试连接: {url}")
        try:
            client = AsyncIOMotorClient(url)
            await client.admin.command('ping')
            print("✅ 连接成功!")
            client.close()
            break
        except Exception as e:
            print(f"❌ 连接失败: {e}")
    
if __name__ == "__main__":
    asyncio.run(test_connection())