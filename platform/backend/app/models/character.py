from sqlalchemy import Column, Integer, String, ForeignKey, Text, Float, JSON
from sqlalchemy.orm import relationship
import json
import os
from app.models.base import BaseModel

class Character(BaseModel):
    __tablename__ = "characters"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, comment="角色名称")
    description = Column(Text, nullable=True, comment="角色描述")
    
    # 书籍关联
    book_id = Column(Integer, ForeignKey("books.id", ondelete="SET NULL"), nullable=True, comment="所属书籍ID")
    chapter_id = Column(Integer, ForeignKey("book_chapters.id", ondelete="SET NULL"), nullable=True, comment="首次出现章节ID")
    
    # 声音配置字段（合并VoiceProfile功能）
    voice_type = Column(String(50), default="custom", comment="声音类型: male, female, child, elder, custom")
    color = Column(String(20), default="#8b5cf6", comment="显示颜色")
    
    # 🔥 新增：外貌特征字段
    age_range = Column(String(20), comment="年龄范围: child, young, middle, elder")
    build_type = Column(String(20), comment="身材类型: slim, average, sturdy, plump")
    clothing_style = Column(String(20), comment="服装风格: ancient, modern, formal, casual")
    distinctive_features = Column(Text, comment="特殊外貌特征")
    appearance_description = Column(Text, comment="完整外貌描述")
    avatar_prompt = Column(Text, comment="头像生成AI提示词")
    consistency_tag = Column(String(100), comment="视觉一致性标签")
    
    # 文件路径
    avatar_path = Column(String(500), comment="头像图片路径")
    reference_audio_path = Column(String(500), comment="参考音频路径")
    latent_file_path = Column(String(500), comment="latent文件路径")
    
    # 参数配置
    voice_parameters = Column(JSON, comment="TTS参数配置")
    tags = Column(JSON, comment="标签")
    
    # 状态信息
    status = Column(String(50), default="unconfigured", comment="状态: configured, unconfigured, training")
    quality_score = Column(Float, comment="质量评分")
    usage_count = Column(Integer, default=0, comment="使用次数")
    
    # 关联关系
    book = relationship("Book", back_populates="characters")
    chapter = relationship("BookChapter", back_populates="characters")
    
    def get_voice_parameters(self):
        """获取声音参数配置"""
        try:
            if isinstance(self.voice_parameters, str):
                return json.loads(self.voice_parameters) if self.voice_parameters else {
                    "time_step": 20,
                    "p_weight": 1.0,
                    "t_weight": 1.0
                }
            elif isinstance(self.voice_parameters, dict):
                return self.voice_parameters
            else:
                return {
                    "time_step": 20,
                    "p_weight": 1.0,
                    "t_weight": 1.0
                }
        except json.JSONDecodeError:
            return {
                "time_step": 20,
                "p_weight": 1.0,
                "t_weight": 1.0
            }
    
    def set_voice_parameters(self, params):
        """设置声音参数配置"""
        self.voice_parameters = json.dumps(params, ensure_ascii=False)
    
    def get_tags(self):
        """获取标签列表"""
        try:
            if isinstance(self.tags, str):
                return json.loads(self.tags) if self.tags else []
            elif isinstance(self.tags, list):
                return self.tags
            else:
                return []
        except json.JSONDecodeError:
            return []
    
    def set_tags(self, tags):
        """设置标签列表"""
        self.tags = json.dumps(tags, ensure_ascii=False)
    
    def validate_voice_files(self):
        """验证声音文件是否存在"""
        missing_files = []
        
        if self.reference_audio_path and not os.path.exists(self.reference_audio_path):
            missing_files.append(self.reference_audio_path)
        
        if self.latent_file_path and not os.path.exists(self.latent_file_path):
            missing_files.append(self.latent_file_path)
        
        return {
            'valid': len(missing_files) == 0,
            'missing_files': missing_files
        }
    
    @property
    def is_voice_configured(self):
        """检查是否已配置声音"""
        if not self.reference_audio_path:
            return False
        
        # 🔧 改进：尝试多个可能的路径
        possible_paths = [
            self.reference_audio_path,
            os.path.join("data/voice_profiles", os.path.basename(self.reference_audio_path)),
            os.path.join("/app/data/voice_profiles", os.path.basename(self.reference_audio_path)) if os.path.exists("/.dockerenv") else None
        ]
        
        for path in possible_paths:
            if path and os.path.exists(path):
                return True
        
        # 🔧 如果文件不存在但有路径，仍然认为是"已配置"状态，只是文件缺失
        # 这样可以避免因为路径问题导致的误判
        return bool(self.reference_audio_path)
    
    def to_dict(self):
        """转换为字典"""
        # 🔧 修复：先获取基础字典，然后处理JSON字段
        result = {}
        for column in self.__table__.columns:
            value = getattr(self, column.name)
            # 跳过JSON字段，稍后单独处理
            if column.name not in ['voice_parameters', 'tags']:
                result[column.name] = value
        
        # 单独处理JSON字段
        result['voice_parameters'] = self.get_voice_parameters()
        result['tags'] = self.get_tags()
        result['is_voice_configured'] = self.is_voice_configured
        
        # 🔧 添加缺失的计算属性
        result['has_avatar'] = bool(self.avatar_path)
        result['has_latent'] = bool(self.latent_file_path)
        
        # 确保所有字段都有值（避免undefined）
        result['status'] = self.status or 'unconfigured'
        result['voice_type'] = self.voice_type or 'custom'
        result['color'] = self.color or '#8b5cf6'
        result['quality_score'] = self.quality_score or 0.0
        result['usage_count'] = self.usage_count or 0
        
        # 生成文件URL
        if self.avatar_path:
            # 🔥 修正：使用正确的API接口路径
            result['avatarUrl'] = f"/api/v1/characters/avatar/{self.id}"
        else:
            # 提供默认头像，确保前端显示一致性
            # 🔥 修复：对角色名称进行URL编码，避免中文字符导致的422错误
            from urllib.parse import quote
            encoded_name = quote(self.name, safe='')
            result['avatarUrl'] = f"/api/v1/characters/avatar/default?name={encoded_name}&voice_type={self.voice_type}"
            
        if self.reference_audio_path:
            # 🔥 修复：使用正确的音频文件访问路径
            result['referenceAudioUrl'] = f"/api/v1/characters/{self.id}/audio/reference"
        else:
            result['referenceAudioUrl'] = None
            
        if self.latent_file_path:
            filename = os.path.basename(self.latent_file_path)
            result['latentFileUrl'] = f"/api/v1/voice_profiles/{filename}"
        else:
            result['latentFileUrl'] = None
        
        return result