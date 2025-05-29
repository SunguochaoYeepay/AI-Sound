#!/usr/bin/env python3
"""
重新初始化数据库数据
"""

import asyncio
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from src.core.database import init_test_data, db_manager

async def main():
    """主函数"""
    try:
        print("🔄 开始重新初始化数据库数据...")
        
        # 连接数据库
        await db_manager.connect()
        print("✅ 数据库连接成功")
        
        # 重新初始化测试数据
        await init_test_data()
        print("✅ 测试数据初始化完成")
        
        # 断开数据库连接
        await db_manager.disconnect()
        print("✅ 数据库连接已断开")
        
        print("🎉 数据库数据重新初始化完成！")
        
    except Exception as e:
        print(f"❌ 初始化失败: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code) 