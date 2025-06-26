"""
角色相关的Pydantic模型
"""
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, validator

class RoleBase(BaseModel):
    """角色基础模型"""
    name: str
    display_name: str
    description: Optional[str] = None
    status: str = "active"

class RoleCreate(RoleBase):
    """创建角色模型"""
    permissions: Optional[List[str]] = []
    
    @validator('name')
    def validate_name(cls, v):
        if len(v) < 2 or len(v) > 50:
            raise ValueError('角色标识长度必须在2-50个字符之间')
        # 角色标识只能包含字母、数字和下划线
        if not v.replace('_', '').isalnum():
            raise ValueError('角色标识只能包含字母、数字和下划线')
        return v
    
    @validator('display_name')
    def validate_display_name(cls, v):
        if len(v) < 2 or len(v) > 100:
            raise ValueError('角色名称长度必须在2-100个字符之间')
        return v

class RoleUpdate(BaseModel):
    """更新角色模型"""
    name: Optional[str] = None
    display_name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    permissions: Optional[List[str]] = None
    
    @validator('name')
    def validate_name(cls, v):
        if v is not None:
            if len(v) < 2 or len(v) > 50:
                raise ValueError('角色标识长度必须在2-50个字符之间')
            if not v.replace('_', '').isalnum():
                raise ValueError('角色标识只能包含字母、数字和下划线')
        return v
    
    @validator('display_name')
    def validate_display_name(cls, v):
        if v is not None and (len(v) < 2 or len(v) > 100):
            raise ValueError('角色名称长度必须在2-100个字符之间')
        return v

class RolePermissionUpdate(BaseModel):
    """角色权限更新模型"""
    permission_names: List[str]

class PermissionInfo(BaseModel):
    """权限信息模型"""
    id: int
    name: str
    display_name: str
    description: Optional[str] = None
    resource: str
    action: str
    
    class Config:
        from_attributes = True

class UserInfo(BaseModel):
    """用户信息模型"""
    id: int
    username: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    status: str
    is_superuser: bool
    
    class Config:
        from_attributes = True

class RoleResponse(BaseModel):
    """角色响应模型"""
    id: int
    name: str
    display_name: str
    description: Optional[str] = None
    status: str
    permissions: List[PermissionInfo] = []
    users: List[UserInfo] = []
    user_count: int = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True
    
    @validator('user_count', pre=True, always=True)
    def set_user_count(cls, v, values):
        users = values.get('users', [])
        return len(users) if users else 0

class RoleListResponse(BaseModel):
    """角色列表响应模型"""
    roles: List[RoleResponse]
    total: int
    skip: int
    limit: int