#!/usr/bin/env python3
"""
检查声音数据库中的数据
"""

import asyncio
import motor.motor_asyncio

async def check_voices():
    """检查数据库中的声音数据"""
    client = motor.motor_asyncio.AsyncMotorClient('mongodb://localhost:27017')
    db = client['ai_sound']
    collection = db['voices']
    
    print("=== 数据库中的声音数据 ===")
    count = 0
    async for doc in collection.find().limit(10):
        count += 1
        print(f"声音 {count}:")
        print(f"  ID: {doc.get('id', 'N/A')}")
        print(f"  Engine ID: {doc.get('engine_id', 'N/A')}")
        print(f"  Engine Voice ID: {doc.get('engine_voice_id', 'N/A')}")
        print(f"  Name: {doc.get('name', 'N/A')}")
        print(f"  Display Name: {doc.get('display_name', 'N/A')}")
        print("---")
    
    if count == 0:
        print("❌ 没有找到声音数据")
    else:
        print(f"✅ 找到 {count} 条声音数据")

async def check_adapters():
    """检查适配器注册情况"""
    print("\n=== 检查适配器注册情况 ===")
    import sys
    import os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
    
    from adapters.factory import AdapterFactory
    
    # 模拟依赖注入中的适配器工厂
    factory = AdapterFactory()
    
    # 假设适配器已注册（实际需要从依赖容器获取）
    print("需要检查依赖容器中的适配器注册情况...")

if __name__ == "__main__":
    asyncio.run(check_voices())
    asyncio.run(check_adapters()) 