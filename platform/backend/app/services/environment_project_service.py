"""
环境音项目服务
封装环境音项目的CRUD操作
"""

import logging
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from datetime import datetime

from app.models.environment_generation import EnvironmentProject
from app.models.novel_project import NovelProject

logger = logging.getLogger(__name__)


class EnvironmentProjectService:
	"""环境音项目服务"""
	
	def __init__(self, db: Session):
		self.db = db
	
	def get_by_book_id(self, book_id: int) -> Optional[EnvironmentProject]:
		"""根据书籍ID获取环境音项目"""
		return self.db.query(EnvironmentProject).filter(
			EnvironmentProject.book_id == book_id
		).first()
	
	def get_by_id(self, project_id: int) -> Optional[EnvironmentProject]:
		"""根据环境音项目ID获取项目"""
		return self.db.query(EnvironmentProject).filter(
			EnvironmentProject.id == project_id
		).first()
	
	def get_by_project_id(self, project_id: int) -> Optional[EnvironmentProject]:
		"""根据项目ID获取环境音项目"""
		return self.get_by_id(project_id)
	
	def create_or_update(
		self, 
		book_id: int, 
		analysis_result: Dict[str, Any],
		analysis_stats: Dict[str, Any],
		analysis_options: Dict[str, Any] = None
	) -> EnvironmentProject:
		"""创建或更新环境音项目"""
		
		# 检查是否强制重新分析
		force_reanalyze = analysis_options and analysis_options.get('force_reanalyze', False)
		existing_project_id = analysis_options and analysis_options.get('existing_project_id')
		
		logger.info(f"create_or_update - force_reanalyze: {force_reanalyze}, existing_project_id: {existing_project_id}")
		logger.info(f"create_or_update - analysis_options: {analysis_options}")
		
		# 🚨 修复：优先按指定的项目ID查找，否则按书籍ID查找
		env_project = None
		if existing_project_id:
			env_project = self.get_by_id(existing_project_id)
			logger.info(f"按指定项目ID查找: {existing_project_id}, 找到: {env_project.id if env_project else None}")
		
		if not env_project:
			env_project = self.get_by_book_id(book_id)
			logger.info(f"按书籍ID查找: {book_id}, 找到: {env_project.id if env_project else None}")
		
		if env_project and force_reanalyze:
			# 🚨 修复：强制重新分析时，只清理子数据，保留项目本身
			logger.info(f"强制重新分析：清理项目 {env_project.id} 的子数据，保留项目本身")
			
			# 删除相关的环境音会话
			from app.models.environment_generation import (
				EnvironmentGenerationSession,
				EnvironmentTrackConfig,
				EnvironmentAudioMixingJob,
				EnvironmentGenerationLog
			)
			
			sessions = self.db.query(EnvironmentGenerationSession).filter(
				EnvironmentGenerationSession.project_id == env_project.id
			).all()
			
			for session in sessions:
				# 删除会话下的所有轨道配置
				tracks = self.db.query(EnvironmentTrackConfig).filter(
					EnvironmentTrackConfig.session_id == session.id
				).all()
				for track in tracks:
					self.db.delete(track)
				# 删除会话
				self.db.delete(session)
			
			# 删除相关的混合任务
			mixing_jobs = self.db.query(EnvironmentAudioMixingJob).filter(
				EnvironmentAudioMixingJob.project_id == env_project.id
			).all()
			for job in mixing_jobs:
				self.db.delete(job)
			
			# 删除相关的生成日志
			logs = self.db.query(EnvironmentGenerationLog).join(
				EnvironmentGenerationSession, EnvironmentGenerationLog.session_id == EnvironmentGenerationSession.id
			).filter(EnvironmentGenerationSession.project_id == env_project.id).all()
			for log in logs:
				self.db.delete(log)
			
			# 🚨 修复：不删除项目本身，只清理子数据
			# self.db.delete(env_project)  # 删除这行
			# self.db.commit()  # 删除这行
			
			# 🚨 修复：直接覆盖分析结果，保留项目ID
			env_project.analysis_result = analysis_result
			env_project.matching_result = {
				'analysis_stats': analysis_stats,
				'session_stage': 'analyzed'
			}
			env_project.analysis_options = analysis_options or {}
			env_project.updated_at = datetime.utcnow()
			
			self.db.commit()
			logger.info(f"项目 {env_project.id} 强制重新分析完成，项目ID保持不变")
			return env_project
		
		if env_project:
			# 更新现有项目 - 合并分析结果而不是覆盖
			existing_result = env_project.analysis_result or {}
			
			# 如果是多章节格式，合并章节数据
			if isinstance(analysis_result, dict) and not analysis_result.get('environment_tracks'):
				# 多章节格式，按章节ID合并
				for chapter_id, chapter_analysis in analysis_result.items():
					if isinstance(chapter_analysis, dict):
						if chapter_id not in existing_result:
							existing_result[chapter_id] = chapter_analysis
						else:
							# 合并环境轨道
							existing_tracks = existing_result[chapter_id].get('environment_tracks', [])
							new_tracks = chapter_analysis.get('environment_tracks', [])
							existing_result[chapter_id]['environment_tracks'] = existing_tracks + new_tracks
			else:
				# 单章节格式，合并环境轨道
				existing_tracks = existing_result.get('environment_tracks', [])
				new_tracks = analysis_result.get('environment_tracks', [])
				
				logger.info(f"合并逻辑 - 现有轨道数量: {len(existing_tracks)}, 新轨道数量: {len(new_tracks)}")
				logger.info(f"合并逻辑 - 现有segment_ids: {[t.get('segment_id') for t in existing_tracks]}")
				logger.info(f"合并逻辑 - 新segment_ids: {[t.get('segment_id') for t in new_tracks]}")
				
				# 🚨 修复：为新的轨道重新分配segment_id，避免与现有轨道冲突
				if existing_tracks and new_tracks:
					max_segment_id = max(track.get('segment_id', 0) for track in existing_tracks)
					logger.info(f"合并逻辑 - 最大现有segment_id: {max_segment_id}")
					for track in new_tracks:
						old_segment_id = track.get('segment_id', 1)
						track['segment_id'] = max_segment_id + old_segment_id
						logger.info(f"合并逻辑 - 重新分配segment_id: {old_segment_id} -> {track['segment_id']}")
				
				# 🚨 修复：确保合并到正确的字段
				if 'environment_tracks' not in existing_result:
					existing_result['environment_tracks'] = []
				
				# 合并前记录数量
				before_count = len(existing_result['environment_tracks'])
				existing_result['environment_tracks'].extend(new_tracks)
				after_count = len(existing_result['environment_tracks'])
				
				logger.info(f"合并逻辑 - 合并前轨道数量: {before_count}, 合并后轨道数量: {after_count}")
				logger.info(f"合并逻辑 - 最终segment_ids: {[t.get('segment_id') for t in existing_result['environment_tracks']]}")
			
			env_project.analysis_result = existing_result
			# 🚨 修复：手动标记JSON字段为已修改，确保SQLAlchemy能检测到变化
			from sqlalchemy.orm.attributes import flag_modified
			flag_modified(env_project, "analysis_result")
			
			# 更新统计信息 - 保留现有的matching_result，只更新analysis_stats
			if not env_project.matching_result:
				env_project.matching_result = {}
			
			existing_stats = env_project.matching_result.get('analysis_stats', {})
			if existing_stats:
				existing_stats['total_chapters'] = existing_stats.get('total_chapters', 0) + analysis_stats.get('total_chapters', 0)
				existing_stats['total_tracks'] = existing_stats.get('total_tracks', 0) + analysis_stats.get('total_tracks', 0)
			else:
				existing_stats = analysis_stats
			
			# 只更新analysis_stats，保留其他字段（如混音信息）
			env_project.matching_result['analysis_stats'] = existing_stats
			env_project.matching_result['session_stage'] = 'analyzed'
			env_project.analysis_options = analysis_options or {}
			env_project.updated_at = datetime.utcnow()
			
			logger.info(f"合并更新环境音项目: {env_project.id}")
		else:
			# 获取书籍信息
			from app.models.book import Book
			book = self.db.query(Book).filter(Book.id == book_id).first()
			
			if not book:
				raise ValueError(f"书籍 {book_id} 不存在")
			
			# 创建新项目
			env_project = EnvironmentProject(
				book_id=book_id,
				name=f"环境音分析_{book.title}",
				description=f"基于书籍 '{book.title}' 的环境音分析",
				status="analyzed",
				analysis_result=analysis_result,
				matching_result={
					'analysis_stats': analysis_stats,
					'session_stage': 'analyzed'
				},
				analysis_options=analysis_options or {},
				book_name=book.title,
				chapter_name="第1章"
			)
			
			self.db.add(env_project)
			logger.info(f"创建环境音项目: {book_id}")
		
		self.db.commit()
		self.db.refresh(env_project)
		return env_project
	
	def update_track_config(
        self, 
        project_id: int, 
        track_index: int, 
        track_config: Dict[str, Any]
        ) -> bool:
            """更新轨道配置"""
            
            env_project = self.get_by_id(project_id)
            if not env_project or not env_project.analysis_result:
                return False
            
            environment_tracks = env_project.analysis_result.get('environment_tracks', [])
            if track_index >= len(environment_tracks):
                return False
            
            # 更新轨道配置
            track = environment_tracks[track_index]
            track.update(track_config)
            track['user_confirmed'] = True
            
            # 更新项目
            env_project.analysis_result['environment_tracks'] = environment_tracks
            env_project.updated_at = datetime.utcnow()
            
            self.db.commit()
            logger.info(f"更新轨道配置: 项目{project_id}, 轨道{track_index}")
            return True
    
def delete_track(
    self, 
    project_id: int, 
    track_index: int
) -> bool:
    """删除轨道"""
    
    env_project = self.get_by_id(project_id)
    if not env_project or not env_project.analysis_result:
        return False
    
    environment_tracks = env_project.analysis_result.get('environment_tracks', [])
    if track_index >= len(environment_tracks):
        return False
    
    # 删除指定轨道
    environment_tracks.pop(track_index)
    
    # 更新项目
    env_project.analysis_result['environment_tracks'] = environment_tracks
    env_project.updated_at = datetime.utcnow()
    
    # 更新统计信息
    if env_project.matching_result and 'analysis_stats' in env_project.matching_result:
        stats = env_project.matching_result['analysis_stats']
        stats['total_tracks'] = max(0, stats.get('total_tracks', 0) - 1)
    
    self.db.commit()
    logger.info(f"删除轨道: 项目{project_id}, 轨道{track_index}")
    return True

def finalize_project(self, project_id: int) -> bool:
    """完成环境音项目"""
    
    env_project = self.get_by_project_id(project_id)
    if not env_project:
        return False
    
    env_project.status = "completed"
    env_project.matching_result['session_stage'] = 'completed'
    env_project.updated_at = datetime.utcnow()
    
    self.db.commit()
    logger.info(f"完成环境音项目: {project_id}")
    return True

def delete_by_book_id(self, book_id: int) -> bool:
    """删除环境音项目"""
    
    env_project = self.get_by_book_id(book_id)
    if not env_project:
        return False
    
    self.db.delete(env_project)
    self.db.commit()
    logger.info(f"删除环境音项目: {book_id}")
    return True
