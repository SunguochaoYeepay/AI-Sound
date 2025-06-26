"""
角色服务类
"""
from typing import List, Tuple, Optional
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, func

from app.models.auth import Role, Permission
from app.schemas.role import RoleCreate, RoleUpdate
from app.utils.logger import get_logger

logger = get_logger(__name__)

class RoleService:
    def __init__(self, db: Session):
        self.db = db
    
    def get_roles(
        self,
        skip: int = 0,
        limit: int = 100,
        search: Optional[str] = None,
        status: Optional[str] = None
    ) -> Tuple[List[Role], int]:
        """获取角色列表"""
        try:
            query = self.db.query(Role).options(
                joinedload(Role.permissions),
                joinedload(Role.users)
            )
            
            # 搜索条件
            if search:
                search_filter = or_(
                    Role.name.ilike(f"%{search}%"),
                    Role.display_name.ilike(f"%{search}%"),
                    Role.description.ilike(f"%{search}%")
                )
                query = query.filter(search_filter)
            
            # 状态筛选
            if status:
                query = query.filter(Role.status == status)
            
            # 获取总数
            total = query.count()
            
            # 分页
            roles = query.offset(skip).limit(limit).all()
            
            return roles, total
        except Exception as e:
            logger.error(f"获取角色列表失败: {e}")
            raise
    
    def get_role_by_id(self, role_id: int) -> Optional[Role]:
        """根据ID获取角色"""
        try:
            return self.db.query(Role).options(
                joinedload(Role.permissions),
                joinedload(Role.users)
            ).filter(Role.id == role_id).first()
        except Exception as e:
            logger.error(f"获取角色失败: {e}")
            raise
    
    def get_role_by_name(self, name: str) -> Optional[Role]:
        """根据名称获取角色"""
        try:
            return self.db.query(Role).options(
                joinedload(Role.permissions),
                joinedload(Role.users)
            ).filter(Role.name == name).first()
        except Exception as e:
            logger.error(f"获取角色失败: {e}")
            raise
    
    def create_role(self, role_data: RoleCreate) -> Role:
        """创建角色"""
        try:
            # 创建角色
            db_role = Role(
                name=role_data.name,
                display_name=role_data.display_name,
                description=role_data.description,
                status=role_data.status
            )
            
            self.db.add(db_role)
            self.db.flush()  # 获取角色ID
            
            # 分配权限
            if role_data.permissions:
                permissions = self.db.query(Permission).filter(
                    Permission.name.in_(role_data.permissions)
                ).all()
                db_role.permissions = permissions
            
            self.db.commit()
            self.db.refresh(db_role)
            
            logger.info(f"角色创建成功: {role_data.name}")
            return db_role
        except Exception as e:
            self.db.rollback()
            logger.error(f"创建角色失败: {e}")
            raise
    
    def update_role(self, role_id: int, role_data: RoleUpdate) -> Role:
        """更新角色"""
        try:
            db_role = self.get_role_by_id(role_id)
            if not db_role:
                raise ValueError("角色不存在")
            
            # 更新基本信息
            update_data = role_data.dict(exclude_unset=True, exclude={'permissions'})
            for field, value in update_data.items():
                setattr(db_role, field, value)
            
            # 更新权限
            if role_data.permissions is not None:
                permissions = self.db.query(Permission).filter(
                    Permission.name.in_(role_data.permissions)
                ).all()
                db_role.permissions = permissions
            
            self.db.commit()
            self.db.refresh(db_role)
            
            logger.info(f"角色更新成功: {db_role.name}")
            return db_role
        except Exception as e:
            self.db.rollback()
            logger.error(f"更新角色失败: {e}")
            raise
    
    def delete_role(self, role_id: int) -> bool:
        """删除角色"""
        try:
            db_role = self.get_role_by_id(role_id)
            if not db_role:
                return False
            
            self.db.delete(db_role)
            self.db.commit()
            
            logger.info(f"角色删除成功: {db_role.name}")
            return True
        except Exception as e:
            self.db.rollback()
            logger.error(f"删除角色失败: {e}")
            raise
    
    def update_role_status(self, role_id: int, status: str) -> Role:
        """更新角色状态"""
        try:
            db_role = self.get_role_by_id(role_id)
            if not db_role:
                raise ValueError("角色不存在")
            
            db_role.status = status
            self.db.commit()
            self.db.refresh(db_role)
            
            logger.info(f"角色状态更新成功: {db_role.name} -> {status}")
            return db_role
        except Exception as e:
            self.db.rollback()
            logger.error(f"更新角色状态失败: {e}")
            raise
    
    def update_role_permissions(self, role_id: int, permission_names: List[str]) -> bool:
        """更新角色权限"""
        try:
            db_role = self.get_role_by_id(role_id)
            if not db_role:
                return False
            
            # 获取权限对象
            permissions = self.db.query(Permission).filter(
                Permission.name.in_(permission_names)
            ).all()
            
            # 更新角色权限
            db_role.permissions = permissions
            self.db.commit()
            
            logger.info(f"角色权限更新成功: {db_role.name}")
            return True
        except Exception as e:
            self.db.rollback()
            logger.error(f"更新角色权限失败: {e}")
            raise
    
    def assign_permission(self, role_id: int, permission_id: int) -> bool:
        """为角色分配权限"""
        try:
            db_role = self.get_role_by_id(role_id)
            if not db_role:
                return False
            
            permission = self.db.query(Permission).filter(Permission.id == permission_id).first()
            if not permission:
                return False
            
            if permission not in db_role.permissions:
                db_role.permissions.append(permission)
                self.db.commit()
                logger.info(f"权限分配成功: {db_role.name} -> {permission.name}")
            
            return True
        except Exception as e:
            self.db.rollback()
            logger.error(f"分配权限失败: {e}")
            raise
    
    def remove_permission(self, role_id: int, permission_id: int) -> bool:
        """移除角色权限"""
        try:
            db_role = self.get_role_by_id(role_id)
            if not db_role:
                return False
            
            permission = self.db.query(Permission).filter(Permission.id == permission_id).first()
            if not permission:
                return False
            
            if permission in db_role.permissions:
                db_role.permissions.remove(permission)
                self.db.commit()
                logger.info(f"权限移除成功: {db_role.name} -> {permission.name}")
            
            return True
        except Exception as e:
            self.db.rollback()
            logger.error(f"移除权限失败: {e}")
            raise