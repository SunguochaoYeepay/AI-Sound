"""
角色管理API
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.auth import get_current_user, require_permission
from app.models.auth import User, Role, Permission
from app.schemas.role import (
    RoleCreate,
    RoleUpdate,
    RoleResponse,
    RoleListResponse,
    RolePermissionUpdate
)
from app.services.role_service import RoleService
from app.utils.permissions import PERMISSIONS

router = APIRouter(prefix="/roles", tags=["角色管理"])

@router.get("/", response_model=RoleListResponse)
async def get_roles(
    skip: int = Query(0, ge=0, description="跳过记录数"),
    limit: int = Query(100, ge=1, le=1000, description="返回记录数"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    role_status: Optional[str] = Query(None, description="角色状态筛选"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取角色列表"""
    # 权限检查
    if not current_user.is_superuser:
        require_permission(current_user, PERMISSIONS.ROLE_VIEW)
    
    try:
        role_service = RoleService(db)
        roles, total = role_service.get_roles(
            skip=skip,
            limit=limit,
            search=search,
            status=role_status
        )
        
        return RoleListResponse(
            roles=[RoleResponse.from_orm(role) for role in roles],
            total=total,
            skip=skip,
            limit=limit
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取角色列表失败: {str(e)}"
        )

@router.get("/{role_id}", response_model=RoleResponse)
async def get_role(
    role_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取角色详情"""
    # 权限检查
    if not current_user.is_superuser:
        require_permission(current_user, PERMISSIONS.ROLE_VIEW)
    
    try:
        role_service = RoleService(db)
        role = role_service.get_role_by_id(role_id)
        if not role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="角色不存在"
            )
        
        return RoleResponse.from_orm(role)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取角色详情失败: {str(e)}"
        )

@router.post("/", response_model=RoleResponse)
async def create_role(
    role_data: RoleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建角色"""
    # 权限检查
    if not current_user.is_superuser:
        require_permission(current_user, PERMISSIONS.ROLE_CREATE)
    
    try:
        role_service = RoleService(db)
        
        # 检查角色名是否已存在
        if role_service.get_role_by_name(role_data.name):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="角色标识已存在"
            )
        
        role = role_service.create_role(role_data)
        return RoleResponse.from_orm(role)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建角色失败: {str(e)}"
        )

@router.put("/{role_id}", response_model=RoleResponse)
async def update_role(
    role_id: int,
    role_data: RoleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新角色"""
    # 权限检查
    if not current_user.is_superuser:
        require_permission(current_user, PERMISSIONS.ROLE_EDIT)
    
    try:
        role_service = RoleService(db)
        role = role_service.get_role_by_id(role_id)
        if not role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="角色不存在"
            )
        
        # 系统内置角色不能修改名称
        if role.name in ['admin', 'user'] and role_data.name and role_data.name != role.name:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="系统内置角色不能修改标识"
            )
        
        # 检查新角色名是否已被其他角色使用
        if role_data.name and role_data.name != role.name:
            existing_role = role_service.get_role_by_name(role_data.name)
            if existing_role and existing_role.id != role_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="角色标识已被其他角色使用"
                )
        
        updated_role = role_service.update_role(role_id, role_data)
        return RoleResponse.from_orm(updated_role)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新角色失败: {str(e)}"
        )

@router.delete("/{role_id}")
async def delete_role(
    role_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除角色"""
    # 权限检查
    if not current_user.is_superuser:
        require_permission(current_user, PERMISSIONS.ROLE_DELETE)
    
    try:
        role_service = RoleService(db)
        role = role_service.get_role_by_id(role_id)
        if not role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="角色不存在"
            )
        
        # 系统内置角色不能删除
        if role.name in ['admin', 'user']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="系统内置角色不能删除"
            )
        
        # 检查是否有用户使用该角色
        if role.users:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"该角色正在被 {len(role.users)} 个用户使用，无法删除"
            )
        
        role_service.delete_role(role_id)
        return {"message": "角色删除成功"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除角色失败: {str(e)}"
        )

@router.get("/{role_id}/permissions", response_model=List[dict])
async def get_role_permissions(
    role_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取角色权限列表"""
    # 权限检查
    if not current_user.is_superuser:
        require_permission(current_user, PERMISSIONS.ROLE_VIEW)
    
    try:
        role_service = RoleService(db)
        role = role_service.get_role_by_id(role_id)
        if not role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="角色不存在"
            )
        
        return [
            {
                "id": permission.id,
                "name": permission.name,
                "display_name": permission.display_name,
                "description": permission.description,
                "resource": permission.resource,
                "action": permission.action
            }
            for permission in role.permissions
        ]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取角色权限失败: {str(e)}"
        )

@router.put("/{role_id}/permissions")
async def update_role_permissions(
    role_id: int,
    permission_data: RolePermissionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新角色权限"""
    # 权限检查
    if not current_user.is_superuser:
        require_permission(current_user, PERMISSIONS.ROLE_EDIT)
    
    try:
        role_service = RoleService(db)
        role = role_service.get_role_by_id(role_id)
        if not role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="角色不存在"
            )
        
        # 更新角色权限
        result = role_service.update_role_permissions(role_id, permission_data.permission_names)
        
        if result:
            return {"message": "角色权限更新成功"}
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="角色权限更新失败"
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新角色权限失败: {str(e)}"
        )

@router.post("/{role_id}/permissions/{permission_id}")
async def assign_permission_to_role(
    role_id: int,
    permission_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """为角色分配权限"""
    # 权限检查
    if not current_user.is_superuser:
        require_permission(current_user, PERMISSIONS.ROLE_EDIT)
    
    try:
        role_service = RoleService(db)
        result = role_service.assign_permission(role_id, permission_id)
        
        if result:
            return {"message": "权限分配成功"}
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="权限分配失败"
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"分配权限失败: {str(e)}"
        )

@router.delete("/{role_id}/permissions/{permission_id}")
async def remove_permission_from_role(
    role_id: int,
    permission_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """移除角色权限"""
    # 权限检查
    if not current_user.is_superuser:
        require_permission(current_user, PERMISSIONS.ROLE_EDIT)
    
    try:
        role_service = RoleService(db)
        result = role_service.remove_permission(role_id, permission_id)
        
        if result:
            return {"message": "权限移除成功"}
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="权限移除失败"
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"移除权限失败: {str(e)}"
        )

@router.get("/{role_id}/users", response_model=List[dict])
async def get_role_users(
    role_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取角色下的用户列表"""
    # 权限检查
    if not current_user.is_superuser:
        require_permission(current_user, PERMISSIONS.ROLE_VIEW)
    
    try:
        role_service = RoleService(db)
        role = role_service.get_role_by_id(role_id)
        if not role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="角色不存在"
            )
        
        return [
            {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "full_name": user.full_name,
                "status": user.status,
                "is_superuser": user.is_superuser,
                "created_at": user.created_at.isoformat() if user.created_at else None
            }
            for user in role.users
        ]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取角色用户失败: {str(e)}"
        )

@router.post("/{role_id}/toggle-status")
async def toggle_role_status(
    role_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """切换角色状态（启用/禁用）"""
    # 权限检查
    if not current_user.is_superuser:
        require_permission(current_user, PERMISSIONS.ROLE_EDIT)
    
    try:
        role_service = RoleService(db)
        role = role_service.get_role_by_id(role_id)
        if not role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="角色不存在"
            )
        
        # 系统内置角色不能禁用
        if role.name in ['admin', 'user']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="系统内置角色不能禁用"
            )
        
        new_status = "inactive" if role.status == "active" else "active"
        updated_role = role_service.update_role_status(role_id, new_status)
        
        return {
            "message": f"角色状态已{'禁用' if new_status == 'inactive' else '启用'}",
            "status": new_status
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"切换角色状态失败: {str(e)}"
        )