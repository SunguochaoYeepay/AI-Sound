#!/usr/bin/env python3
"""
创建兼容当前数据库结构的测试用户脚本
"""

import sys
import os

# 添加项目路径到sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def create_test_user():
    """创建兼容当前数据库结构的测试用户"""
    try:
        from app.database import SessionLocal
        from app.core.auth import auth_manager
        from sqlalchemy import text
        
        db = SessionLocal()
        
        # 检查用户是否已存在
        check_query = text("SELECT id, username FROM users WHERE username = :username")
        existing = db.execute(check_query, {"username": "admin"}).fetchone()
        
        if existing:
            print("✅ 测试用户'admin'已存在")
            print(f"用户ID: {existing[0]}")
            print(f"用户名: {existing[1]}")
            return existing
        
        # 创建新用户
        password_hash = auth_manager.get_password_hash("admin123")
        
        insert_query = text("""
            INSERT INTO users (username, email, password_hash, is_active, is_admin, created_at, updated_at)
            VALUES (:username, :email, :password_hash, :is_active, :is_admin, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            RETURNING id, username
        """)
        
        result = db.execute(insert_query, {
            "username": "admin",
            "email": "admin@ai-sound.com",
            "password_hash": password_hash,
            "is_active": True,
            "is_admin": True
        })
        
        user = result.fetchone()
        db.commit()
        
        print("✅ 测试用户创建成功！")
        print(f"用户名: admin")
        print(f"密码: admin123")
        print(f"邮箱: admin@ai-sound.com")
        print(f"用户ID: {user[0]}")
        
        return user
        
    except Exception as e:
        print(f"❌ 创建测试用户失败: {e}")
        import traceback
        traceback.print_exc()
        if 'db' in locals():
            db.rollback()
        return None
    finally:
        if 'db' in locals():
            db.close()

if __name__ == "__main__":
    print("🚀 开始创建兼容的测试用户...")
    create_test_user() 