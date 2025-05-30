#!/usr/bin/env python3
"""
清理xiaoxiao测试数据的脚本
用于移除自动插入的测试数据，保持数据库干净
"""

import asyncio
import sys
import os

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.core.database import cleanup_test_data, db_manager
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    """主函数"""
    try:
        print("🧹 开始清理xiaoxiao等测试数据...")
        print("   这将删除自动插入的测试声音、引擎和角色数据")
        print("   你手动添加的数据不会被影响")
        print("")
        
        # 连接数据库
        await db_manager.connect()
        
        # 清理测试数据
        await cleanup_test_data()
        
        print("")
        print("✅ 测试数据清理完成！")
        print("   现在数据库中只保留你真正添加的数据")
        print("   重启应用后不会再自动出现xiaoxiao等测试数据")
        
    except Exception as e:
        print(f"❌ 清理失败: {e}")
        logger.error(f"清理测试数据失败: {e}")
    finally:
        await db_manager.disconnect()

if __name__ == "__main__":
    asyncio.run(main()) 