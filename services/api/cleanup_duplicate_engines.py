"""
清理重复的MegaTTS3引擎配置
"""
import asyncio
import sys
import os

# 添加项目路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(project_root, 'services', 'api', 'src'))

from src.core.database import db_manager

async def cleanup_duplicate_engines():
    try:
        # 连接数据库
        await db_manager.connect()
        db = db_manager.get_database()
        engines_collection = db['engines']
        
        # 查找所有引擎
        engines = []
        async for engine in engines_collection.find({}):
            engines.append(engine)
            
        print(f"发现 {len(engines)} 个引擎:")
        
        for engine in engines:
            print(f"- ID: {engine.get('id')}, Name: {engine.get('name')}, Type: {engine.get('type')}")
        
        # 删除重复的 megatts3_001
        result = await engines_collection.delete_many({"id": "megatts3_001"})
        print(f"\n删除了 {result.deleted_count} 个重复的 megatts3_001 引擎")
        
        # 确保只保留一个 MegaTTS3 引擎
        remaining_engines = []
        async for engine in engines_collection.find({}):
            remaining_engines.append(engine)
            
        print(f"\n清理后剩余 {len(remaining_engines)} 个引擎:")
        for engine in remaining_engines:
            print(f"- ID: {engine.get('id')}, Name: {engine.get('name')}, Type: {engine.get('type')}")
            
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await db_manager.disconnect()

if __name__ == "__main__":
    asyncio.run(cleanup_duplicate_engines()) 