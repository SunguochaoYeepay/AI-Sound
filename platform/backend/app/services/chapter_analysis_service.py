"""
章节分析服务
用于聚合和转换章节分析结果，为合成中心提供智能分析能力
"""

import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from ..models import NovelProject, BookChapter, AnalysisResult, VoiceProfile
from ..exceptions import ServiceException

logger = logging.getLogger(__name__)


class ChapterAnalysisService:
    """章节分析服务 - 复用书籍管理的章节分析能力"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def validate_analysis_result(self, analysis_data: Dict[str, Any]) -> bool:
        """验证分析结果格式"""
        try:
            required_fields = ['detected_characters', 'segments']
            for field in required_fields:
                if field not in analysis_data:
                    logger.warning(f"分析结果缺少必需字段: {field}")
                    return False
            
            # 检查角色数据格式
            characters = analysis_data.get('detected_characters', [])
            if not isinstance(characters, list):
                return False
            
            for char in characters:
                if not isinstance(char, dict) or 'name' not in char:
                    return False
            
            # 检查段落数据格式
            segments = analysis_data.get('segments', [])
            if not isinstance(segments, list):
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"验证分析结果失败: {str(e)}")
            return False
    
    def get_existing_analysis(self, chapter_id: int) -> Optional[Dict[str, Any]]:
        """获取单章节分析结果"""
        try:
            # 查找最新的已完成分析结果
            analysis_result = self.db.query(AnalysisResult).filter(
                and_(
                    AnalysisResult.chapter_id == chapter_id,
                    AnalysisResult.status == 'completed'
                )
            ).order_by(AnalysisResult.created_at.desc()).first()
            
            if not analysis_result:
                return None
            
            # 优先使用original_analysis中的数据，如果没有则使用直接字段
            if analysis_result.original_analysis:
                # 使用原始分析数据
                original_data = analysis_result.original_analysis
                if isinstance(original_data, str):
                    original_data = json.loads(original_data)
                
                analysis_data = {
                    'detected_characters': original_data.get('detected_characters', []),
                    'segments': original_data.get('segments', []),
                    'synthesis_plan': original_data.get('synthesis_plan', {}),
                    'final_config': analysis_result.final_config or {},
                    'processing_stats': {
                        'confidence_score': analysis_result.confidence_score or 0,
                        'processing_time': analysis_result.processing_time or 0,
                        'analysis_id': analysis_result.id,
                        'created_at': analysis_result.created_at.isoformat() if analysis_result.created_at else None
                    }
                }
            else:
                # 回退到直接字段
                analysis_data = {
                    'detected_characters': analysis_result.detected_characters or [],
                    'segments': analysis_result.dialogue_segments or [],
                    'synthesis_plan': analysis_result.synthesis_plan or {},
                    'final_config': analysis_result.final_config or {},
                    'processing_stats': {
                        'confidence_score': analysis_result.confidence_score or 0,
                        'processing_time': analysis_result.processing_time or 0,
                        'analysis_id': analysis_result.id,
                        'created_at': analysis_result.created_at.isoformat() if analysis_result.created_at else None
                    }
                }
            
            # 验证数据有效性
            if not self.validate_analysis_result(analysis_data):
                logger.warning(f"章节 {chapter_id} 的分析结果格式无效")
                return None
            
            return analysis_data
            
        except Exception as e:
            logger.error(f"获取章节 {chapter_id} 分析结果失败: {str(e)}")
            return None
    
    def batch_get_existing_analysis(self, chapter_ids: List[int]) -> Dict[int, Dict[str, Any]]:
        """批量获取章节分析结果"""
        try:
            results = {}
            
            # 批量查询所有章节的分析结果
            analysis_results = self.db.query(AnalysisResult).filter(
                and_(
                    AnalysisResult.chapter_id.in_(chapter_ids),
                    AnalysisResult.status == 'completed'
                )
            ).order_by(AnalysisResult.chapter_id, AnalysisResult.created_at.desc()).all()
            
            # 按章节分组，取最新的结果
            chapter_results = {}
            for result in analysis_results:
                if result.chapter_id not in chapter_results:
                    chapter_results[result.chapter_id] = result
            
            # 转换为统一格式
            for chapter_id, analysis_result in chapter_results.items():
                # 优先使用original_analysis中的数据
                if analysis_result.original_analysis:
                    original_data = analysis_result.original_analysis
                    if isinstance(original_data, str):
                        original_data = json.loads(original_data)
                    
                    analysis_data = {
                        'detected_characters': original_data.get('detected_characters', []),
                        'segments': original_data.get('segments', []),
                        'synthesis_plan': original_data.get('synthesis_plan', {}),
                        'final_config': analysis_result.final_config or {},
                        'processing_stats': {
                            'confidence_score': analysis_result.confidence_score or 0,
                            'processing_time': analysis_result.processing_time or 0,
                            'analysis_id': analysis_result.id,
                            'created_at': analysis_result.created_at.isoformat() if analysis_result.created_at else None
                        }
                    }
                else:
                    # 回退到直接字段
                    analysis_data = {
                        'detected_characters': analysis_result.detected_characters or [],
                        'segments': analysis_result.dialogue_segments or [],
                        'synthesis_plan': analysis_result.synthesis_plan or {},
                        'final_config': analysis_result.final_config or {},
                        'processing_stats': {
                            'confidence_score': analysis_result.confidence_score or 0,
                            'processing_time': analysis_result.processing_time or 0,
                            'analysis_id': analysis_result.id,
                            'created_at': analysis_result.created_at.isoformat() if analysis_result.created_at else None
                        }
                    }
                
                if self.validate_analysis_result(analysis_data):
                    results[chapter_id] = analysis_data
                else:
                    logger.warning(f"跳过章节 {chapter_id} 的无效分析结果")
            
            return results
            
        except Exception as e:
            logger.error(f"批量获取章节分析结果失败: {str(e)}")
            return {}
    
    def get_project_chapters(self, project_id: int) -> List[Dict[str, Any]]:
        """获取项目关联章节列表"""
        try:
            project = self.db.query(NovelProject).filter(NovelProject.id == project_id).first()
            if not project:
                raise ServiceException("项目不存在")
            
            if not project.book_id:
                raise ServiceException("项目没有关联书籍")
            
            # 获取书籍的所有章节
            chapters = self.db.query(BookChapter).filter(
                BookChapter.book_id == project.book_id
            ).order_by(BookChapter.chapter_number).all()
            
            if not chapters:
                raise ServiceException("项目关联的书籍没有章节")
            
            # 转换为字典格式
            chapter_list = []
            for chapter in chapters:
                chapter_list.append({
                    'id': chapter.id,
                    'chapter_number': chapter.chapter_number,
                    'chapter_title': chapter.chapter_title,
                    'word_count': chapter.word_count or 0,
                    'analysis_status': chapter.analysis_status,
                    'synthesis_status': chapter.synthesis_status
                })
            
            return chapter_list
            
        except Exception as e:
            logger.error(f"获取项目 {project_id} 章节列表失败: {str(e)}")
            raise ServiceException(f"获取项目章节失败: {str(e)}")
    
    def get_project_chapters_with_status(self, project_id: int, selected_chapter_ids: Optional[List[int]] = None) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """获取章节及分析状态"""
        try:
            chapters = self.get_project_chapters(project_id)
            
            # 如果指定了选中的章节ID，则只处理这些章节
            if selected_chapter_ids:
                chapters = [ch for ch in chapters if ch['id'] in selected_chapter_ids]
                logger.info(f"过滤后的章节数量: {len(chapters)}, 原始数量: {len(self.get_project_chapters(project_id))}")
            
            chapter_ids = [ch['id'] for ch in chapters]
            
            # 获取分析结果
            analysis_results = self.batch_get_existing_analysis(chapter_ids)
            
            # 统计状态
            status_summary = {
                'total_chapters': len(chapters),
                'analyzed_chapters': len(analysis_results),
                'pending_chapters': len(chapters) - len(analysis_results),
                'analyzed_chapter_ids': list(analysis_results.keys()),
                'pending_chapter_ids': [ch['id'] for ch in chapters if ch['id'] not in analysis_results]
            }
            
            # 为章节添加分析状态
            for chapter in chapters:
                chapter['has_analysis'] = chapter['id'] in analysis_results
                chapter['analysis_result'] = analysis_results.get(chapter['id'])
            
            return chapters, status_summary
            
        except Exception as e:
            logger.error(f"获取项目 {project_id} 章节状态失败: {str(e)}")
            raise ServiceException(f"获取章节状态失败: {str(e)}")
    
    def convert_chapter_analysis_to_synthesis_format(self, analysis_data: Dict[str, Any], chapter_info: Dict[str, Any]) -> Dict[str, Any]:
        """单章节格式转换"""
        try:
            # 提取角色信息
            characters = analysis_data.get('detected_characters', [])
            segments = analysis_data.get('segments', [])
            
            # 转换角色格式
            converted_characters = []
            for char in characters:
                char_info = {
                    'name': char.get('name', ''),
                    'frequency': char.get('frequency', 1),
                    'gender': char.get('recommended_config', {}).get('gender', 'unknown'),
                    'personality': char.get('recommended_config', {}).get('personality', 'calm'),
                    'personality_description': char.get('recommended_config', {}).get('personality_description', ''),
                    'is_main_character': char.get('is_main_character', False),
                    'chapter_source': chapter_info.get('chapter_number', 0),
                    'first_appearance_chapter': chapter_info.get('chapter_number', 0)
                }
                converted_characters.append(char_info)
            
            # 转换段落格式为合成计划
            synthesis_plan = []
            for i, segment in enumerate(segments):
                plan_item = {
                    'segment_id': i + 1,
                    'text': segment.get('text', ''),
                    'speaker': segment.get('speaker', '旁白'),
                    'text_type': segment.get('text_type', 'narration'),
                    'confidence': segment.get('confidence', 0.8),
                    'chapter_id': chapter_info.get('id'),
                    'chapter_number': chapter_info.get('chapter_number'),
                    'parameters': {
                        'timeStep': 20,
                        'pWeight': 1.0,
                        'tWeight': 1.0
                    }
                }
                synthesis_plan.append(plan_item)
            
            return {
                'characters': converted_characters,
                'synthesis_plan': synthesis_plan,
                'chapter_info': chapter_info,
                'processing_stats': analysis_data.get('processing_stats', {})
            }
            
        except Exception as e:
            logger.error(f"转换章节分析格式失败: {str(e)}")
            raise ServiceException(f"格式转换失败: {str(e)}")
    
    def aggregate_chapter_results(self, project_id: int, selected_chapter_ids: Optional[List[int]] = None) -> Dict[str, Any]:
        """多章节结果聚合"""
        try:
            # 获取章节及状态
            chapters, status_summary = self.get_project_chapters_with_status(project_id, selected_chapter_ids)
            
            # 检查是否所有章节都已分析
            if status_summary['pending_chapters'] > 0:
                pending_titles = []
                for chapter in chapters:
                    if not chapter['has_analysis']:
                        pending_titles.append(f"第{chapter['chapter_number']}章: {chapter['chapter_title']}")
                
                raise ServiceException(
                    f"项目还有 {status_summary['pending_chapters']} 个章节未完成分析，"
                    f"请先完成以下章节的智能准备：\n" + "\n".join(pending_titles[:5]) + 
                    ("..." if len(pending_titles) > 5 else "")
                )
            
            # 聚合所有章节的分析结果
            all_characters = {}  # 角色名 -> 角色信息（合并后）
            all_synthesis_plan = []
            chapter_mapping = {}  # 章节ID -> 章节信息
            
            for chapter in chapters:
                analysis_data = chapter['analysis_result']
                if not analysis_data:
                    continue
                
                chapter_info = {
                    'id': chapter['id'],
                    'chapter_number': chapter['chapter_number'],
                    'chapter_title': chapter['chapter_title'],
                    'word_count': chapter['word_count']
                }
                
                # 转换单章节格式
                converted = self.convert_chapter_analysis_to_synthesis_format(analysis_data, chapter_info)
                
                # 合并角色信息
                for char in converted['characters']:
                    char_name = char['name']
                    if char_name in all_characters:
                        # 合并已存在的角色
                        existing = all_characters[char_name]
                        existing['frequency'] += char['frequency']
                        existing['appearances'] = existing.get('appearances', []) + [chapter['chapter_number']]
                        
                        # 更新主角色标识
                        if char['is_main_character']:
                            existing['is_main_character'] = True
                    else:
                        # 新角色
                        char['appearances'] = [chapter['chapter_number']]
                        all_characters[char_name] = char
                
                # 添加合成计划
                all_synthesis_plan.extend(converted['synthesis_plan'])
                
                # 记录章节映射
                chapter_mapping[chapter['id']] = chapter_info
            
            # 转换角色字典为列表
            characters_list = list(all_characters.values())
            
            # 按频次排序角色
            characters_list.sort(key=lambda x: x['frequency'], reverse=True)
            
            # 构建聚合结果
            aggregated_result = {
                'project_info': {
                    'project_id': project_id,
                    'total_chapters': status_summary['total_chapters'],
                    'total_characters': len(characters_list),
                    'total_segments': len(all_synthesis_plan),
                    'analysis_time': datetime.now().isoformat(),
                    'ai_model': 'ollama-gemma3-27b',
                    'source': 'chapter_analysis_aggregation'
                },
                'characters': characters_list,
                'synthesis_plan': all_synthesis_plan,
                'chapter_mapping': chapter_mapping,
                'status_summary': status_summary
            }
            
            logger.info(f"项目 {project_id} 章节聚合完成: {len(characters_list)} 个角色, {len(all_synthesis_plan)} 个段落")
            
            return aggregated_result
            
        except Exception as e:
            logger.error(f"聚合项目 {project_id} 章节结果失败: {str(e)}")
            if isinstance(e, ServiceException):
                raise
            else:
                raise ServiceException(f"章节结果聚合失败: {str(e)}")
    
    def assign_voices_to_characters(self, characters: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """为角色分配语音 - 已禁用自动分配，保持voice_id为None"""
        try:
            logger.info(f"🎭 检测到 {len(characters)} 个角色，但不自动分配voice_id")
            
            # 🔧 不再自动分配任何voice_id，让用户手动分配
            assigned_characters = []
            
            for char in characters:
                char_name = char.get('name', '')
                
                # 更新角色信息，但不分配voice_id
                char_with_voice = char.copy()
                char_with_voice['voice_id'] = None
                char_with_voice['voice_name'] = '未分配'
                char_with_voice['voice_type'] = 'unknown'
                char_with_voice['voice_description'] = ''
                
                logger.info(f"⚠️ 角色 '{char_name}' 未分配voice_id，需要用户手动设置")
                assigned_characters.append(char_with_voice)
            
            logger.info(f"完成角色处理: {len(assigned_characters)} 个角色，全部需要用户手动分配voice_id")
            
            return assigned_characters
            
        except Exception as e:
            logger.error(f"角色处理失败: {str(e)}")
            # 回退：返回原始角色列表，不分配声音
            for char in characters:
                char['voice_id'] = None
                char['voice_name'] = '处理失败'
            return characters
    
    def _infer_gender_from_name(self, name: str) -> str:
        """从角色名称推断性别 - 已禁用自动推断"""
        logger.info(f"❌ 性别自动推断已禁用，角色 '{name}' 性别保持为 unknown")
        return 'unknown'
    
    def convert_to_synthesis_format(self, aggregated_data: Dict[str, Any]) -> Dict[str, Any]:
        """转换为合成格式"""
        try:
            # 为角色分配声音
            characters_with_voices = self.assign_voices_to_characters(aggregated_data['characters'])
            
            # 更新合成计划中的声音信息
            synthesis_plan = aggregated_data['synthesis_plan']
            character_voice_mapping = {char['name']: char for char in characters_with_voices}
            
            for plan_item in synthesis_plan:
                speaker = plan_item.get('speaker', '旁白')
                if speaker in character_voice_mapping:
                    char_info = character_voice_mapping[speaker]
                    plan_item['voice_id'] = char_info.get('voice_id')
                    plan_item['voice_name'] = char_info.get('voice_name', '')
                else:
                    # 如果找不到对应角色，使用默认声音
                    plan_item['voice_id'] = None
                    plan_item['voice_name'] = '未分配'
            
            # 🔧 数据一致性检查和修复
            character_names = {char['name'] for char in characters_with_voices}
            synthesis_speakers = {item.get('speaker') for item in synthesis_plan}
            
            # 找出在synthesis_plan中但不在characters中的角色
            missing_characters = synthesis_speakers - character_names
            if missing_characters:
                logger.warning(f"发现不一致：synthesis_plan中有角色但characters中缺失: {missing_characters}")
                
                # 自动添加缺失的角色到characters列表（使用默认配置）
                for missing_char in missing_characters:
                    if missing_char and missing_char.strip():  # 过滤空值
                        default_char = {
                            'name': missing_char,
                            'voice_id': None,
                            'voice_name': '未分配',
                            'voice_type': 'unknown',
                            'frequency': 1,
                            'gender': 'unknown',
                            'personality': 'calm',
                            'is_main_character': False
                        }
                        characters_with_voices.append(default_char)
                        logger.info(f"自动添加缺失角色: {missing_char}")
            
            # 构建最终的合成格式
            synthesis_format = {
                'project_info': aggregated_data['project_info'],
                'synthesis_plan': synthesis_plan,
                'characters': characters_with_voices,
                'chapter_mapping': aggregated_data.get('chapter_mapping', {}),
                'voice_assignment_summary': {
                    'total_characters': len(characters_with_voices),
                    'assigned_voices': len([c for c in characters_with_voices if c.get('voice_id')]),
                    'unassigned_characters': len([c for c in characters_with_voices if not c.get('voice_id')])
                },
                'data_consistency_check': {
                    'characters_count': len(character_names),
                    'synthesis_speakers_count': len(synthesis_speakers),
                    'missing_characters_found': len(missing_characters),
                    'missing_characters': list(missing_characters) if missing_characters else []
                }
            }
            
            return synthesis_format
            
        except Exception as e:
            logger.error(f"转换为合成格式失败: {str(e)}")
            raise ServiceException(f"合成格式转换失败: {str(e)}") 