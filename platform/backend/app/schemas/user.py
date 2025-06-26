"""
用户相关的Pydantic模型
"""
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, EmailStr, validator

class UserBase(BaseModel):
    """用户基础模型"""
    username: str
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    status: str = "active"
    daily_quota: int = 1000
    is_superuser: bool = False

class UserCreate(UserBase):
    """创建用户模型"""
    password: str
    roles: Optional[List[str]] = []
    
    @validator('username')
    def validate_username(cls, v):
        if len(v) < 3 or len(v) > 20:
            raise ValueError('用户名长度必须在3-20个字符之间')
        return v
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 6:
            raise ValueError('密码长度至少6个字符')
        return v

class UserUpdate(BaseModel):
    """更新用户模型"""
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    status: Optional[str] = None
    daily_quota: Optional[int] = None
    is_superuser: Optional[bool] = None
    roles: Optional[List[str]] = None

class PasswordReset(BaseModel):
    """密码重置模型"""
    password: str
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 6:
            raise ValueError('密码长度至少6个字符')
        return v

class RoleInfo(BaseModel):
    """角色信息模型"""
    id: int
    name: str
    display_name: str
    description: Optional[str] = None
    
    class Config:
        from_attributes = True

class UserResponse(BaseModel):
    """用户响应模型"""
    id: int
    username: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    status: str
    daily_quota: int
    used_quota: int = 0
    is_superuser: bool
    is_verified: bool = False
    roles: List[RoleInfo] = []
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    last_login: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class UserListResponse(BaseModel):
    """用户列表响应模型"""
    users: List[UserResponse]
    total: int
    skip: int
    limit: int