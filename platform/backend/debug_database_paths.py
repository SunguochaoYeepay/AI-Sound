#!/usr/bin/env python3
"""
调试数据库路径和连接问题
"""
import sys
import os
import sqlite3
sys.path.append('app')

def debug_database_paths():
    print("🔍 === 调试数据库路径配置 ===")
    
    # 1. 检查当前工作目录
    print(f"📁 当前工作目录: {os.getcwd()}")
    
    # 2. 检查SQLAlchemy配置
    try:
        from database import DATABASE_PATH, DATABASE_URL, DATABASE_DIR
        print(f"📋 SQLAlchemy配置:")
        print(f"  DATABASE_DIR: {DATABASE_DIR}")
        print(f"  DATABASE_PATH: {DATABASE_PATH}")
        print(f"  DATABASE_URL: {DATABASE_URL}")
        print(f"  绝对路径: {os.path.abspath(DATABASE_PATH)}")
        print(f"  文件存在: {os.path.exists(DATABASE_PATH)}")
        
        if os.path.exists(DATABASE_PATH):
            print(f"  文件大小: {os.path.getsize(DATABASE_PATH)} 字节")
            print(f"  最后修改: {os.path.getmtime(DATABASE_PATH)}")
    except Exception as e:
        print(f"❌ SQLAlchemy配置错误: {e}")
    
    # 3. 检查直接路径
    direct_paths = [
        "data/database.db",
        "../data/database.db", 
        "./data/database.db",
        "platform/backend/data/database.db"
    ]
    
    print(f"\n📋 检查可能的数据库路径:")
    for path in direct_paths:
        exists = os.path.exists(path)
        print(f"  {path}: {'✅' if exists else '❌'}")
        if exists:
            print(f"    文件大小: {os.path.getsize(path)} 字节")
    
    # 4. 测试SQLAlchemy连接
    print(f"\n🔌 测试SQLAlchemy连接:")
    try:
        from database import get_db
        from models import NovelProject
        
        db = next(get_db())
        print(f"✅ SQLAlchemy连接成功")
        
        # 查询项目数量
        count = db.query(NovelProject).count()
        print(f"📊 SQLAlchemy查询项目数: {count}")
        
        # 查询最新项目
        latest = db.query(NovelProject).order_by(NovelProject.id.desc()).first()
        if latest:
            print(f"📋 最新项目: ID={latest.id}, 名称={latest.name}")
        else:
            print(f"📋 没有找到任何项目")
            
        db.close()
        
    except Exception as e:
        print(f"❌ SQLAlchemy连接失败: {e}")
        import traceback
        traceback.print_exc()
    
    # 5. 测试直接sqlite3连接
    print(f"\n🔌 测试直接sqlite3连接:")
    for path in direct_paths:
        if os.path.exists(path):
            try:
                conn = sqlite3.connect(path)
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM novel_projects")
                count = cursor.fetchone()[0]
                print(f"✅ {path}: 项目数={count}")
                
                cursor.execute("SELECT id, name FROM novel_projects ORDER BY id DESC LIMIT 1")
                latest = cursor.fetchone()
                if latest:
                    print(f"   最新: ID={latest[0]}, 名称={latest[1]}")
                    
                conn.close()
                
            except Exception as e:
                print(f"❌ {path}: {e}")

if __name__ == "__main__":
    debug_database_paths() 