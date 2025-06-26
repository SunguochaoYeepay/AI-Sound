"""
用户服务类
"""
from typing import List, Tuple, Optional
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, func

from app.models.auth import User, Role
from app.schemas.user import UserCreate, UserUpdate
from app.core.auth import auth_manager
from app.utils.logger import get_logger

logger = get_logger(__name__)

class UserService:
    def __init__(self, db: Session):
        self.db = db
    
    def get_users(
        self,
        skip: int = 0,
        limit: int = 100,
        search: Optional[str] = None,
        status: Optional[str] = None,
        role: Optional[str] = None
    ) -> Tuple[List[User], int]:
        """获取用户列表"""
        try:
            query = self.db.query(User).options(joinedload(User.roles))
            
            # 搜索条件
            if search:
                search_filter = or_(
                    User.username.ilike(f"%{search}%"),
                    User.email.ilike(f"%{search}%"),
                    User.full_name.ilike(f"%{search}%")
                )
                query = query.filter(search_filter)
            
            # 状态筛选
            if status:
                query = query.filter(User.status == status)
            
            # 角色筛选
            if role:
                query = query.join(User.roles).filter(Role.name == role)
            
            # 获取总数
            total = query.count()
            
            # 分页
            users = query.offset(skip).limit(limit).all()
            
            return users, total
        except Exception as e:
            logger.error(f"获取用户列表失败: {e}")
            raise
    
    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """根据ID获取用户"""
        try:
            return self.db.query(User).options(joinedload(User.roles)).filter(User.id == user_id).first()
        except Exception as e:
            logger.error(f"获取用户失败: {e}")
            raise
    
    def get_user_by_username(self, username: str) -> Optional[User]:
        """根据用户名获取用户"""
        try:
            return self.db.query(User).options(joinedload(User.roles)).filter(User.username == username).first()
        except Exception as e:
            logger.error(f"获取用户失败: {e}")
            raise
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """根据邮箱获取用户"""
        try:
            return self.db.query(User).options(joinedload(User.roles)).filter(User.email == email).first()
        except Exception as e:
            logger.error(f"获取用户失败: {e}")
            raise
    
    def create_user(self, user_data: UserCreate) -> User:
        """创建用户"""
        try:
            # 创建用户
            db_user = User(
                username=user_data.username,
                email=user_data.email,
                full_name=user_data.full_name,
                hashed_password=auth_manager.get_password_hash(user_data.password),
                status=user_data.status,
                daily_quota=user_data.daily_quota,
                is_superuser=user_data.is_superuser,
                is_verified=True  # 管理员创建的用户默认已验证
            )
            
            self.db.add(db_user)
            self.db.flush()  # 获取用户ID
            
            # 分配角色
            if user_data.roles:
                roles = self.db.query(Role).filter(Role.name.in_(user_data.roles)).all()
                db_user.roles = roles
            
            self.db.commit()
            self.db.refresh(db_user)
            
            logger.info(f"用户创建成功: {user_data.username}")
            return db_user
        except Exception as e:
            self.db.rollback()
            logger.error(f"创建用户失败: {e}")
            raise
    
    def update_user(self, user_id: int, user_data: UserUpdate) -> User:
        """更新用户"""
        try:
            db_user = self.get_user_by_id(user_id)
            if not db_user:
                raise ValueError("用户不存在")
            
            # 更新基本信息
            update_data = user_data.dict(exclude_unset=True, exclude={'roles'})
            for field, value in update_data.items():
                setattr(db_user, field, value)
            
            # 更新角色
            if user_data.roles is not None:
                roles = self.db.query(Role).filter(Role.name.in_(user_data.roles)).all()
                db_user.roles = roles
            
            self.db.commit()
            self.db.refresh(db_user)
            
            logger.info(f"用户更新成功: {db_user.username}")
            return db_user
        except Exception as e:
            self.db.rollback()
            logger.error(f"更新用户失败: {e}")
            raise
    
    def delete_user(self, user_id: int) -> bool:
        """删除用户"""
        try:
            db_user = self.get_user_by_id(user_id)
            if not db_user:
                return False
            
            self.db.delete(db_user)
            self.db.commit()
            
            logger.info(f"用户删除成功: {db_user.username}")
            return True
        except Exception as e:
            self.db.rollback()
            logger.error(f"删除用户失败: {e}")
            raise
    
    def reset_password(self, user_id: int, new_password: str) -> bool:
        """重置用户密码"""
        try:
            db_user = self.get_user_by_id(user_id)
            if not db_user:
                return False
            
            db_user.hashed_password = auth_manager.get_password_hash(new_password)
            self.db.commit()
            
            logger.info(f"用户密码重置成功: {db_user.username}")
            return True
        except Exception as e:
            self.db.rollback()
            logger.error(f"重置密码失败: {e}")
            raise
    
    def update_user_status(self, user_id: int, status: str) -> User:
        """更新用户状态"""
        try:
            db_user = self.get_user_by_id(user_id)
            if not db_user:
                raise ValueError("用户不存在")
            
            db_user.status = status
            self.db.commit()
            self.db.refresh(db_user)
            
            logger.info(f"用户状态更新成功: {db_user.username} -> {status}")
            return db_user
        except Exception as e:
            self.db.rollback()
            logger.error(f"更新用户状态失败: {e}")
            raise
    
    def assign_role(self, user_id: int, role_id: int) -> bool:
        """为用户分配角色"""
        try:
            db_user = self.get_user_by_id(user_id)
            if not db_user:
                return False
            
            role = self.db.query(Role).filter(Role.id == role_id).first()
            if not role:
                return False
            
            if role not in db_user.roles:
                db_user.roles.append(role)
                self.db.commit()
                logger.info(f"角色分配成功: {db_user.username} -> {role.name}")
            
            return True
        except Exception as e:
            self.db.rollback()
            logger.error(f"分配角色失败: {e}")
            raise
    
    def remove_role(self, user_id: int, role_id: int) -> bool:
        """移除用户角色"""
        try:
            db_user = self.get_user_by_id(user_id)
            if not db_user:
                return False
            
            role = self.db.query(Role).filter(Role.id == role_id).first()
            if not role:
                return False
            
            if role in db_user.roles:
                db_user.roles.remove(role)
                self.db.commit()
                logger.info(f"角色移除成功: {db_user.username} -> {role.name}")
            
            return True
        except Exception as e:
            self.db.rollback()
            logger.error(f"移除角色失败: {e}")
            raise