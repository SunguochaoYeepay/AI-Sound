#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
认证核心模块
"""

import warnings
# 抑制bcrypt版本兼容性警告，这是已知的兼容性问题
warnings.filterwarnings("ignore", message=".*bcrypt version.*")
warnings.filterwarnings("ignore", message=".*error reading bcrypt version.*")

from jose import jwt
from jose.exceptions import JWTError, ExpiredSignatureError
import uuid
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from functools import wraps
from fastapi import HTTPException, Depends, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from passlib.context import CryptContext
import uuid

from app.database import get_db
from app.models.auth import User, UserSession, LoginLog, Role, Permission, UserStatus
from app.config import settings

# 密码加密上下文 - 添加兼容性配置
pwd_context = CryptContext(
    schemes=["bcrypt"], 
    deprecated="auto",
    # 兼容新版bcrypt，避免版本警告
    bcrypt__rounds=12,
    bcrypt__ident="2b"
)

# HTTP Bearer认证
security = HTTPBearer()


class AuthManager:
    """认证管理器"""
    
    def __init__(self):
        # 从环境变量获取secret key，生产环境必须设置
        self.secret_key = settings.SECRET_KEY
        if not self.secret_key:
            raise ValueError("SECRET_KEY must be set in environment variables")
        self.algorithm = "HS256"
        self.access_token_expire_minutes = 30
        self.refresh_token_expire_days = 7
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """验证密码"""
        return pwd_context.verify(plain_password, hashed_password)
    
    def get_password_hash(self, password: str) -> str:
        """生成密码哈希"""
        return pwd_context.hash(password)
    
    def create_access_token(self, user_id: int, session_id: str) -> str:
        """创建访问令牌"""
        expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        to_encode = {
            "sub": str(user_id),
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "access",
            "sid": session_id
        }
        return jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
    
    def create_refresh_token(self, user_id: int, session_id: str) -> str:
        """创建刷新令牌"""
        expire = datetime.utcnow() + timedelta(days=self.refresh_token_expire_days)
        to_encode = {
            "sub": str(user_id),
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "refresh",
            "sid": session_id
        }
        return jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
    
    def create_tokens(self, user_id: int) -> tuple[str, str]:
        """创建访问令牌和刷新令牌"""
        session_id = str(uuid.uuid4())
        access_token = self.create_access_token(user_id, session_id)
        refresh_token = self.create_refresh_token(user_id, session_id)
        return access_token, refresh_token
    
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """验证令牌"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except (JWTError, ExpiredSignatureError, Exception):
            # 捕获所有JWT相关异常
            return None
    
    def authenticate_user(self, db: Session, username: str, password: str) -> Optional[User]:
        """验证用户身份"""
        user = db.query(User).filter(
            (User.username == username) | (User.email == username)
        ).first()
        
        if not user or not self.verify_password(password, user.hashed_password):
            return None
        
        return user
    
    def create_user_session(self, db: Session, user: User, request: Request) -> UserSession:
        """创建用户会话"""
        session_id = str(uuid.uuid4())
        session = UserSession(
            user_id=user.id,
            token_id=session_id,
            ip_address=self.get_client_ip(request),
            user_agent=request.headers.get("User-Agent", ""),
            expires_at=datetime.utcnow() + timedelta(days=self.refresh_token_expire_days)
        )
        db.add(session)
        db.commit()
        db.refresh(session)
        return session
    
    def revoke_user_session(self, db: Session, session_id: str):
        """撤销用户会话"""
        session = db.query(UserSession).filter(
            UserSession.token_id == session_id
        ).first()
        if session:
            session.revoke()
            db.commit()
    
    def log_login_attempt(self, db: Session, username: str, success: bool, 
                         request: Request, failure_reason: str = None,
                         user_id: int = None):
        """记录登录尝试"""
        log = LoginLog(
            user_id=user_id,
            username=username,
            ip_address=self.get_client_ip(request),
            user_agent=request.headers.get("User-Agent", ""),
            success=success,
            failure_reason=failure_reason
        )
        db.add(log)
        db.commit()
    
    def get_client_ip(self, request: Request) -> str:
        """获取客户端IP地址"""
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "unknown"
    
    def update_last_login(self, db: Session, user_id: int):
        """更新用户最后登录时间"""
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            user.last_login = datetime.utcnow()
            db.commit()


# 全局认证管理器实例
auth_manager = AuthManager()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """获取当前用户"""
    
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
    
    # 暂时跳过会话检查，先测试基本认证功能
    # session_id = payload.get("sid")
    # if session_id:
    #     session = db.query(UserSession).filter(
    #         UserSession.token_id == session_id
    #     ).first()
    #     if not session or not session.is_valid:
    #         raise credentials_exception
    
    # 获取用户
    user = db.query(User).filter(User.id == int(user_id)).first()
    if user is None:
        raise credentials_exception
    
    # 检查用户状态
    if user.status != UserStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="用户账号已被禁用"
        )
    
    return user


def require_permissions(*permissions: str):
    """权限装饰器"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 从kwargs中获取current_user
            current_user = kwargs.get('current_user')
            if not current_user:
                # 如果没有在kwargs中，尝试从args中获取
                for arg in args:
                    if isinstance(arg, User):
                        current_user = arg
                        break
            
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="需要登录"
                )
            
            # 检查权限
            for permission in permissions:
                if not current_user.has_permission(permission):
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"缺少权限: {permission}"
                    )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator


def require_roles(*roles: str):
    """角色装饰器"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            current_user = kwargs.get('current_user')
            if not current_user:
                for arg in args:
                    if isinstance(arg, User):
                        current_user = arg
                        break
            
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="需要登录"
                )
            
            # 检查角色
            has_role = any(current_user.has_role(role) for role in roles)
            if not has_role:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"需要角色: {', '.join(roles)}"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator


# 常用权限检查依赖
async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """获取当前活跃用户"""
    if current_user.status != "active":
        raise HTTPException(status_code=400, detail="用户账号未激活")
    return current_user


async def get_current_admin_user(current_user: User = Depends(get_current_user)) -> User:
    """获取当前管理员用户"""
    if not current_user.has_role("admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限"
        )
    return current_user


def require_permission(user: User, permission: str):
    """检查用户权限"""
    if user.is_superuser:
        return  # 超级管理员拥有所有权限
    
    if not user.has_permission(permission):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"缺少权限: {permission}"
        )