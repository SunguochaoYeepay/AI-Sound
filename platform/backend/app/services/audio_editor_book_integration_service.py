"""
音频编辑器与书籍资源库集成服务
支持编辑器项目关联书籍章节，并从资源库选择导入对话音、环境音、JSON配置
"""
import logging
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path
from sqlalchemy.orm import Session

from ..models import Book, BookChapter, NovelProject, AudioFile, EnvironmentSound
from ..models.environment_generation import EnvironmentGenerationSession, EnvironmentTrackConfig
from ..services.environment_to_editor_converter import EnvironmentToEditorConverter

logger = logging.getLogger(__name__)


class AudioEditorBookIntegrationService:
    """音频编辑器与书籍资源库集成服务"""
    
    def __init__(self, db: Session):
        self.db = db
        self.converter = EnvironmentToEditorConverter()
    
    def get_available_books(self) -> List[Dict[str, Any]]:
        """获取可用的书籍列表"""
        try:
            books = self.db.query(Book).filter(Book.status != 'archived').all()
            
            result = []
            for book in books:
                # 统计相关资源
                projects_count = self.db.query(NovelProject).filter(NovelProject.book_id == book.id).count()
                chapters_count = self.db.query(BookChapter).filter(BookChapter.book_id == book.id).count()
                
                book_info = {
                    'id': book.id,
                    'title': book.title,
                    'author': book.author,
                    'description': book.description,
                    'status': book.status,
                    'word_count': book.word_count,
                    'chapter_count': book.chapter_count,
                    'character_count': book.get_character_count(),
                    'projects_count': projects_count,
                    'chapters_count': chapters_count,
                    'created_at': book.created_at.isoformat() if book.created_at else None,
                    'tags': book.get_tags()
                }
                result.append(book_info)
            
            # 按创建时间排序
            result.sort(key=lambda x: x['created_at'] or '', reverse=True)
            
            logger.info(f"获取到 {len(result)} 本可用书籍")
            return result
            
        except Exception as e:
            logger.error(f"获取书籍列表失败: {e}")
            return []
    
    def get_book_chapters(self, book_id: int) -> List[Dict[str, Any]]:
        """获取书籍的章节列表"""
        try:
            book = self.db.query(Book).filter(Book.id == book_id).first()
            if not book:
                return []
            
            chapters = self.db.query(BookChapter).filter(
                BookChapter.book_id == book_id
            ).order_by(BookChapter.chapter_number).all()
            
            result = []
            for chapter in chapters:
                # 统计章节资源
                projects = self.db.query(NovelProject).filter(NovelProject.book_id == book_id).all()
                
                audio_count = 0
                env_config_count = 0
                
                for project in projects:
                    # 统计对话音频（通过chapter关联）
                    chapter_audio = self.db.query(AudioFile).filter(
                        AudioFile.project_id == project.id,
                        AudioFile.segment_id.like(f"%chapter_{chapter.chapter_number}%")
                    ).count()
                    audio_count += chapter_audio
                    
                    # 统计环境音配置
                    env_sessions = self.db.query(EnvironmentGenerationSession).filter(
                        EnvironmentGenerationSession.project_id == project.id,
                        EnvironmentGenerationSession.chapter_id == f"chapter_{chapter.chapter_number}"
                    ).count()
                    env_config_count += env_sessions
                
                chapter_info = {
                    'id': chapter.id,
                    'chapter_number': chapter.chapter_number,
                    'title': chapter.title,
                    'content_preview': chapter.content[:200] + '...' if chapter.content and len(chapter.content) > 200 else chapter.content,
                    'word_count': len(chapter.content) if chapter.content else 0,
                    'status': chapter.status,
                    'audio_files_count': audio_count,
                    'environment_configs_count': env_config_count,
                    'has_resources': audio_count > 0 or env_config_count > 0,
                    'created_at': chapter.created_at.isoformat() if chapter.created_at else None
                }
                result.append(chapter_info)
            
            logger.info(f"获取书籍 {book_id} 的 {len(result)} 个章节")
            return result
            
        except Exception as e:
            logger.error(f"获取书籍章节失败: {e}")
            return []
    
    def get_chapter_resources(self, book_id: int, chapter_ids: List[int]) -> Dict[str, Any]:
        """获取指定章节的所有资源"""
        try:
            book = self.db.query(Book).filter(Book.id == book_id).first()
            if not book:
                return {'error': '书籍不存在'}
            
            chapters = self.db.query(BookChapter).filter(
                BookChapter.id.in_(chapter_ids),
                BookChapter.book_id == book_id
            ).all()
            
            if not chapters:
                return {'error': '章节不存在'}
            
            # 获取相关项目
            projects = self.db.query(NovelProject).filter(NovelProject.book_id == book_id).all()
            
            # 获取对话音频（按章节过滤）
            dialogue_audio = []
            environment_configs = []
            
            for chapter in chapters:
                chapter_number = chapter.chapter_number
                
                for project in projects:
                    # 获取该章节的对话音频
                    audio_files = self.db.query(AudioFile).filter(
                        AudioFile.project_id == project.id,
                        AudioFile.segment_id.like(f"%chapter_{chapter_number}%")
                    ).all()
                    
                    for audio in audio_files:
                        dialogue_audio.append({
                            'id': audio.id,
                            'filename': audio.filename,
                            'original_name': audio.original_name,
                            'project_id': project.id,
                            'project_name': project.name,
                            'chapter_id': chapter.id,
                            'chapter_number': chapter_number,
                            'chapter_title': chapter.title,
                            'segment_id': audio.segment_id,
                            'type': audio.type,
                            'duration': audio.duration,
                            'file_size': audio.file_size,
                            'sample_rate': audio.sample_rate,
                            'channels': audio.channels,
                            'file_path': audio.file_path,
                            'created_at': audio.created_at.isoformat() if audio.created_at else None
                        })
                    
                    # 获取该章节的环境音配置
                    env_sessions = self.db.query(EnvironmentGenerationSession).filter(
                        EnvironmentGenerationSession.project_id == project.id,
                        EnvironmentGenerationSession.chapter_id == f"chapter_{chapter_number}",
                        EnvironmentGenerationSession.session_status == 'completed'
                    ).all()
                    
                    for session in env_sessions:
                        if session.persistence_data:
                            track_count = len(session.persistence_data.get('environment_tracks', []))
                            total_duration = sum(
                                track.get('duration', 0) 
                                for track in session.persistence_data.get('environment_tracks', [])
                            )
                            
                            environment_configs.append({
                                'session_id': session.id,
                                'project_id': project.id,
                                'project_name': project.name,
                                'chapter_id': chapter.id,
                                'chapter_number': chapter_number,
                                'chapter_title': chapter.title,
                                'config_data': session.persistence_data,
                                'config_summary': session.persistence_summary,
                                'track_count': track_count,
                                'total_duration': total_duration,
                                'created_at': session.persistence_timestamp.isoformat() if session.persistence_timestamp else None
                            })
            
            # 获取通用环境音（不特定于章节）
            environment_audio = self.db.query(EnvironmentSound).filter(
                EnvironmentSound.name.contains(book.title[:10])  # 简单关联
            ).all()
            
            environment_audio_list = []
            for env_sound in environment_audio:
                environment_audio_list.append({
                    'id': env_sound.id,
                    'name': env_sound.name,
                    'description': env_sound.description,
                    'file_path': env_sound.file_path,
                    'duration': env_sound.duration,
                    'category': env_sound.category,
                    'tags': env_sound.tags,
                    'volume_level': env_sound.volume_level,
                    'fade_in_duration': env_sound.fade_in_duration,
                    'fade_out_duration': env_sound.fade_out_duration,
                    'loop_enabled': env_sound.loop_enabled,
                    'status': env_sound.status,
                    'created_at': env_sound.created_at.isoformat() if env_sound.created_at else None
                })
            
            # 计算总时长
            total_dialogue_duration = sum(audio.get('duration', 0) for audio in dialogue_audio)
            total_environment_duration = sum(config.get('total_duration', 0) for config in environment_configs)
            
            result = {
                'book': {
                    'id': book.id,
                    'title': book.title,
                    'author': book.author,
                    'description': book.description
                },
                'selected_chapters': [{
                    'id': ch.id,
                    'chapter_number': ch.chapter_number,
                    'title': ch.title,
                    'word_count': len(ch.content) if ch.content else 0
                } for ch in chapters],
                'dialogue_audio': dialogue_audio,
                'environment_audio': environment_audio_list,
                'environment_configs': environment_configs,
                'resource_summary': {
                    'chapters_count': len(chapters),
                    'dialogue_count': len(dialogue_audio),
                    'environment_count': len(environment_audio_list),
                    'config_count': len(environment_configs),
                    'total_dialogue_duration': total_dialogue_duration,
                    'total_environment_duration': total_environment_duration,
                    'estimated_total_duration': total_dialogue_duration + total_environment_duration
                }
            }
            
            logger.info(f"获取章节资源完成: {result['resource_summary']}")
            return result
            
        except Exception as e:
            logger.error(f"获取章节资源失败: {e}")
            return {'error': str(e)}
    
    def create_editor_project_with_chapters(self, 
                                          project_name: str,
                                          book_id: int,
                                          chapter_ids: List[int],
                                          selected_resources: Dict[str, List[int]] = None) -> Dict[str, Any]:
        """
        创建关联书籍章节的编辑器项目
        
        Args:
            project_name: 项目名称
            book_id: 关联的书籍ID
            chapter_ids: 选中的章节ID列表
            selected_resources: 选中的资源 {'dialogue_audio': [id1, id2], 'environment_configs': [id1]}
        """
        try:
            book = self.db.query(Book).filter(Book.id == book_id).first()
            if not book:
                return {'success': False, 'error': '书籍不存在'}
            
            chapters = self.db.query(BookChapter).filter(
                BookChapter.id.in_(chapter_ids),
                BookChapter.book_id == book_id
            ).all()
            
            if not chapters:
                return {'success': False, 'error': '章节不存在'}
            
            # 生成项目ID
            import uuid
            project_id = f"project_{int(datetime.now().timestamp())}_{uuid.uuid4().hex[:8]}"
            timestamp = datetime.now().isoformat()
            
            # 构建章节摘要
            chapters_summary = [f"第{ch.chapter_number}章 {ch.title}" for ch in chapters]
            chapters_description = "、".join(chapters_summary[:3])
            if len(chapters_summary) > 3:
                chapters_description += f"等{len(chapters_summary)}个章节"
            
            # 构建基础项目信息
            project_info = {
                "id": project_id,
                "title": project_name,
                "description": f"基于《{book.title}》的{chapters_description}创建",
                "author": book.author or "AI-Sound",
                "totalDuration": 0.0,  # 将根据导入的音频计算
                "sampleRate": 44100,
                "channels": 2,
                "bitDepth": 16,
                "exportFormat": "wav",
                "createdAt": timestamp,
                "version": "1.0"
            }
            
            # 构建默认轨道
            tracks = [
                {
                    "id": "track_dialogue",
                    "name": "角色对话",
                    "type": "dialogue",
                    "volume": 1.0,
                    "muted": False,
                    "solo": False,
                    "color": "#3498db",
                    "order": 1,
                    "clips": []
                },
                {
                    "id": "track_environment",
                    "name": "环境音效",
                    "type": "environment",
                    "volume": 0.8,
                    "muted": False,
                    "solo": False,
                    "color": "#27ae60",
                    "order": 2,
                    "clips": []
                },
                {
                    "id": "track_background",
                    "name": "背景音乐",
                    "type": "background",
                    "volume": 0.5,
                    "muted": False,
                    "solo": False,
                    "color": "#e74c3c",
                    "order": 3,
                    "clips": []
                }
            ]
            
            # 导入选中的资源
            total_duration = 0.0
            markers = []
            chapter_timeline = {}  # 记录每个章节在时间轴上的位置
            
            if selected_resources:
                # 按章节顺序组织对话音频
                if 'dialogue_audio' in selected_resources:
                    dialogue_track = tracks[0]  # 对话轨道
                    current_time = 0.0
                    
                    # 按章节号排序
                    chapter_audio_map = {}
                    for audio_id in selected_resources['dialogue_audio']:
                        audio_file = self.db.query(AudioFile).filter(AudioFile.id == audio_id).first()
                        if audio_file:
                            # 从segment_id提取章节号
                            chapter_num = self._extract_chapter_number(audio_file.segment_id)
                            if chapter_num not in chapter_audio_map:
                                chapter_audio_map[chapter_num] = []
                            chapter_audio_map[chapter_num].append(audio_file)
                    
                    # 按章节顺序添加音频
                    for chapter in sorted(chapters, key=lambda x: x.chapter_number):
                        chapter_start_time = current_time
                        chapter_timeline[chapter.chapter_number] = {
                            'start_time': chapter_start_time,
                            'title': chapter.title
                        }
                        
                        # 添加章节标记
                        markers.append({
                            "id": f"marker_chapter_{chapter.chapter_number}",
                            "time": chapter_start_time,
                            "label": f"第{chapter.chapter_number}章: {chapter.title}",
                            "description": f"章节开始",
                            "color": "#f39c12"
                        })
                        
                        # 添加该章节的音频
                        chapter_audio_files = chapter_audio_map.get(chapter.chapter_number, [])
                        for audio_file in chapter_audio_files:
                            clip = {
                                "id": f"clip_dialogue_{audio_file.id}_{uuid.uuid4().hex[:8]}",
                                "fileId": str(audio_file.id),
                                "filename": audio_file.original_name or audio_file.filename,
                                "startTime": current_time,
                                "duration": audio_file.duration or 0,
                                "volume": 1.0,
                                "offset": 0.0,
                                "fadeIn": 0.1,
                                "fadeOut": 0.1,
                                "audioFilePath": audio_file.file_path,
                                "_chapterInfo": {
                                    "chapter_number": chapter.chapter_number,
                                    "chapter_title": chapter.title
                                }
                            }
                            dialogue_track["clips"].append(clip)
                            current_time += audio_file.duration or 0
                        
                        # 记录章节结束时间
                        chapter_timeline[chapter.chapter_number]['end_time'] = current_time
                        chapter_timeline[chapter.chapter_number]['duration'] = current_time - chapter_start_time
                    
                    total_duration = max(total_duration, current_time)
                
                # 导入环境音配置（覆盖到对话音频时间轴上）
                if 'environment_configs' in selected_resources:
                    environment_track = tracks[1]  # 环境音轨道
                    
                    for session_id in selected_resources['environment_configs']:
                        session = self.db.query(EnvironmentGenerationSession).filter(
                            EnvironmentGenerationSession.id == session_id
                        ).first()
                        
                        if session and session.persistence_data:
                            # 获取章节号
                            chapter_num = self._extract_chapter_number(session.chapter_id)
                            chapter_info = chapter_timeline.get(chapter_num)
                            
                            if chapter_info:
                                # 使用转换器转换环境音配置
                                conversion_result = self.converter.convert_environment_config_to_editor_project(
                                    session.persistence_data,
                                    project_name=f"{project_name}_环境音_第{chapter_num}章"
                                )
                                
                                if conversion_result['success']:
                                    # 调整环境音时间到章节时间轴
                                    env_clips = conversion_result['editor_project']['tracks'][0]['clips']
                                    for clip in env_clips:
                                        # 将环境音时间偏移到章节开始时间
                                        clip['startTime'] += chapter_info['start_time']
                                        clip['_chapterInfo'] = {
                                            "chapter_number": chapter_num,
                                            "chapter_title": chapter_info['title']
                                        }
                                    
                                    environment_track["clips"].extend(env_clips)
                                    
                                    # 调整标记点时间
                                    env_markers = conversion_result['editor_project']['markers']
                                    for marker in env_markers:
                                        marker['time'] += chapter_info['start_time']
                                        marker['label'] = f"第{chapter_num}章 {marker['label']}"
                                    
                                    markers.extend(env_markers)
            
            # 更新项目总时长
            project_info["totalDuration"] = total_duration
            
            # 构建完整项目数据
            editor_project = {
                "project": project_info,
                "tracks": tracks,
                "markers": markers,
                # 扩展字段：保存书籍章节关联信息
                "_bookAssociation": {
                    "book_id": book_id,
                    "book_title": book.title,
                    "book_author": book.author,
                    "chapter_ids": chapter_ids,
                    "chapters": [{
                        'id': ch.id,
                        'chapter_number': ch.chapter_number,
                        'title': ch.title
                    } for ch in chapters],
                    "chapter_timeline": chapter_timeline,
                    "association_timestamp": timestamp,
                    "selected_resources": selected_resources or {}
                }
            }
            
            # 保存项目文件到音频编辑器目录
            from ..api.v1.sound_editor import get_project_storage_path
            storage_path = get_project_storage_path()
            project_file = storage_path / f"{project_id}.json"
            
            with open(project_file, 'w', encoding='utf-8') as f:
                json.dump(editor_project, f, indent=2, ensure_ascii=False)
            
            logger.info(f"创建关联章节的编辑器项目成功: {project_name} -> {project_id}")
            
            return {
                'success': True,
                'project_id': project_id,
                'editor_project': editor_project,
                'resource_summary': {
                    'book_title': book.title,
                    'chapters_count': len(chapters),
                    'total_duration': total_duration,
                    'imported_dialogue': len(selected_resources.get('dialogue_audio', [])) if selected_resources else 0,
                    'imported_environment_configs': len(selected_resources.get('environment_configs', [])) if selected_resources else 0,
                    'markers_count': len(markers)
                },
                'message': f'项目创建成功，已关联《{book.title}》的{len(chapters)}个章节'
            }
            
        except Exception as e:
            logger.error(f"创建关联章节的编辑器项目失败: {e}")
            return {'success': False, 'error': str(e)}
    
    def _extract_chapter_number(self, segment_id_or_chapter_id: str) -> int:
        """从segment_id或chapter_id中提取章节号"""
        try:
            if 'chapter_' in segment_id_or_chapter_id:
                # 格式: chapter_1, segment_chapter_1_xxx
                parts = segment_id_or_chapter_id.split('chapter_')
                if len(parts) > 1:
                    number_part = parts[1].split('_')[0]
                    return int(number_part)
            return 0
        except:
            return 0