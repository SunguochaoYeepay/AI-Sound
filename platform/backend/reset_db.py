#!/usr/bin/env python
"""
数据库重置脚本
"""

import sys
import os

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import db_manager

def main():
    print("🔄 开始重置数据库...")
    
    try:
        # 重置数据库表结构
        db_manager.reset_db()
        print("✅ 数据库表结构重置完成!")
        
        # 检查连接
        if db_manager.check_connection():
            print("✅ 数据库连接正常")
        else:
            print("❌ 数据库连接失败")
            
        print("🎉 数据库重置操作完成!")
        
    except Exception as e:
        print(f"❌ 数据库重置失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()