#!/usr/bin/env python3
"""
调试密码验证脚本
"""

import sys
import os

# 添加项目路径到sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def debug_password():
    """调试密码验证逻辑"""
    try:
        from app.database import SessionLocal
        from app.core.auth import auth_manager
        from sqlalchemy import text
        
        db = SessionLocal()
        
        # 查询admin用户信息
        user_query = text("SELECT id, username, email, password_hash, is_active FROM users WHERE username = :username")
        result = db.execute(user_query, {"username": "admin"}).fetchone()
        
        if not result:
            print("❌ 用户'admin'不存在")
            return
            
        user_id, username, email, password_hash, is_active = result
        
        print("👤 用户信息:")
        print(f"  ID: {user_id}")
        print(f"  用户名: {username}")
        print(f"  邮箱: {email}")
        print(f"  激活状态: {is_active}")
        print(f"  密码哈希: {password_hash[:50]}...")
        
        # 测试密码验证
        test_password = "admin123"
        print(f"\n🔐 测试密码验证: '{test_password}'")
        
        # 生成新的密码哈希用于对比
        new_hash = auth_manager.get_password_hash(test_password)
        print(f"新生成的哈希: {new_hash[:50]}...")
        
        # 验证密码
        is_valid = auth_manager.verify_password(test_password, password_hash)
        print(f"密码验证结果: {is_valid}")
        
        if not is_valid:
            print("\n🔧 重新设置密码...")
            # 更新密码
            update_query = text("""
                UPDATE users 
                SET password_hash = :password_hash, updated_at = CURRENT_TIMESTAMP 
                WHERE username = :username
            """)
            db.execute(update_query, {
                "username": "admin",
                "password_hash": new_hash
            })
            db.commit()
            print("✅ 密码已重新设置")
            
            # 再次验证
            verify_again = auth_manager.verify_password(test_password, new_hash)
            print(f"新密码验证结果: {verify_again}")
        
        db.close()
        
    except Exception as e:
        print(f"❌ 调试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🚀 开始密码调试...")
    debug_password() 