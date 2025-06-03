"""
检查当前引擎配置
"""
import asyncio
import sys
import os

# 添加项目路径
sys.path.insert(0, 'src')

from src.core.database import db_manager

async def check_engines():
    try:
        await db_manager.connect()
        db = db_manager.get_database()
        engines_collection = db['engines']
        
        engines = []
        async for engine in engines_collection.find({}):
            engines.append(engine)
            
        print(f"数据库中的引擎 ({len(engines)} 个):")
        for engine in engines:
            print(f"- ID: {engine.get('id')}")
            print(f"  Name: {engine.get('name')}")
            print(f"  Type: {engine.get('type')}")
            print(f"  Status: {engine.get('status')}")
            print()
            
    except Exception as e:
        print(f"错误: {e}")
    finally:
        await db_manager.disconnect()

if __name__ == "__main__":
    asyncio.run(check_engines()) 