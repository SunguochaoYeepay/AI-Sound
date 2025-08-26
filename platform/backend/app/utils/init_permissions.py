#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
权限系统初始化脚本
"""

import sys
import os
import logging
from sqlalchemy.orm import Session

# 添加项目根目录到路径
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(os.path.dirname(current_dir))
sys.path.append(backend_dir)

from app.database import SessionLocal
from app.models.auth import User, Role, Permission, UserStatus, user_roles
from app.core.auth import auth_manager

# 获取日志记录器
logger = logging.getLogger(__name__)

def init_auth_system():
    """初始化完整的权限系统"""
    logger.info("🚀 开始初始化权限系统...")
    
    db = SessionLocal()
    try:
        # 1. 创建基础权限
        permissions_data = [
            {"code": "user.view", "name": "查看用户", "description": "查看用户列表", "module": "user"},
            {"code": "user.create", "name": "创建用户", "description": "创建新用户", "module": "user"},
            {"code": "tts.basic", "name": "基础TTS", "description": "使用基础TTS", "module": "tts"},
            {"code": "project.view", "name": "查看项目", "description": "查看项目", "module": "project"},
            {"code": "system.logs", "name": "查看日志", "description": "查看系统日志", "module": "system"},
        ]
        
        # 创建权限
        for perm_data in permissions_data:
            permission = db.query(Permission).filter(Permission.code == perm_data["code"]).first()
            if not permission:
                permission = Permission(**perm_data)
                db.add(permission)
                logger.info(f"  ✅ 创建权限: {perm_data['code']}")
        
        db.commit()
        
        # 2. 创建角色
        roles_data = [
            {"name": "admin", "display_name": "管理员", "description": "系统管理员", "is_system": True},
            {"name": "user", "display_name": "普通用户", "description": "标准用户", "is_system": True},
        ]
        
        for role_data in roles_data:
            role = db.query(Role).filter(Role.name == role_data["name"]).first()
            if not role:
                role = Role(**role_data)
                db.add(role)
                logger.info(f"  ✅ 创建角色: {role_data['name']}")
        
        db.commit()
        
        # 3. 创建管理员用户
        admin_user = db.query(User).filter(User.username == "admin").first()
        if not admin_user:
            admin_password = "admin123456"
            hashed_password = auth_manager.get_password_hash(admin_password)
            
            admin_user = User(
                username="admin",
                email="admin@ai-sound.local",
                hashed_password=hashed_password,
                full_name="系统管理员",
                status=UserStatus.ACTIVE,
                is_verified=True,
                is_superuser=True,
                daily_quota=10000
            )
            
            db.add(admin_user)
            db.flush()
            
            # 分配管理员角色
            admin_role = db.query(Role).filter(Role.name == "admin").first()
            if admin_role:
                admin_user.roles.append(admin_role)
            
            db.commit()
            logger.info(f"  ✅ 创建管理员: admin / {admin_password}")
        
        logger.info("🎉 权限系统初始化完成！")
        
    except Exception as e:
        db.rollback()
        logger.error(f"❌ 初始化失败: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    init_auth_system()