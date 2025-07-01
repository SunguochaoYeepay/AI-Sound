#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
认证相关的API路由
"""

from datetime import timedelta
from typing import Any
import logging
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm, HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, text

from ...database import get_db
# 临时使用原始SQL而不是新的认证模型，因为数据库表结构不匹配
# from ...models.auth import User, Role, Permission, UserSession, LoginLog, UserStatus
from ...core.auth import auth_manager

# 配置日志
logger = logging.getLogger(__name__)

router = APIRouter(tags=["认证"])

# HTTPBearer认证
security = HTTPBearer()

# ==================== 辅助函数 ====================

async def get_current_user_from_token(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> int:
    """临时的简化用户认证函数，返回用户ID而不是完整User对象"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="认证失败",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    # 验证令牌
    payload = auth_manager.verify_token(credentials.credentials)
    if payload is None:
        raise credentials_exception
    
    # 检查令牌类型
    if payload.get("type") != "access":
        raise credentials_exception
    
    # 获取用户ID
    user_id = payload.get("sub")
    if user_id is None:
        raise credentials_exception
    
    # 在独立的数据库会话中验证用户是否存在
    try:
        from ...database import SessionLocal
        db = SessionLocal()
        user_query = text("SELECT id, status FROM users WHERE id = :user_id")
        result = db.execute(user_query, {"user_id": int(user_id)}).fetchone()
        db.close()
        
        if not result:  # 用户不存在
            raise credentials_exception
            
        return int(user_id)
    except HTTPException:
        # 重新抛出认证相关的HTTPException
        raise
    except Exception as e:
        # 数据库错误转换为认证失败
        logger.error(f"认证过程中数据库错误: {e}")
        raise credentials_exception

# ==================== 基础认证接口 ====================

@router.post("/login", summary="用户登录")
async def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    用户登录接口 - 兼容当前数据库表结构
    """
    try:
        # 使用原始SQL查询用户，兼容当前数据库结构
        user_query = text("""
            SELECT id, username, email, hashed_password, is_superuser 
            FROM users 
            WHERE username = :username OR email = :username
        """)
        
        result = db.execute(user_query, {"username": form_data.username}).fetchone()
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户名或密码错误"
            )
        
        user_id, username, email, hashed_password, is_superuser = result
        
        # 检查用户状态 - 根据实际表结构调整
        # 暂时假设所有用户都是active状态，因为没有is_active字段
        
        # 验证密码
        if not auth_manager.verify_password(form_data.password, hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户名或密码错误"
            )
        
        # 创建令牌
        access_token, refresh_token = auth_manager.create_tokens(user_id)
        
        # 更新最后登录时间
        update_query = text("""
            UPDATE users 
            SET last_login = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP 
            WHERE id = :user_id
        """)
        db.execute(update_query, {"user_id": user_id})
        db.commit()
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": 3600
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"登录错误详情: {e}")  # 临时调试输出
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"登录错误: {str(e)}"
        )


@router.get("/me", summary="获取当前用户信息")
async def get_current_user_info(
    current_user_id: int = Depends(get_current_user_from_token)
):
    """获取当前用户信息 - 兼容当前数据库表结构"""
    try:
        from ...database import SessionLocal
        db = SessionLocal()
        
        user_query = text("""
            SELECT id, username, email, status, is_superuser, created_at, last_login
            FROM users 
            WHERE id = :user_id
        """)
        
        result = db.execute(user_query, {"user_id": current_user_id}).fetchone()
        db.close()
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )
        
        user_id, username, email, status, is_superuser, created_at, last_login = result
        
        return {
            "id": user_id,
            "username": username,
            "email": email,
            "full_name": username,  # 临时使用username作为full_name
            "status": status,
            "is_verified": True,  # 临时设为True
            "is_superuser": is_superuser,
            "roles": [{"name": "admin", "display_name": "管理员"}] if is_superuser else [],
            "permissions": [],
            "created_at": created_at.isoformat() if created_at else None,
            "last_login": last_login.isoformat() if last_login else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取用户信息错误: {str(e)}"
        )

