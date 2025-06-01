"""
删除重复的MegaTTS3引擎，只保留第一个
"""
import asyncio
import sys
import os

# 添加项目路径
sys.path.insert(0, 'src')

from src.core.database import db_manager

async def remove_duplicate_megatts():
    try:
        await db_manager.connect()
        db = db_manager.get_database()
        engines_collection = db['engines']
        
        # 查找所有MegaTTS3引擎
        engines = []
        async for engine in engines_collection.find({"type": "megatts3"}):
            engines.append(engine)
            
        print(f"发现 {len(engines)} 个MegaTTS3引擎:")
        for i, engine in enumerate(engines):
            print(f"{i+1}. ID: {engine.get('id')}, Name: {engine.get('name')}")
            
        if len(engines) > 1:
            # 保留第一个，删除其他的
            keep_engine = engines[0]
            delete_engines = engines[1:]
            
            print(f"\n保留: {keep_engine.get('id')} - {keep_engine.get('name')}")
            print(f"删除 {len(delete_engines)} 个重复引擎:")
            
            for engine in delete_engines:
                print(f"- 删除: {engine.get('id')} - {engine.get('name')}")
                result = await engines_collection.delete_one({"_id": engine["_id"]})
                print(f"  删除结果: {result.deleted_count} 个文档")
            
            print("\n✓ 清理完成!")
        else:
            print("只有1个MegaTTS3引擎，无需删除")
            
        # 验证最终结果
        final_engines = []
        async for engine in engines_collection.find({}):
            final_engines.append(engine)
            
        print(f"\n最终引擎列表 ({len(final_engines)} 个):")
        for engine in final_engines:
            print(f"- {engine.get('name')} ({engine.get('type')})")
            
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await db_manager.disconnect()

if __name__ == "__main__":
    asyncio.run(remove_duplicate_megatts()) 