"""
用户管理API
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.auth import get_current_user, require_permission
from app.models.auth import User, Role
from app.schemas.user import (
    UserCreate,
    UserUpdate,
    UserResponse,
    UserListResponse,
    PasswordReset
)
from app.services.user_service import UserService
from app.utils.permissions import PERMISSIONS

router = APIRouter(prefix="/users", tags=["用户管理"])

@router.get("/", response_model=UserListResponse)
async def get_users(
    skip: int = Query(0, ge=0, description="跳过记录数"),
    limit: int = Query(100, ge=1, le=1000, description="返回记录数"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    user_status: Optional[str] = Query(None, description="用户状态筛选"),
    role: Optional[str] = Query(None, description="角色筛选"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取用户列表"""
    # 权限检查
    if not current_user.is_superuser:
        require_permission(current_user, PERMISSIONS.USER_VIEW)
    
    try:
        user_service = UserService(db)
        users, total = user_service.get_users(
            skip=skip,
            limit=limit,
            search=search,
            status=user_status,
            role=role
        )
        
        return UserListResponse(
            users=[UserResponse.from_orm(user) for user in users],
            total=total,
            skip=skip,
            limit=limit
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取用户列表失败: {str(e)}"
        )

@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取用户详情"""
    # 权限检查：超级管理员或查看自己的信息
    if not current_user.is_superuser and current_user.id != user_id:
        require_permission(current_user, PERMISSIONS.USER_VIEW)
    
    try:
        user_service = UserService(db)
        user = user_service.get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )
        
        return UserResponse.from_orm(user)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取用户详情失败: {str(e)}"
        )

@router.post("/", response_model=UserResponse)
async def create_user(
    user_data: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建用户"""
    # 权限检查
    if not current_user.is_superuser:
        require_permission(current_user, PERMISSIONS.USER_CREATE)
    
    try:
        user_service = UserService(db)
        
        # 检查用户名是否已存在
        if user_service.get_user_by_username(user_data.username):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="用户名已存在"
            )
        
        # 检查邮箱是否已存在
        if user_data.email and user_service.get_user_by_email(user_data.email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="邮箱已存在"
            )
        
        user = user_service.create_user(user_data)
        return UserResponse.from_orm(user)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建用户失败: {str(e)}"
        )

@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新用户"""
    # 权限检查
    if not current_user.is_superuser:
        if current_user.id == user_id:
            # 用户可以更新自己的基本信息，但不能修改角色和权限
            if user_data.roles is not None or user_data.is_superuser is not None:
                require_permission(current_user, PERMISSIONS.USER_EDIT)
        else:
            require_permission(current_user, PERMISSIONS.USER_EDIT)
    else:
        # 超级管理员也不能修改自己的超级管理员状态和角色（防止意外取消权限）
        if current_user.id == user_id:
            if user_data.is_superuser is not None and not user_data.is_superuser:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="不能取消自己的超级管理员权限，请联系其他超级管理员操作"
                )
            # 超级管理员可以修改自己的基本信息，但建议不要修改关键角色
            if user_data.roles is not None:
                # 警告：这可能会影响权限，但允许操作（给予灵活性）
                pass
    
    try:
        user_service = UserService(db)
        user = user_service.get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )
        
        # 检查邮箱是否已被其他用户使用
        if user_data.email and user_data.email != user.email:
            existing_user = user_service.get_user_by_email(user_data.email)
            if existing_user and existing_user.id != user_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="邮箱已被其他用户使用"
                )
        
        updated_user = user_service.update_user(user_id, user_data)
        return UserResponse.from_orm(updated_user)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新用户失败: {str(e)}"
        )

@router.delete("/{user_id}")
async def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除用户"""
    # 权限检查
    if not current_user.is_superuser:
        require_permission(current_user, PERMISSIONS.USER_DELETE)
    
    # 不能删除自己
    if current_user.id == user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="不能删除自己"
        )
    
    try:
        user_service = UserService(db)
        user = user_service.get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )
        
        # 不能删除超级管理员（除非当前用户也是超级管理员）
        if user.is_superuser and not current_user.is_superuser:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权删除超级管理员"
            )
        
        user_service.delete_user(user_id)
        return {"message": "用户删除成功"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除用户失败: {str(e)}"
        )

@router.post("/{user_id}/reset-password")
async def reset_user_password(
    user_id: int,
    password_data: PasswordReset,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """重置用户密码"""
    # 权限检查
    if not current_user.is_superuser:
        if current_user.id == user_id:
            # 用户可以重置自己的密码
            pass
        else:
            require_permission(current_user, PERMISSIONS.USER_EDIT)
    
    try:
        user_service = UserService(db)
        user = user_service.get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )
        
        user_service.reset_password(user_id, password_data.password)
        return {"message": "密码重置成功"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"重置密码失败: {str(e)}"
        )

@router.post("/{user_id}/toggle-status")
async def toggle_user_status(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """切换用户状态（启用/禁用）"""
    # 权限检查
    if not current_user.is_superuser:
        require_permission(current_user, PERMISSIONS.USER_EDIT)
    
    # 不能禁用自己
    if current_user.id == user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="不能禁用自己"
        )
    
    try:
        user_service = UserService(db)
        user = user_service.get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )
        
        new_status = "inactive" if user.status == "active" else "active"
        updated_user = user_service.update_user_status(user_id, new_status)
        
        return {
            "message": f"用户状态已{'禁用' if new_status == 'inactive' else '启用'}",
            "status": new_status
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"切换用户状态失败: {str(e)}"
        )

@router.get("/{user_id}/roles", response_model=List[dict])
async def get_user_roles(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取用户角色列表"""
    # 权限检查
    if not current_user.is_superuser and current_user.id != user_id:
        require_permission(current_user, PERMISSIONS.USER_VIEW)
    
    try:
        user_service = UserService(db)
        user = user_service.get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )
        
        return [
            {
                "id": role.id,
                "name": role.name,
                "display_name": role.display_name,
                "description": role.description
            }
            for role in user.roles
        ]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取用户角色失败: {str(e)}"
        )

@router.post("/{user_id}/roles/{role_id}")
async def assign_role_to_user(
    user_id: int,
    role_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """为用户分配角色"""
    # 权限检查
    if not current_user.is_superuser:
        require_permission(current_user, PERMISSIONS.USER_EDIT)
    
    try:
        user_service = UserService(db)
        result = user_service.assign_role(user_id, role_id)
        
        if result:
            return {"message": "角色分配成功"}
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="角色分配失败"
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"分配角色失败: {str(e)}"
        )

@router.delete("/{user_id}/roles/{role_id}")
async def remove_role_from_user(
    user_id: int,
    role_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """移除用户角色"""
    # 权限检查
    if not current_user.is_superuser:
        require_permission(current_user, PERMISSIONS.USER_EDIT)
    
    # 防止超级管理员移除自己的管理员角色
    if current_user.id == user_id and current_user.is_superuser:
        # 检查要移除的是否是管理员角色
        from app.models.auth import Role
        role = db.query(Role).filter(Role.id == role_id).first()
        if role and role.name == "admin":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="超级管理员不能移除自己的管理员角色，请联系其他超级管理员操作"
            )
    
    try:
        user_service = UserService(db)
        result = user_service.remove_role(user_id, role_id)
        
        if result:
            return {"message": "角色移除成功"}
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="角色移除失败"
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"移除角色失败: {str(e)}"
        )