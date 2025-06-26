import os
import json
import hashlib
import secrets
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_

from app.database import get_db
from app.schemas.collaboration import (
    ProjectTemplateCreate, ProjectTemplateUpdate, ProjectTemplate,
    EditHistoryCreate, EditHistory,
    ExportTaskCreate, ExportTaskUpdate, ExportTask, ExportFormat,
    ProjectShareCreate, ProjectShareUpdate, ProjectShare,
    SyncStatusUpdate, SyncStatusResponse,
    BatchExportRequest, BatchExportResponse
)
from app.services.moviepy_service import MoviePyService
import logging

logger = logging.getLogger(__name__)


class CollaborationService:
    """协作与导出服务"""
    
    def __init__(self):
        self.moviepy_service = MoviePyService()
        self.export_dir = "storage/exports"
        self.template_dir = "storage/templates"
        self.cloud_storage_dir = "storage/cloud"
        
        # 确保目录存在
        os.makedirs(self.export_dir, exist_ok=True)
        os.makedirs(self.template_dir, exist_ok=True)
        os.makedirs(self.cloud_storage_dir, exist_ok=True)
    
    # ==================== 项目模板管理 ====================
    
    def create_template(self, db: Session, template_data: ProjectTemplateCreate, user_id: Optional[int] = None) -> ProjectTemplate:
        """创建项目模板"""
        try:
            from app.models.audio_editor import ProjectTemplateModel
            
            template = ProjectTemplateModel(
                name=template_data.name,
                description=template_data.description,
                category=template_data.category.value,
                preview_image=template_data.preview_image,
                config_data=template_data.config_data,
                is_public=template_data.is_public,
                created_by=user_id,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            
            db.add(template)
            db.commit()
            db.refresh(template)
            
            logger.info(f"Created project template: {template.id}")
            return ProjectTemplate.from_orm(template)
            
        except Exception as e:
            logger.error(f"Error creating project template: {str(e)}")
            db.rollback()
            raise
    
    def get_templates(self, db: Session, category: Optional[str] = None, public_only: bool = True) -> List[ProjectTemplate]:
        """获取项目模板列表"""
        try:
            from app.models.audio_editor import ProjectTemplateModel
            
            query = db.query(ProjectTemplateModel)
            
            if public_only:
                query = query.filter(ProjectTemplateModel.is_public == True)
            
            if category:
                query = query.filter(ProjectTemplateModel.category == category)
            
            templates = query.order_by(desc(ProjectTemplateModel.usage_count)).all()
            return [ProjectTemplate.from_orm(t) for t in templates]
            
        except Exception as e:
            logger.error(f"Error getting templates: {str(e)}")
            return []
    
    def use_template(self, db: Session, template_id: int) -> Optional[ProjectTemplate]:
        """使用模板（增加使用计数）"""
        try:
            from app.models.audio_editor import ProjectTemplateModel
            
            template = db.query(ProjectTemplateModel).filter(ProjectTemplateModel.id == template_id).first()
            if not template:
                return None
            
            template.usage_count += 1
            template.updated_at = datetime.now()
            db.commit()
            db.refresh(template)
            
            return ProjectTemplate.from_orm(template)
            
        except Exception as e:
            logger.error(f"Error using template {template_id}: {str(e)}")
            db.rollback()
            return None
    
    # ==================== 版本控制管理 ====================
    
    def save_edit_history(self, db: Session, project_id: int, operation_type: str, 
                         operation_data: Dict[str, Any], snapshot_data: Optional[Dict[str, Any]] = None,
                         user_id: Optional[int] = None) -> EditHistory:
        """保存编辑历史"""
        try:
            from app.models.audio_editor import EditHistoryModel
            
            # 获取当前项目的最新版本号
            latest_version = db.query(EditHistoryModel)\
                .filter(EditHistoryModel.project_id == project_id)\
                .order_by(desc(EditHistoryModel.version_number))\
                .first()
            
            version_number = (latest_version.version_number + 1) if latest_version else 1
            
            history = EditHistoryModel(
                project_id=project_id,
                version_number=version_number,
                operation_type=operation_type,
                operation_data=operation_data,
                snapshot_data=snapshot_data,
                user_id=user_id,
                created_at=datetime.now()
            )
            
            db.add(history)
            db.commit()
            db.refresh(history)
            
            logger.info(f"Saved edit history for project {project_id}, version {version_number}")
            return EditHistory.from_orm(history)
            
        except Exception as e:
            logger.error(f"Error saving edit history: {str(e)}")
            db.rollback()
            raise
    
    def get_edit_history(self, db: Session, project_id: int, limit: int = 50) -> List[EditHistory]:
        """获取编辑历史"""
        try:
            from app.models.audio_editor import EditHistoryModel
            
            histories = db.query(EditHistoryModel)\
                .filter(EditHistoryModel.project_id == project_id)\
                .order_by(desc(EditHistoryModel.version_number))\
                .limit(limit).all()
            
            return [EditHistory.from_orm(h) for h in histories]
            
        except Exception as e:
            logger.error(f"Error getting edit history for project {project_id}: {str(e)}")
            return []
    
    def revert_to_version(self, db: Session, project_id: int, version_number: int) -> Optional[Dict[str, Any]]:
        """回滚到指定版本"""
        try:
            from app.models.audio_editor import EditHistoryModel
            
            history = db.query(EditHistoryModel)\
                .filter(and_(
                    EditHistoryModel.project_id == project_id,
                    EditHistoryModel.version_number == version_number
                )).first()
            
            if not history or not history.snapshot_data:
                return None
            
            # 创建回滚操作记录
            self.save_edit_history(
                db, project_id, "revert",
                {"reverted_to_version": version_number},
                history.snapshot_data
            )
            
            return history.snapshot_data
            
        except Exception as e:
            logger.error(f"Error reverting project {project_id} to version {version_number}: {str(e)}")
            return None
    
    # ==================== 导出任务管理 ====================
    
    def create_export_task(self, db: Session, task_data: ExportTaskCreate, user_id: Optional[int] = None) -> ExportTask:
        """创建导出任务"""
        try:
            from app.models.audio_editor import ExportTaskModel
            
            task = ExportTaskModel(
                project_id=task_data.project_id,
                export_format=task_data.export_format.value,
                export_settings=task_data.export_settings.dict(),
                status="pending",
                progress=0,
                user_id=user_id,
                created_at=datetime.now()
            )
            
            db.add(task)
            db.commit()
            db.refresh(task)
            
            logger.info(f"Created export task: {task.id}")
            return ExportTask.from_orm(task)
            
        except Exception as e:
            logger.error(f"Error creating export task: {str(e)}")
            db.rollback()
            raise
    
    def process_export_task(self, db: Session, task_id: int) -> bool:
        """处理导出任务"""
        try:
            from app.models.audio_editor import ExportTaskModel, AudioProjectModel
            
            task = db.query(ExportTaskModel).filter(ExportTaskModel.id == task_id).first()
            if not task:
                return False
            
            # 更新状态为处理中
            task.status = "processing"
            task.progress = 0
            db.commit()
            
            # 获取项目信息
            project = db.query(AudioProjectModel).filter(AudioProjectModel.id == task.project_id).first()
            if not project:
                task.status = "failed"
                task.error_message = "Project not found"
                db.commit()
                return False
            
            # 生成输出文件路径
            output_filename = f"project_{task.project_id}_{task_id}.{task.export_format}"
            output_path = os.path.join(self.export_dir, output_filename)
            
            # 模拟导出处理过程
            settings = task.export_settings
            
            # 更新进度
            for progress in [25, 50, 75, 90]:
                task.progress = progress
                db.commit()
                # 这里应该是实际的音频处理逻辑
            
            # 模拟生成文件
            with open(output_path, 'wb') as f:
                f.write(b"Mock audio file content")
            
            # 完成任务
            file_size = os.path.getsize(output_path)
            task.status = "completed"
            task.progress = 100
            task.file_path = output_path
            task.file_size = file_size
            task.completed_at = datetime.now()
            db.commit()
            
            logger.info(f"Export task {task_id} completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error processing export task {task_id}: {str(e)}")
            # 更新任务状态为失败
            try:
                from app.models.audio_editor import ExportTaskModel
                task = db.query(ExportTaskModel).filter(ExportTaskModel.id == task_id).first()
                if task:
                    task.status = "failed"
                    task.error_message = str(e)
                    db.commit()
            except:
                pass
            return False
    
    def get_export_tasks(self, db: Session, project_id: Optional[int] = None, user_id: Optional[int] = None) -> List[ExportTask]:
        """获取导出任务列表"""
        try:
            from app.models.audio_editor import ExportTaskModel
            
            query = db.query(ExportTaskModel)
            
            if project_id:
                query = query.filter(ExportTaskModel.project_id == project_id)
            
            if user_id:
                query = query.filter(ExportTaskModel.user_id == user_id)
            
            tasks = query.order_by(desc(ExportTaskModel.created_at)).all()
            return [ExportTask.from_orm(t) for t in tasks]
            
        except Exception as e:
            logger.error(f"Error getting export tasks: {str(e)}")
            return []
    
    # ==================== 项目分享管理 ====================
    
    def create_project_share(self, db: Session, share_data: ProjectShareCreate, user_id: Optional[int] = None) -> ProjectShare:
        """创建项目分享"""
        try:
            from app.models.audio_editor import ProjectShareModel
            
            # 生成分享令牌
            share_token = secrets.token_urlsafe(32)
            
            share = ProjectShareModel(
                project_id=share_data.project_id,
                share_token=share_token,
                share_type=share_data.share_type.value,
                password=share_data.password,
                expires_at=share_data.expires_at,
                created_by=user_id,
                created_at=datetime.now()
            )
            
            db.add(share)
            db.commit()
            db.refresh(share)
            
            logger.info(f"Created project share: {share.id}")
            return ProjectShare.from_orm(share)
            
        except Exception as e:
            logger.error(f"Error creating project share: {str(e)}")
            db.rollback()
            raise
    
    def get_project_share(self, db: Session, share_token: str) -> Optional[ProjectShare]:
        """通过分享令牌获取分享信息"""
        try:
            from app.models.audio_editor import ProjectShareModel
            
            share = db.query(ProjectShareModel)\
                .filter(and_(
                    ProjectShareModel.share_token == share_token,
                    ProjectShareModel.is_active == True
                )).first()
            
            if not share:
                return None
            
            # 检查是否过期
            if share.expires_at and share.expires_at < datetime.now():
                return None
            
            # 增加访问计数
            share.access_count += 1
            db.commit()
            
            return ProjectShare.from_orm(share)
            
        except Exception as e:
            logger.error(f"Error getting project share with token {share_token}: {str(e)}")
            return None
    
    def update_project_share(self, db: Session, share_id: int, update_data: ProjectShareUpdate) -> Optional[ProjectShare]:
        """更新项目分享"""
        try:
            from app.models.audio_editor import ProjectShareModel
            
            share = db.query(ProjectShareModel).filter(ProjectShareModel.id == share_id).first()
            if not share:
                return None
            
            update_dict = update_data.dict(exclude_unset=True)
            for field, value in update_dict.items():
                if hasattr(share, field):
                    if field == 'share_type' and value:
                        setattr(share, field, value.value)
                    else:
                        setattr(share, field, value)
            
            db.commit()
            db.refresh(share)
            
            return ProjectShare.from_orm(share)
            
        except Exception as e:
            logger.error(f"Error updating project share {share_id}: {str(e)}")
            db.rollback()
            return None
    
    # ==================== 云端同步管理 ====================
    
    def get_sync_status(self, db: Session, project_id: int) -> Optional[SyncStatusResponse]:
        """获取项目同步状态"""
        try:
            from app.models.audio_editor import SyncStatusModel
            
            sync_status = db.query(SyncStatusModel)\
                .filter(SyncStatusModel.project_id == project_id).first()
            
            if not sync_status:
                # 创建默认同步状态
                sync_status = SyncStatusModel(
                    project_id=project_id,
                    local_version=1,
                    cloud_version=0,
                    sync_status="local",
                    created_at=datetime.now(),
                    updated_at=datetime.now()
                )
                db.add(sync_status)
                db.commit()
                db.refresh(sync_status)
            
            return SyncStatusResponse.from_orm(sync_status)
            
        except Exception as e:
            logger.error(f"Error getting sync status for project {project_id}: {str(e)}")
            return None
    
    def sync_to_cloud(self, db: Session, project_id: int) -> bool:
        """同步项目到云端"""
        try:
            from app.models.audio_editor import SyncStatusModel, AudioProjectModel
            
            # 获取项目和同步状态
            project = db.query(AudioProjectModel).filter(AudioProjectModel.id == project_id).first()
            sync_status = db.query(SyncStatusModel).filter(SyncStatusModel.project_id == project_id).first()
            
            if not project:
                return False
            
            if not sync_status:
                sync_status = SyncStatusModel(
                    project_id=project_id,
                    local_version=1,
                    cloud_version=0,
                    sync_status="local",
                    created_at=datetime.now(),
                    updated_at=datetime.now()
                )
                db.add(sync_status)
            
            # 更新同步状态
            sync_status.sync_status = "syncing"
            sync_status.updated_at = datetime.now()
            db.commit()
            
            # 模拟云端同步过程
            cloud_path = f"{self.cloud_storage_dir}/project_{project_id}.json"
            project_data = {
                "id": project.id,
                "name": project.name,
                "description": project.description,
                "sync_time": datetime.now().isoformat()
            }
            
            with open(cloud_path, 'w', encoding='utf-8') as f:
                json.dump(project_data, f, ensure_ascii=False, indent=2)
            
            # 完成同步
            sync_status.sync_status = "synced"
            sync_status.cloud_version = sync_status.local_version
            sync_status.last_sync_at = datetime.now()
            sync_status.cloud_storage_path = cloud_path
            sync_status.sync_error = None
            db.commit()
            
            logger.info(f"Project {project_id} synced to cloud successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error syncing project {project_id} to cloud: {str(e)}")
            # 更新错误状态
            try:
                from app.models.audio_editor import SyncStatusModel
                sync_status = db.query(SyncStatusModel).filter(SyncStatusModel.project_id == project_id).first()
                if sync_status:
                    sync_status.sync_status = "error"
                    sync_status.sync_error = str(e)
                    sync_status.updated_at = datetime.now()
                    db.commit()
            except:
                pass
            return False
    
    # ==================== 批量操作 ====================
    
    def batch_export(self, db: Session, request: BatchExportRequest, user_id: Optional[int] = None) -> BatchExportResponse:
        """批量导出项目"""
        try:
            task_ids = []
            
            for project_id in request.project_ids:
                task_create = ExportTaskCreate(
                    project_id=project_id,
                    export_format=request.export_format,
                    export_settings=request.export_settings
                )
                
                task = self.create_export_task(db, task_create, user_id)
                task_ids.append(task.id)
            
            # 估算处理时间（每个项目约30秒）
            estimated_time = len(request.project_ids) * 30
            
            return BatchExportResponse(
                task_ids=task_ids,
                total_projects=len(request.project_ids),
                estimated_time=estimated_time
            )
            
        except Exception as e:
            logger.error(f"Error in batch export: {str(e)}")
            raise 