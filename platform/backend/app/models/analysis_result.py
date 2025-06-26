"""
分析结果模型
存储LLM分析的结果和用户修改
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Index, JSON, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from typing import Dict, Any, Optional, List

from .base import Base


class AnalysisResult(Base):
    """分析结果模型"""
    
    __tablename__ = 'analysis_results'
    
    # 基础字段
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey('analysis_sessions.id', ondelete='CASCADE'), nullable=True)
    chapter_id = Column(Integer, ForeignKey('book_chapters.id', ondelete='CASCADE'), nullable=False)
    
    # 原始分析数据
    original_analysis = Column(JSON)  # LLM原始返回的分析结果
    llm_response_raw = Column(Text)  # LLM原始响应文本
    
    # 处理后的结果
    detected_characters = Column(JSON)  # 检测到的角色列表
    dialogue_segments = Column(JSON)  # 对话段落分析
    emotion_analysis = Column(JSON)  # 情感分析结果
    voice_recommendations = Column(JSON)  # 声音推荐
    
    # 合成计划
    synthesis_plan = Column(JSON)  # 合成计划配置
    
    # 用户修改
    user_modifications = Column(JSON)  # 用户手动修改记录
    final_config = Column(JSON)  # 最终确认的配置
    is_user_confirmed = Column(Boolean, default=False)  # 用户是否已确认
    
    # 处理状态
    status = Column(String(20), default='pending')  # pending, processing, completed, failed
    processing_time = Column(Integer)  # 处理耗时（秒）
    
    # 质量评估
    confidence_score = Column(Integer)  # 置信度评分 0-100
    quality_metrics = Column(JSON)  # 质量指标
    
    # 错误信息
    error_message = Column(Text)
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    confirmed_at = Column(DateTime)  # 用户确认时间
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    session = relationship("AnalysisSession", back_populates="analysis_results")
    chapter = relationship("BookChapter", back_populates="analysis_results")
    synthesis_tasks = relationship("SynthesisTask", back_populates="analysis_result")
    
    # 索引
    __table_args__ = (
        Index('idx_analysis_results_session_id', 'session_id'),
        Index('idx_analysis_results_chapter_id', 'chapter_id'),
        Index('idx_analysis_results_status', 'status'),
        Index('idx_analysis_results_is_confirmed', 'is_user_confirmed'),
        Index('idx_analysis_results_session_chapter', 'session_id', 'chapter_id'),
    )
    
    def __repr__(self):
        return f"<AnalysisResult(id={self.id}, session_id={self.session_id}, chapter_id={self.chapter_id}, status='{self.status}')>"
    
    def to_dict(self, include_raw: bool = False) -> Dict[str, Any]:
        """转换为字典格式"""
        result = {
            'id': self.id,
            'session_id': self.session_id,
            'chapter_id': self.chapter_id,
            'detected_characters': self.detected_characters,
            'dialogue_segments': self.dialogue_segments,
            'emotion_analysis': self.emotion_analysis,
            'voice_recommendations': self.voice_recommendations,
            'synthesis_plan': self.synthesis_plan,
            'user_modifications': self.user_modifications,
            'final_config': self.final_config,
            'is_user_confirmed': self.is_user_confirmed,
            'status': self.status,
            'processing_time': self.processing_time,
            'confidence_score': self.confidence_score,
            'quality_metrics': self.quality_metrics,
            'error_message': self.error_message,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'confirmed_at': self.confirmed_at.isoformat() if self.confirmed_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
        
        if include_raw:
            result.update({
                'original_analysis': self.original_analysis,
                'llm_response_raw': self.llm_response_raw
            })
        
        return result
    
    def get_character_count(self) -> int:
        """获取检测到的角色数量"""
        if not self.detected_characters:
            return 0
        return len(self.detected_characters)
    
    def get_dialogue_count(self) -> int:
        """获取对话段落数量"""
        if not self.dialogue_segments:
            return 0
        return len(self.dialogue_segments)
    
    def get_final_character_mapping(self) -> Dict[str, Any]:
        """获取最终的角色声音映射"""
        if self.final_config and 'character_mapping' in self.final_config:
            return self.final_config['character_mapping']
        
        if self.synthesis_plan and 'character_mapping' in self.synthesis_plan:
            return self.synthesis_plan['character_mapping']
        
        return {}
    
    def add_user_modification(self, modification_type: str, data: Dict[str, Any], user_id: str = None):
        """添加用户修改记录"""
        if not self.user_modifications:
            self.user_modifications = []
        
        modification = {
            'type': modification_type,
            'data': data,
            'timestamp': datetime.utcnow().isoformat(),
            'user_id': user_id
        }
        
        self.user_modifications.append(modification)
        self.updated_at = datetime.utcnow()
    
    def apply_user_modifications(self):
        """应用用户修改到最终配置"""
        if not self.user_modifications:
            self.final_config = self.synthesis_plan
            return
        
        # 从原始合成计划开始
        final_config = self.synthesis_plan.copy() if self.synthesis_plan else {}
        
        # 应用每个修改
        for mod in self.user_modifications:
            mod_type = mod.get('type')
            mod_data = mod.get('data', {})
            
            if mod_type == 'character_voice_change':
                # 修改角色声音
                character_name = mod_data.get('character_name')
                voice_id = mod_data.get('voice_id')
                if character_name and voice_id:
                    if 'character_mapping' not in final_config:
                        final_config['character_mapping'] = {}
                    final_config['character_mapping'][character_name] = voice_id
            
            elif mod_type == 'synthesis_params_change':
                # 修改合成参数
                params = mod_data.get('parameters', {})
                if 'synthesis_params' not in final_config:
                    final_config['synthesis_params'] = {}
                final_config['synthesis_params'].update(params)
            
            elif mod_type == 'character_add':
                # 添加角色
                character = mod_data.get('character')
                if character:
                    if 'detected_characters' not in final_config:
                        final_config['detected_characters'] = []
                    final_config['detected_characters'].append(character)
            
            elif mod_type == 'character_remove':
                # 移除角色
                character_name = mod_data.get('character_name')
                if character_name and 'detected_characters' in final_config:
                    final_config['detected_characters'] = [
                        char for char in final_config['detected_characters']
                        if char.get('name') != character_name
                    ]
        
        self.final_config = final_config
        self.updated_at = datetime.utcnow()
    
    def confirm_by_user(self, user_id: str = None):
        """用户确认分析结果"""
        self.is_user_confirmed = True
        self.confirmed_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        
        # 应用所有用户修改
        self.apply_user_modifications()
        
        # 记录确认操作
        self.add_user_modification('user_confirmed', {'confirmed_by': user_id}, user_id)
    
    def mark_completed(self, processing_time: int = None):
        """标记分析完成"""
        self.status = 'completed'
        self.completed_at = datetime.utcnow()
        if processing_time is not None:
            self.processing_time = processing_time
        self.updated_at = datetime.utcnow()
    
    def mark_failed(self, error_message: str):
        """标记分析失败"""
        self.status = 'failed'
        self.error_message = error_message
        self.updated_at = datetime.utcnow()
    
    def calculate_confidence_score(self) -> int:
        """计算置信度评分"""
        score = 0
        
        # 基于角色检测质量
        if self.detected_characters:
            character_count = len(self.detected_characters)
            if character_count > 0:
                score += min(30, character_count * 5)  # 最多30分
        
        # 基于对话检测质量
        if self.dialogue_segments:
            dialogue_count = len(self.dialogue_segments)
            if dialogue_count > 0:
                score += min(25, dialogue_count * 2)  # 最多25分
        
        # 基于情感分析质量
        if self.emotion_analysis:
            emotion_data = self.emotion_analysis
            if isinstance(emotion_data, list) and len(emotion_data) > 0:
                score += 20  # 20分
        
        # 基于声音推荐质量
        if self.voice_recommendations:
            recommendation_count = len(self.voice_recommendations)
            if recommendation_count > 0:
                score += min(25, recommendation_count * 5)  # 最多25分
        
        self.confidence_score = min(100, score)
        return self.confidence_score 