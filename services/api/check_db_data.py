#!/usr/bin/env python3
"""
检查数据库数据
"""

import asyncio
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from src.core.database import db_manager

async def main():
    """主函数"""
    try:
        print("🔍 检查数据库数据...")
        
        # 连接数据库
        await db_manager.connect()
        print("✅ 数据库连接成功")
        
        db = db_manager.get_database()
        
        # 检查引擎数据
        print("\n📊 引擎数据:")
        engines_collection = db["engines"]
        engines = await engines_collection.find({}).to_list(length=None)
        print(f"总数: {len(engines)}")
        for engine in engines:
            print(f"  - ID: {engine.get('id')}, 名称: {engine.get('name')}, 状态: {engine.get('status')}")
        
        # 检查声音数据
        print("\n🎤 声音数据:")
        voices_collection = db["voices"]
        voices = await voices_collection.find({}).to_list(length=None)
        print(f"总数: {len(voices)}")
        for voice in voices:
            print(f"  - ID: {voice.get('id')}, 名称: {voice.get('name')}, 风格: {voice.get('style')}")
        
        # 检查角色数据
        print("\n👤 角色数据:")
        characters_collection = db["characters"]
        characters = await characters_collection.find({}).to_list(length=None)
        print(f"总数: {len(characters)}")
        for character in characters:
            print(f"  - ID: {character.get('id')}, 名称: {character.get('name')}, 显示名: {character.get('display_name')}")
        
        # 断开数据库连接
        await db_manager.disconnect()
        print("\n✅ 数据库连接已断开")
        
    except Exception as e:
        print(f"❌ 检查失败: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code) 