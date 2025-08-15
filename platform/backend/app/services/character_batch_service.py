"""角色批量操作服务"""

from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, UploadFile
import logging
import os
import json
import csv
import io
from datetime import datetime
import asyncio
from concurrent.futures import ThreadPoolExecutor

from app.models.character import Character
from app.models import AnalysisResult
from app.schemas.character import CharacterCreate, CharacterUpdate
from app.utils import log_system_event
from app.services.character_management_service import CharacterManagementService

logger = logging.getLogger(__name__)

class CharacterBatchService:
    """角色批量操作服务类"""
    
    def __init__(self, db: Session):
        self.db = db
        self.crud_service = CharacterManagementService(db)
    
    def batch_update_characters(
        self, 
        character_ids: List[int], 
        update_data: CharacterUpdate
    ) -> Dict[str, Any]:
        """批量更新角色"""
        try:
            updated_characters = []
            failed_characters = []
            
            for character_id in character_ids:
                try:
                    result = self.crud_service.update_character(character_id, update_data)
                    if result["success"]:
                        updated_characters.append(result["data"])
                    else:
                        failed_characters.append({
                            "id": character_id,
                            "reason": result.get("message", "更新失败")
                        })
                except Exception as e:
                    failed_characters.append({
                        "id": character_id,
                        "reason": str(e)
                    })
            
            # 记录系统日志
            log_system_event(
                self.db,
                "characters_batch_updated",
                f"批量更新角色: 成功 {len(updated_characters)} 个，失败 {len(failed_characters)} 个",
                {
                    "updated_count": len(updated_characters),
                    "failed_count": len(failed_characters),
                    "character_ids": character_ids
                }
            )
            
            return {
                "success": True,
                "data": {
                    "updated_characters": updated_characters,
                    "failed_characters": failed_characters,
                    "summary": {
                        "total": len(character_ids),
                        "updated": len(updated_characters),
                        "failed": len(failed_characters)
                    }
                },
                "message": f"批量更新完成: 成功 {len(updated_characters)} 个，失败 {len(failed_characters)} 个"
            }
            
        except Exception as e:
            logger.error(f"批量更新角色失败: {str(e)}")
            raise HTTPException(status_code=500, detail=f"批量更新角色失败: {str(e)}")
    
    def batch_delete_characters(
        self, 
        character_ids: List[int], 
        force: bool = False
    ) -> Dict[str, Any]:
        """批量删除角色"""
        try:
            deleted_characters = []
            failed_characters = []
            
            for character_id in character_ids:
                try:
                    character = self.db.query(Character).filter(
                        Character.id == character_id
                    ).first()
                    
                    if not character:
                        failed_characters.append({
                            "id": character_id,
                            "reason": "角色不存在"
                        })
                        continue
                    
                    # 检查是否有关联文件
                    if not force and (character.reference_audio_path or character.latent_file_path):
                        failed_characters.append({
                            "id": character_id,
                            "name": character.name,
                            "reason": "角色有关联文件，需要强制删除"
                        })
                        continue
                    
                    # 删除关联文件
                    self._delete_character_files(character)
                    
                    # 删除数据库记录
                    character_name = character.name
                    self.db.delete(character)
                    
                    deleted_characters.append({
                        "id": character_id,
                        "name": character_name
                    })
                    
                except Exception as e:
                    failed_characters.append({
                        "id": character_id,
                        "reason": str(e)
                    })
            
            # 提交删除操作
            self.db.commit()
            
            # 记录系统日志
            log_system_event(
                self.db,
                "characters_batch_deleted",
                f"批量删除角色: 成功 {len(deleted_characters)} 个，失败 {len(failed_characters)} 个",
                {
                    "deleted_count": len(deleted_characters),
                    "failed_count": len(failed_characters),
                    "force": force
                }
            )
            
            return {
                "success": True,
                "data": {
                    "deleted_characters": deleted_characters,
                    "failed_characters": failed_characters,
                    "summary": {
                        "total": len(character_ids),
                        "deleted": len(deleted_characters),
                        "failed": len(failed_characters)
                    }
                },
                "message": f"批量删除完成: 成功 {len(deleted_characters)} 个，失败 {len(failed_characters)} 个"
            }
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"批量删除角色失败: {str(e)}")
            raise HTTPException(status_code=500, detail=f"批量删除角色失败: {str(e)}")
    
    def _delete_character_files(self, character: Character):
        """删除角色关联文件"""
        files_to_delete = [
            character.reference_audio_path,
            character.latent_file_path,
            character.avatar_path
        ]
        
        for file_path in files_to_delete:
            if file_path and os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except Exception as e:
                    logger.warning(f"删除文件失败: {file_path}, 错误: {str(e)}")
    
    def export_characters_list(
        self, 
        character_ids: Optional[List[int]] = None,
        format_type: str = "csv"
    ) -> Dict[str, Any]:
        """导出角色列表"""
        try:
            # 构建查询
            query = self.db.query(Character)
            if character_ids:
                query = query.filter(Character.id.in_(character_ids))
            
            characters = query.all()
            
            if format_type == "csv":
                return self._export_to_csv(characters)
            elif format_type == "json":
                return self._export_to_json(characters)
            else:
                raise HTTPException(status_code=400, detail="不支持的导出格式")
                
        except Exception as e:
            logger.error(f"导出角色列表失败: {str(e)}")
            raise HTTPException(status_code=500, detail=f"导出角色列表失败: {str(e)}")
    
    def _export_to_csv(self, characters: List[Character]) -> Dict[str, Any]:
        """导出为CSV格式"""
        output = io.StringIO()
        writer = csv.writer(output)
        
        # 写入表头
        headers = [
            "ID", "名称", "描述", "声音类型", "质量评分", "状态", 
            "标签", "书籍ID", "章节ID", "创建时间", "更新时间"
        ]
        writer.writerow(headers)
        
        # 写入数据
        for character in characters:
            tags = character.get_tags()
            tags_str = ", ".join(tags)
            
            row = [
                character.id,
                character.name,
                character.description or "",
                character.voice_type or "",
                character.quality_score or 0,
                character.status or "",
                tags_str,
                character.book_id or "",
                character.chapter_id or "",
                character.created_at.strftime("%Y-%m-%d %H:%M:%S") if character.created_at else "",
                character.updated_at.strftime("%Y-%m-%d %H:%M:%S") if character.updated_at else ""
            ]
            writer.writerow(row)
        
        csv_content = output.getvalue()
        output.close()
        
        return {
            "success": True,
            "data": {
                "content": csv_content,
                "filename": f"characters_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                "content_type": "text/csv",
                "count": len(characters)
            },
            "message": f"成功导出 {len(characters)} 个角色"
        }
    
    def _export_to_json(self, characters: List[Character]) -> Dict[str, Any]:
        """导出为JSON格式"""
        characters_data = [character.to_dict() for character in characters]
        
        export_data = {
            "export_time": datetime.now().isoformat(),
            "count": len(characters),
            "characters": characters_data
        }
        
        json_content = json.dumps(export_data, ensure_ascii=False, indent=2)
        
        return {
            "success": True,
            "data": {
                "content": json_content,
                "filename": f"characters_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                "content_type": "application/json",
                "count": len(characters)
            },
            "message": f"成功导出 {len(characters)} 个角色"
        }
    
    def batch_configure_characters(
        self, 
        character_configs: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """批量配置角色"""
        try:
            configured_characters = []
            failed_characters = []
            
            for config in character_configs:
                try:
                    character_id = config.get("character_id")
                    if not character_id:
                        failed_characters.append({
                            "config": config,
                            "reason": "缺少角色ID"
                        })
                        continue
                    
                    character = self.db.query(Character).filter(
                        Character.id == character_id
                    ).first()
                    
                    if not character:
                        failed_characters.append({
                            "character_id": character_id,
                            "reason": "角色不存在"
                        })
                        continue
                    
                    # 应用配置
                    self._apply_character_config(character, config)
                    configured_characters.append(character.to_dict())
                    
                except Exception as e:
                    failed_characters.append({
                        "config": config,
                        "reason": str(e)
                    })
            
            # 提交更改
            self.db.commit()
            
            # 记录系统日志
            log_system_event(
                self.db,
                "characters_batch_configured",
                f"批量配置角色: 成功 {len(configured_characters)} 个，失败 {len(failed_characters)} 个",
                {
                    "configured_count": len(configured_characters),
                    "failed_count": len(failed_characters)
                }
            )
            
            return {
                "success": True,
                "data": {
                    "configured_characters": configured_characters,
                    "failed_characters": failed_characters,
                    "summary": {
                        "total": len(character_configs),
                        "configured": len(configured_characters),
                        "failed": len(failed_characters)
                    }
                },
                "message": f"批量配置完成: 成功 {len(configured_characters)} 个，失败 {len(failed_characters)} 个"
            }
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"批量配置角色失败: {str(e)}")
            raise HTTPException(status_code=500, detail=f"批量配置角色失败: {str(e)}")
    
    def _apply_character_config(self, character: Character, config: Dict[str, Any]):
        """应用角色配置"""
        # 更新基本信息
        if "description" in config:
            character.description = config["description"]
        
        if "voice_type" in config:
            character.voice_type = config["voice_type"]
        
        if "quality_score" in config:
            character.quality_score = config["quality_score"]
        
        if "tags" in config:
            character.tags = json.dumps(config["tags"])
        
        # 更新文件路径
        if "reference_audio_path" in config:
            character.reference_audio_path = config["reference_audio_path"]
        
        if "latent_file_path" in config:
            character.latent_file_path = config["latent_file_path"]
        
        if "avatar_path" in config:
            character.avatar_path = config["avatar_path"]
        
        # 更新状态
        character.status = "configured"
        character.updated_at = datetime.now()
    
    def sync_characters_with_analysis(self, book_id: Optional[int] = None) -> Dict[str, Any]:
        """同步角色与分析结果"""
        try:
            # 获取分析结果
            analysis_query = self.db.query(AnalysisResult)
            if book_id:
                analysis_query = analysis_query.filter(AnalysisResult.book_id == book_id)
            
            analysis_results = analysis_query.all()
            
            synced_count = 0
            created_count = 0
            
            for analysis in analysis_results:
                if not analysis.characters_data:
                    continue
                
                characters_data = json.loads(analysis.characters_data)
                
                for char_data in characters_data:
                    char_name = char_data.get("name")
                    if not char_name:
                        continue
                    
                    # 查找现有角色
                    existing_character = self.db.query(Character).filter(
                        Character.name == char_name,
                        Character.book_id == analysis.book_id
                    ).first()
                    
                    if existing_character:
                        # 更新现有角色
                        existing_character.description = char_data.get("description", existing_character.description)
                        existing_character.voice_type = char_data.get("voice_type", existing_character.voice_type)
                        existing_character.updated_at = datetime.now()
                        synced_count += 1
                    else:
                        # 创建新角色
                        new_character = Character(
                            name=char_name,
                            description=char_data.get("description", ""),
                            voice_type=char_data.get("voice_type", "custom"),
                            book_id=analysis.book_id,
                            chapter_id=analysis.chapter_id,
                            status="unconfigured",
                            created_at=datetime.now(),
                            updated_at=datetime.now()
                        )
                        self.db.add(new_character)
                        created_count += 1
            
            self.db.commit()
            
            # 记录系统日志
            log_system_event(
                self.db,
                "characters_synced_with_analysis",
                f"同步角色与分析结果: 更新 {synced_count} 个，创建 {created_count} 个",
                {
                    "book_id": book_id,
                    "synced_count": synced_count,
                    "created_count": created_count
                }
            )
            
            return {
                "success": True,
                "data": {
                    "synced_count": synced_count,
                    "created_count": created_count,
                    "total_processed": synced_count + created_count
                },
                "message": f"同步完成: 更新 {synced_count} 个角色，创建 {created_count} 个新角色"
            }
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"同步角色失败: {str(e)}")
            raise HTTPException(status_code=500, detail=f"同步角色失败: {str(e)}")