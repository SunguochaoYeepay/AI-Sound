#!/usr/bin/env python3
"""
检查引擎的is_enabled字段
"""

import asyncio
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from src.core.database import db_manager

async def main():
    try:
        print("检查引擎的is_enabled字段...")
        
        # 连接数据库
        await db_manager.connect()
        
        db = db_manager.get_database()
        engines_collection = db["engines"]
        
        # 查看所有引擎详细信息
        engines = await engines_collection.find({}).to_list(length=None)
        print(f"找到 {len(engines)} 个引擎:")
        
        for engine in engines:
            print(f"引擎ID: {engine.get('id')}")
            print(f"  名称: {engine.get('name')}")
            print(f"  类型: {engine.get('type')}")
            print(f"  状态: {engine.get('status')}")
            print(f"  是否启用: {engine.get('is_enabled')}")
        
        # 断开数据库连接
        await db_manager.disconnect()
        
    except Exception as e:
        print(f"检查失败: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code) 