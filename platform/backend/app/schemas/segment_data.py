"""
Segment数据结构Schema定义
确保数据一致性和完整性
"""

from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field, validator
from datetime import datetime

class SegmentDataSchema(BaseModel):
    """标准化的Segment数据结构"""
    
    # 🔥 强制要求的核心字段
    segment_id: int = Field(..., description="段落ID，必须唯一")
    chapter_id: int = Field(..., description="章节ID，必须存在")
    chapter_number: int = Field(..., description="章节编号，必须存在")
    text: str = Field(..., min_length=1, description="段落文本内容，不能为空")
    speaker: str = Field(..., min_length=1, description="说话者，不能为空")
    
    # 语音配置字段
    voice_name: str = Field(default="未分配", description="语音名称")
    character_id: Optional[int] = Field(None, description="角色配音库ID")
    voice_id: Optional[int] = Field(None, description="传统语音Profile ID")
    
    # 文本分析字段
    text_type: str = Field(default="dialogue", description="文本类型")
    confidence: float = Field(default=0.8, ge=0.0, le=1.0, description="置信度")
    detection_rule: str = Field(default="ai_analysis", description="检测规则")
    
    # TTS参数
    timeStep: int = Field(default=20, description="时间步长")
    pWeight: float = Field(default=1.0, description="音调权重")
    tWeight: float = Field(default=1.0, description="时长权重")
    narrator_mode: bool = Field(default=False, description="旁白模式")
    skip_ai_analysis: bool = Field(default=False, description="跳过AI分析")
    
    @validator('segment_id')
    def validate_segment_id(cls, v):
        if v <= 0:
            raise ValueError('segment_id必须大于0')
        return v
    
    @validator('chapter_id')
    def validate_chapter_id(cls, v):
        if v <= 0:
            raise ValueError('chapter_id必须大于0')
        return v
    
    @validator('chapter_number')
    def validate_chapter_number(cls, v):
        if v <= 0:
            raise ValueError('chapter_number必须大于0')
        return v
    
    @validator('text')
    def validate_text(cls, v):
        if not v.strip():
            raise ValueError('text内容不能为空')
        return v.strip()
    
    @validator('speaker')
    def validate_speaker(cls, v):
        if not v.strip():
            raise ValueError('speaker不能为空')
        return v.strip()

class SynthesisPlanSchema(BaseModel):
    """合成计划数据结构"""
    
    # 项目信息
    project_info: Dict[str, Any] = Field(..., description="项目元信息")
    
    # 段落列表 - 强制使用标准化Schema
    synthesis_plan: List[SegmentDataSchema] = Field(..., description="合成段落列表")
    
    # 角色信息
    characters: List[Dict[str, Any]] = Field(default=[], description="角色列表")
    
    @validator('synthesis_plan')
    def validate_synthesis_plan(cls, v):
        if not v:
            raise ValueError('synthesis_plan不能为空')
        
        # 检查segment_id唯一性
        segment_ids = [seg.segment_id for seg in v]
        if len(segment_ids) != len(set(segment_ids)):
            raise ValueError('segment_id必须唯一')
        
        # 检查章节一致性
        chapter_ids = set(seg.chapter_id for seg in v)
        if len(chapter_ids) > 1:
            # 多章节合成时，确保chapter_number与chapter_id匹配
            for seg in v:
                if seg.chapter_id is None or seg.chapter_number is None:
                    raise ValueError(f'多章节合成时，所有segment必须包含完整章节信息')
        
        return v

class DataIntegrityValidator:
    """数据完整性验证器"""
    
    @staticmethod
    def validate_segment_data(data: Dict[str, Any]) -> SegmentDataSchema:
        """验证单个segment数据"""
        try:
            return SegmentDataSchema(**data)
        except Exception as e:
            raise ValueError(f"Segment数据验证失败: {str(e)}")
    
    @staticmethod
    def validate_synthesis_plan(data: Dict[str, Any]) -> SynthesisPlanSchema:
        """验证完整的合成计划"""
        try:
            return SynthesisPlanSchema(**data)
        except Exception as e:
            raise ValueError(f"合成计划验证失败: {str(e)}")
    
    @staticmethod
    def batch_validate_segments(segments: List[Dict[str, Any]]) -> List[SegmentDataSchema]:
        """批量验证segment数据"""
        validated_segments = []
        errors = []
        
        for i, segment in enumerate(segments):
            try:
                validated = DataIntegrityValidator.validate_segment_data(segment)
                validated_segments.append(validated)
            except ValueError as e:
                errors.append(f"Segment {i+1}: {str(e)}")
        
        if errors:
            raise ValueError(f"批量验证失败:\n" + "\n".join(errors))
        
        return validated_segments

class ConsistencyChecker:
    """数据一致性检查器"""
    
    @staticmethod
    def check_chapter_segment_consistency(db, project_id: int) -> Dict[str, Any]:
        """检查项目中章节与段落数据的一致性"""
        from ..models import NovelProject, BookChapter, AudioFile, AnalysisResult
        
        # 获取项目信息
        project = db.query(NovelProject).filter(NovelProject.id == project_id).first()
        if not project:
            return {"success": False, "error": "项目不存在"}
        
        # 获取章节信息
        chapters = db.query(BookChapter).filter(
            BookChapter.book_id == project.book_id
        ).all()
        
        # 获取分析结果
        analysis_results = db.query(AnalysisResult).filter(
            AnalysisResult.chapter_id.in_([ch.id for ch in chapters])
        ).all()
        
        # 获取音频文件
        audio_files = db.query(AudioFile).filter(
            AudioFile.project_id == project_id
        ).all()
        
        # 一致性检查
        issues = []
        chapter_mapping = {ch.id: ch for ch in chapters}
        
        for analysis in analysis_results:
            if not analysis.synthesis_plan:
                continue
                
            try:
                # 验证synthesis_plan数据完整性
                validated_plan = DataIntegrityValidator.validate_synthesis_plan(
                    analysis.synthesis_plan
                )
                
                # 检查章节映射一致性
                for segment in validated_plan.synthesis_plan:
                    if segment.chapter_id not in chapter_mapping:
                        issues.append(f"Segment {segment.segment_id} 引用了不存在的章节ID: {segment.chapter_id}")
                    
                    expected_chapter_number = chapter_mapping[segment.chapter_id].chapter_number
                    if segment.chapter_number != expected_chapter_number:
                        issues.append(f"Segment {segment.segment_id} 章节号不匹配: 期望{expected_chapter_number}, 实际{segment.chapter_number}")
                
            except ValueError as e:
                issues.append(f"章节 {analysis.chapter_id} 数据格式错误: {str(e)}")
        
        # 检查音频文件一致性
        audio_chapter_distribution = {}
        for audio in audio_files:
            chapter_id = audio.chapter_id
            if chapter_id not in audio_chapter_distribution:
                audio_chapter_distribution[chapter_id] = 0
            audio_chapter_distribution[chapter_id] += 1
        
        return {
            "success": len(issues) == 0,
            "issues": issues,
            "statistics": {
                "total_chapters": len(chapters),
                "analyzed_chapters": len(analysis_results),
                "audio_files_count": len(audio_files),
                "audio_chapter_distribution": audio_chapter_distribution
            }
        } 