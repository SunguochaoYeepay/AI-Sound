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
        """智能声音分配"""
        try:
            # 获取可用的声音档案
            available_voices = self.db.query(VoiceProfile).filter(
                VoiceProfile.status == 'active'
            ).all()
            
            if len(available_voices) < 2:
                logger.warning("可用声音档案不足，使用默认分配")
                # 如果声音不足，至少保证有基本的声音分配
                for i, char in enumerate(characters):
                    if available_voices:
                        char['voice_id'] = available_voices[i % len(available_voices)].id
                        char['voice_name'] = available_voices[i % len(available_voices)].name
                    else:
                        char['voice_id'] = None
                        char['voice_name'] = '未分配'
                return characters
            
            # 按性别和类型分类声音
            male_voices = [v for v in available_voices if v.type == 'male']
            female_voices = [v for v in available_voices if v.type == 'female']
            neutral_voices = [v for v in available_voices if v.type in ['neutral', 'narrator']]
            child_voices = [v for v in available_voices if v.type == 'child']
            
            # 为每个角色智能分配声音
            assigned_characters = []
            voice_assignment_counter = {'male': 0, 'female': 0, 'neutral': 0, 'child': 0}
            
            for char in characters:
                char_name = char.get('name', '')
                char_gender = char.get('gender', 'unknown')
                char_personality = char.get('personality', 'calm')
                
                assigned_voice = None
                
                # 特殊角色处理
                if char_name in ['旁白', '叙述者', 'narrator']:
                    # 旁白优先使用旁白专用声音
                    narrator_voices = [v for v in neutral_voices if 'narrator' in v.type.lower() or 'narrator' in v.name.lower()]
                    if narrator_voices:
                        assigned_voice = narrator_voices[0]
                    elif neutral_voices:
                        assigned_voice = neutral_voices[voice_assignment_counter['neutral'] % len(neutral_voices)]
                        voice_assignment_counter['neutral'] += 1
                
                # 根据性别分配声音
                elif char_gender == 'male' and male_voices:
                    assigned_voice = male_voices[voice_assignment_counter['male'] % len(male_voices)]
                    voice_assignment_counter['male'] += 1
                
                elif char_gender == 'female' and female_voices:
                    assigned_voice = female_voices[voice_assignment_counter['female'] % len(female_voices)]
                    voice_assignment_counter['female'] += 1
                
                # 智能性别推断
                elif char_gender == 'unknown':
                    # 基于角色名称推断性别
                    inferred_gender = self._infer_gender_from_name(char_name)
                    
                    if inferred_gender == 'male' and male_voices:
                        assigned_voice = male_voices[voice_assignment_counter['male'] % len(male_voices)]
                        voice_assignment_counter['male'] += 1
                    elif inferred_gender == 'female' and female_voices:
                        assigned_voice = female_voices[voice_assignment_counter['female'] % len(female_voices)]
                        voice_assignment_counter['female'] += 1
                    else:
                        # 默认使用中性声音
                        if neutral_voices:
                            assigned_voice = neutral_voices[voice_assignment_counter['neutral'] % len(neutral_voices)]
                            voice_assignment_counter['neutral'] += 1
                
                # 回退方案：使用任意可用声音
                if not assigned_voice and available_voices:
                    assigned_voice = available_voices[len(assigned_characters) % len(available_voices)]
                
                # 更新角色信息
                char_with_voice = char.copy()
                if assigned_voice:
                    char_with_voice['voice_id'] = assigned_voice.id
                    char_with_voice['voice_name'] = assigned_voice.name
                    char_with_voice['voice_type'] = assigned_voice.type
                    char_with_voice['voice_description'] = assigned_voice.description
                else:
                    char_with_voice['voice_id'] = None
                    char_with_voice['voice_name'] = '未分配'
                    char_with_voice['voice_type'] = 'unknown'
                    char_with_voice['voice_description'] = ''
                
                assigned_characters.append(char_with_voice)
            
            logger.info(f"完成声音分配: {len(assigned_characters)} 个角色, 使用了 {len(available_voices)} 个可用声音")
            
            return assigned_characters
            
        except Exception as e:
            logger.error(f"声音分配失败: {str(e)}")
            # 回退：返回原始角色列表，不分配声音
            for char in characters:
                char['voice_id'] = None
                char['voice_name'] = '分配失败'
            return characters
    
    def _infer_gender_from_name(self, name: str) -> str:
        """从角色名称推断性别"""
        try:
            # 常见的性别关键词
            male_keywords = ['王', '帝', '皇', '公', '爷', '父', '兄', '弟', '师父', '先生', '大人']
            female_keywords = ['女', '妃', '后', '姐', '妹', '母', '娘', '夫人', '小姐', '姑娘']
            
            name_lower = name.lower()
            
            # 检查名称中的性别关键词
            for keyword in male_keywords:
                if keyword in name:
                    return 'male'
            
            for keyword in female_keywords:
                if keyword in name:
                    return 'female'
            
            # 基于常见中文姓名特征
            if len(name) >= 2:
                last_char = name[-1]
                # 常见女性名字结尾字
                female_endings = ['妹', '娘', '芳', '花', '玉', '珠', '凤', '燕', '莲', '梅', '兰', '竹', '菊']
                if last_char in female_endings:
                    return 'female'
                
                # 常见男性名字结尾字
                male_endings = ['强', '勇', '军', '伟', '刚', '豪', '雄', '杰', '峰', '龙', '虎', '鹏']
                if last_char in male_endings:
                    return 'male'
            
            return 'unknown'
            
        except Exception as e:
            logger.error(f"性别推断失败: {str(e)}")
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
                }
            }
            
            return synthesis_format
            
        except Exception as e:
            logger.error(f"转换为合成格式失败: {str(e)}")
            raise ServiceException(f"合成格式转换失败: {str(e)}") 