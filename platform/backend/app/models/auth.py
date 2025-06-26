#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
用户认证与权限数据模型
"""

from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey, Table
from sqlalchemy.orm import relationship
from datetime import datetime
from enum import Enum

from .base import BaseModel

# 用户角色关联表
user_roles = Table(
    'user_roles',
    BaseModel.metadata,
    Column('user_id', Integer, ForeignKey('users.id'), primary_key=True),
    Column('role_id', Integer, ForeignKey('roles.id'), primary_key=True)
)

# 角色权限关联表
role_permissions = Table(
    'role_permissions',
    BaseModel.metadata,
    Column('role_id', Integer, ForeignKey('roles.id'), primary_key=True),
    Column('permission_id', Integer, ForeignKey('permissions.id'), primary_key=True)
)


class UserStatus(str, Enum):
    """用户状态枚举"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    DELETED = "deleted"


class User(BaseModel):
    """用户模型"""
    __tablename__ = 'users'
    
    username = Column(String(50), unique=True, nullable=False, index=True, comment="用户名")
    email = Column(String(100), unique=True, nullable=False, index=True, comment="邮箱")
    hashed_password = Column(String(255), nullable=False, comment="密码哈希")
    full_name = Column(String(100), nullable=True, comment="真实姓名")
    avatar_url = Column(String(500), nullable=True, comment="头像URL")
    
    # 状态信息
    status = Column(String(20), default=UserStatus.ACTIVE, comment="用户状态")
    is_verified = Column(Boolean, default=False, comment="是否已验证邮箱")
    is_superuser = Column(Boolean, default=False, comment="是否超级管理员")
    
    # 使用配额
    daily_quota = Column(Integer, default=100, comment="每日TTS配额")
    used_quota = Column(Integer, default=0, comment="已使用配额")
    quota_reset_date = Column(DateTime, default=datetime.utcnow, comment="配额重置日期")
    
    # 时间戳
    last_login = Column(DateTime, nullable=True, comment="最后登录时间")
    
    # 关系
    roles = relationship("Role", secondary=user_roles, back_populates="users", lazy="select")
    user_sessions = relationship("UserSession", back_populates="user", cascade="all, delete-orphan")
    
    # 🎵 音乐生成相关关系
    music_generation_tasks = relationship("MusicGenerationTask", back_populates="user", cascade="all, delete-orphan")
    music_generation_batches = relationship("MusicGenerationBatch", back_populates="user", cascade="all, delete-orphan")
    music_style_templates = relationship("MusicStyleTemplate", back_populates="creator", cascade="all, delete-orphan")
    music_generation_usage_logs = relationship("MusicGenerationUsageLog", back_populates="user", cascade="all, delete-orphan")
    music_generation_settings = relationship("MusicGenerationSettings", back_populates="modifier")
    
    def __repr__(self):
        return f"<User(username='{self.username}', email='{self.email}')>"
    
    @property
    def permissions(self):
        """获取用户所有权限"""
        perms = set()
        for role in self.roles:
            perms.update([p.code for p in role.permissions])
        return list(perms)
    
    def has_permission(self, permission_code: str) -> bool:
        """检查用户是否有特定权限"""
        return permission_code in self.permissions
    
    def has_role(self, role_name: str) -> bool:
        """检查用户是否有特定角色"""
        return any(role.name == role_name for role in self.roles)
    
    def reset_daily_quota(self):
        """重置每日配额"""
        now = datetime.utcnow()
        if self.quota_reset_date.date() < now.date():
            self.used_quota = 0
            self.quota_reset_date = now
            return True
        return False


class Role(BaseModel):
    """角色模型"""
    __tablename__ = 'roles'
    
    name = Column(String(50), unique=True, nullable=False, comment="角色名称")
    display_name = Column(String(100), nullable=False, comment="显示名称")
    description = Column(Text, nullable=True, comment="角色描述")
    status = Column(String(20), default="active", comment="角色状态")
    is_system = Column(Boolean, default=False, comment="是否系统角色")
    
    # 关系
    users = relationship("User", secondary=user_roles, back_populates="roles")
    permissions = relationship("Permission", secondary=role_permissions, back_populates="roles", lazy="select")
    
    def __repr__(self):
        return f"<Role(name='{self.name}', display_name='{self.display_name}')>"


class Permission(BaseModel):
    """权限模型"""
    __tablename__ = 'permissions'
    
    code = Column(String(100), unique=True, nullable=False, comment="权限代码")
    name = Column(String(100), nullable=False, comment="权限名称")
    description = Column(Text, nullable=True, comment="权限描述")
    module = Column(String(50), nullable=False, comment="所属模块")
    
    # 关系
    roles = relationship("Role", secondary=role_permissions, back_populates="permissions")
    
    def __repr__(self):
        return f"<Permission(code='{self.code}', name='{self.name}')>"


class UserSession(BaseModel):
    """用户会话模型"""
    __tablename__ = 'user_sessions'
    
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, comment="用户ID")
    token_id = Column(String(255), unique=True, nullable=False, comment="Token ID")
    ip_address = Column(String(45), nullable=True, comment="IP地址")
    user_agent = Column(Text, nullable=True, comment="用户代理")
    
    expires_at = Column(DateTime, nullable=False, comment="过期时间")
    revoked_at = Column(DateTime, nullable=True, comment="撤销时间")
    
    # 关系
    user = relationship("User", back_populates="user_sessions")
    
    @property
    def is_valid(self) -> bool:
        """检查会话是否有效"""
        return (
            self.revoked_at is None and 
            self.expires_at > datetime.utcnow()
        )
    
    def revoke(self):
        """撤销会话"""
        self.revoked_at = datetime.utcnow()


class LoginLog(BaseModel):
    """登录日志模型"""
    __tablename__ = 'login_logs'
    
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True, comment="用户ID")
    username = Column(String(50), nullable=True, comment="用户名")
    ip_address = Column(String(45), nullable=True, comment="IP地址")
    user_agent = Column(Text, nullable=True, comment="用户代理")
    login_time = Column(DateTime, default=datetime.utcnow, comment="登录时间")
    success = Column(Boolean, nullable=False, comment="是否成功")
    failure_reason = Column(String(200), nullable=True, comment="失败原因")
    
    def __repr__(self):
        status = "成功" if self.success else f"失败({self.failure_reason})"
        return f"<LoginLog(username='{self.username}', status='{status}')>"