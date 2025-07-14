"""
自动恢复服务
检测和修复章节-段落数据不一致问题
"""

import logging
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from datetime import datetime

logger = logging.getLogger(__name__)

class AutoRecoveryService:
    """自动恢复服务"""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def check_and_fix_project_consistency(self, project_id: int) -> Dict[str, Any]:
        """检查并修复项目的数据一致性"""
        logger.info(f"[AUTO_RECOVERY] 开始检查项目 {project_id} 的数据一致性")
        
        # 第一步：使用一致性检查器检测问题
        from ..schemas.segment_data import ConsistencyChecker
        consistency_result = ConsistencyChecker.check_chapter_segment_consistency(
            self.db, project_id
        )
        
        if consistency_result["success"]:
            logger.info(f"[AUTO_RECOVERY] 项目 {project_id} 数据一致性良好，无需修复")
            return {
                "success": True,
                "message": "数据一致性良好，无需修复",
                "issues_fixed": [],
                "statistics": consistency_result["statistics"]
            }
        
        # 第二步：分析具体问题类型
        issues = consistency_result["issues"]
        logger.warning(f"[AUTO_RECOVERY] 发现 {len(issues)} 个数据一致性问题")
        
        # 第三步：尝试自动修复
        fixed_issues = []
        unfixable_issues = []
        
        for issue in issues:
            try:
                if "章节号不匹配" in issue:
                    # 修复章节号不匹配问题
                    if await self._fix_chapter_number_mismatch(project_id, issue):
                        fixed_issues.append(issue)
                    else:
                        unfixable_issues.append(issue)
                
                elif "引用了不存在的章节ID" in issue:
                    # 修复引用不存在章节的问题
                    if await self._fix_invalid_chapter_reference(project_id, issue):
                        fixed_issues.append(issue)
                    else:
                        unfixable_issues.append(issue)
                
                elif "数据格式错误" in issue:
                    # 修复数据格式错误
                    if await self._fix_data_format_error(project_id, issue):
                        fixed_issues.append(issue)
                    else:
                        unfixable_issues.append(issue)
                
                else:
                    unfixable_issues.append(issue)
                    
            except Exception as e:
                logger.error(f"[AUTO_RECOVERY] 修复问题失败: {issue}, 错误: {str(e)}")
                unfixable_issues.append(f"{issue} (修复失败: {str(e)})")
        
        # 第四步：如果有音频文件位置错误，尝试修复
        audio_fix_result = await self._fix_audio_file_chapter_mismatch(project_id)
        if audio_fix_result["fixed_count"] > 0:
            fixed_issues.extend(audio_fix_result["fixed_issues"])
        
        logger.info(f"[AUTO_RECOVERY] 修复完成：成功修复 {len(fixed_issues)} 个问题，{len(unfixable_issues)} 个问题需要手动处理")
        
        return {
            "success": len(unfixable_issues) == 0,
            "message": f"自动修复完成：成功修复 {len(fixed_issues)} 个问题",
            "issues_fixed": fixed_issues,
            "issues_unfixable": unfixable_issues,
            "audio_fix_result": audio_fix_result
        }
    
    async def _fix_chapter_number_mismatch(self, project_id: int, issue: str) -> bool:
        """修复章节号不匹配问题"""
        try:
            from ..models import NovelProject, BookChapter, AnalysisResult
            
            # 获取项目信息
            project = self.db.query(NovelProject).filter(NovelProject.id == project_id).first()
            if not project:
                return False
            
            # 获取所有章节的正确映射
            chapters = self.db.query(BookChapter).filter(
                BookChapter.book_id == project.book_id
            ).all()
            chapter_mapping = {ch.id: ch.chapter_number for ch in chapters}
            
            # 获取分析结果并修复
            analysis_results = self.db.query(AnalysisResult).filter(
                AnalysisResult.chapter_id.in_(list(chapter_mapping.keys()))
            ).all()
            
            fixed_count = 0
            for analysis in analysis_results:
                if not analysis.synthesis_plan:
                    continue
                
                synthesis_plan = analysis.synthesis_plan
                if 'synthesis_plan' in synthesis_plan:
                    segments = synthesis_plan['synthesis_plan']
                    corrected = False
                    
                    for segment in segments:
                        chapter_id = segment.get('chapter_id')
                        if chapter_id and chapter_id in chapter_mapping:
                            correct_chapter_number = chapter_mapping[chapter_id]
                            if segment.get('chapter_number') != correct_chapter_number:
                                segment['chapter_number'] = correct_chapter_number
                                corrected = True
                    
                    if corrected:
                        # 标记为已修改并保存
                        analysis.synthesis_plan = synthesis_plan
                        fixed_count += 1
            
            if fixed_count > 0:
                self.db.commit()
                logger.info(f"[AUTO_RECOVERY] 修复了 {fixed_count} 个章节号不匹配问题")
                return True
            
        except Exception as e:
            logger.error(f"[AUTO_RECOVERY] 修复章节号不匹配失败: {str(e)}")
            self.db.rollback()
        
        return False
    
    async def _fix_invalid_chapter_reference(self, project_id: int, issue: str) -> bool:
        """修复引用不存在章节的问题"""
        try:
            # 这种问题通常需要重新生成智能准备结果
            # 暂时标记为需要手动处理
            logger.warning(f"[AUTO_RECOVERY] 引用不存在章节的问题需要手动处理: {issue}")
            return False
        except Exception as e:
            logger.error(f"[AUTO_RECOVERY] 修复无效章节引用失败: {str(e)}")
        
        return False
    
    async def _fix_data_format_error(self, project_id: int, issue: str) -> bool:
        """修复数据格式错误"""
        try:
            from ..models import NovelProject, AnalysisResult, BookChapter
            from ..schemas.segment_data import DataIntegrityValidator
            
            # 获取项目信息
            project = self.db.query(NovelProject).filter(NovelProject.id == project_id).first()
            if not project:
                return False
            
            # 获取有问题的分析结果
            analysis_results = self.db.query(AnalysisResult).join(
                BookChapter, AnalysisResult.chapter_id == BookChapter.id
            ).filter(BookChapter.book_id == project.book_id).all()
            
            fixed_count = 0
            for analysis in analysis_results:
                try:
                    if analysis.synthesis_plan:
                        # 尝试验证并自动修复
                        validated_plan = DataIntegrityValidator.validate_synthesis_plan(
                            analysis.synthesis_plan
                        )
                        fixed_count += 1
                except Exception:
                    # 如果验证失败，尝试补全缺失字段
                    if await self._supplement_missing_fields(analysis):
                        fixed_count += 1
            
            if fixed_count > 0:
                self.db.commit()
                logger.info(f"[AUTO_RECOVERY] 修复了 {fixed_count} 个数据格式错误")
                return True
                
        except Exception as e:
            logger.error(f"[AUTO_RECOVERY] 修复数据格式错误失败: {str(e)}")
            self.db.rollback()
        
        return False
    
    async def _supplement_missing_fields(self, analysis: 'AnalysisResult') -> bool:
        """补全缺失的字段"""
        try:
            from ..models import BookChapter
            
            if not analysis.synthesis_plan:
                return False
            
            # 获取章节信息
            chapter = self.db.query(BookChapter).filter(
                BookChapter.id == analysis.chapter_id
            ).first()
            
            if not chapter:
                return False
            
            synthesis_plan = analysis.synthesis_plan
            if 'synthesis_plan' in synthesis_plan:
                segments = synthesis_plan['synthesis_plan']
                modified = False
                
                for segment in segments:
                    # 补全缺失的chapter_id
                    if 'chapter_id' not in segment or segment['chapter_id'] is None:
                        segment['chapter_id'] = chapter.id
                        modified = True
                    
                    # 补全缺失的chapter_number
                    if 'chapter_number' not in segment or segment['chapter_number'] is None:
                        segment['chapter_number'] = chapter.chapter_number
                        modified = True
                
                if modified:
                    analysis.synthesis_plan = synthesis_plan
                    logger.info(f"[AUTO_RECOVERY] 为章节 {chapter.id} 补全了缺失字段")
                    return True
            
        except Exception as e:
            logger.error(f"[AUTO_RECOVERY] 补全缺失字段失败: {str(e)}")
        
        return False
    
    async def _fix_audio_file_chapter_mismatch(self, project_id: int) -> Dict[str, Any]:
        """修复音频文件章节映射错误"""
        try:
            from ..models import AudioFile, AnalysisResult, BookChapter, NovelProject
            
            # 获取项目信息
            project = self.db.query(NovelProject).filter(NovelProject.id == project_id).first()
            if not project:
                return {"fixed_count": 0, "fixed_issues": []}
            
            # 获取所有音频文件
            audio_files = self.db.query(AudioFile).filter(
                AudioFile.project_id == project_id,
                AudioFile.audio_type == 'segment'
            ).all()
            
            # 构建segment_id到正确chapter_id的映射
            segment_chapter_mapping = {}
            analysis_results = self.db.query(AnalysisResult).join(
                BookChapter, AnalysisResult.chapter_id == BookChapter.id
            ).filter(BookChapter.book_id == project.book_id).all()
            
            for analysis in analysis_results:
                if analysis.synthesis_plan and 'synthesis_plan' in analysis.synthesis_plan:
                    segments = analysis.synthesis_plan['synthesis_plan']
                    for segment in segments:
                        segment_id = segment.get('segment_id')
                        chapter_id = segment.get('chapter_id') or analysis.chapter_id
                        if segment_id:
                            segment_chapter_mapping[segment_id] = chapter_id
            
            # 修复音频文件的章节映射
            fixed_count = 0
            fixed_issues = []
            
            for audio in audio_files:
                if audio.segment_id and audio.segment_id in segment_chapter_mapping:
                    correct_chapter_id = segment_chapter_mapping[audio.segment_id]
                    if audio.chapter_id != correct_chapter_id:
                        old_chapter_id = audio.chapter_id
                        audio.chapter_id = correct_chapter_id
                        fixed_count += 1
                        fixed_issues.append(
                            f"音频文件 {audio.id} (segment_{audio.segment_id}) 章节映射从 {old_chapter_id} 修正为 {correct_chapter_id}"
                        )
            
            if fixed_count > 0:
                self.db.commit()
                logger.info(f"[AUTO_RECOVERY] 修复了 {fixed_count} 个音频文件章节映射错误")
            
            return {
                "fixed_count": fixed_count,
                "fixed_issues": fixed_issues
            }
            
        except Exception as e:
            logger.error(f"[AUTO_RECOVERY] 修复音频文件章节映射失败: {str(e)}")
            self.db.rollback()
            return {"fixed_count": 0, "fixed_issues": []}
    
    async def run_daily_consistency_check(self) -> Dict[str, Any]:
        """运行每日数据一致性检查"""
        logger.info("[AUTO_RECOVERY] 开始每日数据一致性检查")
        
        try:
            from ..models import NovelProject
            
            # 获取所有活跃项目
            active_projects = self.db.query(NovelProject).filter(
                NovelProject.status.in_(['active', 'completed'])
            ).all()
            
            total_projects = len(active_projects)
            checked_projects = 0
            projects_with_issues = 0
            total_issues_fixed = 0
            
            for project in active_projects:
                try:
                    result = await self.check_and_fix_project_consistency(project.id)
                    checked_projects += 1
                    
                    if not result["success"]:
                        projects_with_issues += 1
                    
                    total_issues_fixed += len(result.get("issues_fixed", []))
                    
                except Exception as e:
                    logger.error(f"[AUTO_RECOVERY] 检查项目 {project.id} 失败: {str(e)}")
            
            summary = {
                "success": True,
                "total_projects": total_projects,
                "checked_projects": checked_projects,
                "projects_with_issues": projects_with_issues,
                "total_issues_fixed": total_issues_fixed,
                "check_time": datetime.now().isoformat()
            }
            
            logger.info(f"[AUTO_RECOVERY] 每日检查完成：{summary}")
            return summary
            
        except Exception as e:
            logger.error(f"[AUTO_RECOVERY] 每日检查失败: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "check_time": datetime.now().isoformat()
            } 