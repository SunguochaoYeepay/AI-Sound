#!/usr/bin/env python3
"""
测试数据库连接
"""

import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient

async def test_db_connection():
    # 从环境变量获取配置
    db_host = os.getenv('DB_HOST', 'localhost')
    db_port = int(os.getenv('DB_PORT', '27017'))
    db_database = os.getenv('DB_DATABASE', 'ai_sound')
    db_username = os.getenv('DB_USERNAME')
    db_password = os.getenv('DB_PASSWORD')
    
    print(f"数据库配置:")
    print(f"  主机: {db_host}")
    print(f"  端口: {db_port}")
    print(f"  数据库: {db_database}")
    print(f"  用户名: {db_username}")
    print(f"  密码: {'*' * len(db_password) if db_password else None}")
    
    # 构建连接URL
    if db_username and db_password:
        url = f"mongodb://{db_username}:{db_password}@{db_host}:{db_port}/{db_database}?authSource=admin"
    else:
        url = f"mongodb://{db_host}:{db_port}/{db_database}"
    
    print(f"\n连接URL: {url}")
    
    try:
        client = AsyncIOMotorClient(url)
        await client.admin.command('ping')
        print("✅ 数据库连接成功!")
        
        # 测试数据库操作
        db = client[db_database]
        collection = db.test_collection
        
        # 插入测试文档
        result = await collection.insert_one({"test": "data", "timestamp": "2023-12-01"})
        print(f"✅ 插入文档成功: {result.inserted_id}")
        
        # 查询测试文档
        doc = await collection.find_one({"test": "data"})
        print(f"✅ 查询文档成功: {doc}")
        
        # 删除测试文档
        await collection.delete_one({"_id": result.inserted_id})
        print("✅ 删除文档成功")
        
        client.close()
        
    except Exception as e:
        print(f"❌ 数据库连接失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_db_connection())