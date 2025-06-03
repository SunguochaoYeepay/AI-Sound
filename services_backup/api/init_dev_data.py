#!/usr/bin/env python3
"""
开发环境测试数据初始化脚本
仅在开发环境中使用，用于快速创建测试数据
"""

import asyncio
import sys
import os

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.core.database import init_test_data_manual, db_manager
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    """主函数"""
    try:
        print("🔧 开发环境测试数据初始化")
        print("   这将创建xiaoxiao等测试数据，仅用于开发测试")
        print("   生产环境请不要运行此脚本！")
        print("")
        
        # 确认操作
        confirm = input("确认要初始化测试数据吗？(y/N): ").strip().lower()
        if confirm not in ['y', 'yes']:
            print("取消操作")
            return
        
        # 连接数据库
        await db_manager.connect()
        
        # 初始化测试数据
        await init_test_data_manual()
        
        print("")
        print("✅ 开发测试数据初始化完成！")
        print("   已创建：")
        print("   - MegaTTS3 测试引擎")
        print("   - xiaoxiao 测试声音")
        print("   - 智能小助手 测试角色")
        
    except Exception as e:
        print(f"❌ 初始化失败: {e}")
        logger.error(f"初始化测试数据失败: {e}")
    finally:
        await db_manager.disconnect()

if __name__ == "__main__":
    asyncio.run(main()) 