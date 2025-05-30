#!/usr/bin/env python3
"""
调试声音预览问题
"""

import asyncio
import sys
import os

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

async def debug_preview():
    """调试声音预览问题"""
    print("=== 调试声音预览问题 ===")
    
    # 测试问题声音ID
    voice_id = "voice_1748592890_a94c2c9a"
    
    print(f"1. 测试声音ID: {voice_id}")
    
    # 模拟voice_service查找过程
    from core.database import db_manager
    
    try:
        # 连接数据库
        await db_manager.connect()
        db = db_manager.get_database()
        voices_collection = db["voices"]
        
        # 查找声音
        voice_doc = await voices_collection.find_one({"id": voice_id})
        if voice_doc:
            print(f"2. 找到声音数据:")
            print(f"   - ID: {voice_doc.get('id')}")
            print(f"   - Name: {voice_doc.get('name')}")
            print(f"   - Engine ID: {voice_doc.get('engine_id')}")
            print(f"   - Engine Voice ID: {voice_doc.get('engine_voice_id')}")
            
            # 测试适配器查找
            engine_id = voice_doc.get('engine_id')
            print(f"3. 查找适配器: {engine_id}")
            
            from adapters.factory import AdapterFactory
            from core.dependencies import dependency_manager
            
            # 模拟依赖管理器状态
            await dependency_manager.initialize()
            adapter_factory = dependency_manager.adapter_factory
            
            adapter = await adapter_factory.get_adapter(engine_id)
            if adapter:
                print(f"   ✅ 找到适配器: {adapter.__class__.__name__}")
                print(f"   - 状态: {adapter.status}")
                print(f"   - 配置: {adapter.config}")
            else:
                print(f"   ❌ 未找到适配器: {engine_id}")
                
                # 显示所有注册的适配器
                stats = adapter_factory.get_adapter_stats()
                print(f"   已注册的适配器:")
                for adapter_info in stats.get('adapters', []):
                    print(f"     - {adapter_info['engine_id']}: {adapter_info['status']}")
        else:
            print(f"2. ❌ 未找到声音数据: {voice_id}")
            
            # 列出所有声音
            print("所有声音数据:")
            async for doc in voices_collection.find().limit(5):
                print(f"  - {doc.get('id')}: {doc.get('name')} -> {doc.get('engine_id')}")
        
    except Exception as e:
        print(f"❌ 调试失败: {e}")
    finally:
        await db_manager.disconnect()

if __name__ == "__main__":
    asyncio.run(debug_preview()) 