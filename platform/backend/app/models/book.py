"""
书籍模型
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.orm.attributes import flag_modified
from datetime import datetime
import json
from typing import Dict, List, Any, Optional

from .base import BaseModel


class Book(BaseModel):
    """书籍模型"""
    __tablename__ = "books"
    
    title = Column(String(255), nullable=False, comment="书籍标题")
    author = Column(String(255), default="", comment="作者")
    description = Column(Text, default="", comment="描述")
    content = Column(Text, comment="书籍内容")
    chapters_data = Column(Text, comment="章节数据")
    status = Column(String(50), default="draft", comment="状态: draft, published, archived")
    tags = Column(Text, default="[]", comment="标签JSON")
    word_count = Column(Integer, default=0, comment="字数")
    chapter_count = Column(Integer, default=0, comment="章节数")
    source_file_path = Column(String(500), comment="源文件路径")
    source_file_name = Column(String(255), comment="源文件名")
    
    # 新增：角色汇总字段，存储整本书的角色信息汇总
    character_summary = Column(JSON, comment="角色汇总信息: {characters: [], voice_mappings: {}, last_updated: ''}")
    
    # 新增：图片生成配置字段，存储书籍级别的通用配置
    image_generation_config = Column(JSON, comment="图片生成配置: {style: '', steps: 20, guidance: 7.5, model: '', seed: -1, batchSize: 1}")
    
    # 添加反向关联
    characters = relationship("Character", back_populates="book")
    
    # 关系
    chapters = relationship("BookChapter", back_populates="book", cascade="all, delete-orphan")
    projects = relationship("NovelProject", back_populates="book", cascade="all, delete-orphan")
    storyboard_sessions = relationship("StoryboardAnalysisSession", back_populates="book", cascade="all, delete-orphan")
    
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
    
    def get_chapters(self):
        """获取章节信息"""
        try:
            return json.loads(self.chapters_data) if self.chapters_data else []
        except json.JSONDecodeError:
            return []
    
    def set_chapters(self, chapters):
        """设置章节信息"""
        self.chapters_data = json.dumps(chapters, ensure_ascii=False)
    
    def get_character_summary(self) -> Dict[str, Any]:
        """获取角色汇总信息"""
        if not self.character_summary:
            return {
                "characters": [],
                "voice_mappings": {},
                "last_updated": None,
                "total_chapters_analyzed": 0
            }
        
        # 🔥 修复：处理字符串格式的数据
        if isinstance(self.character_summary, str):
            try:
                return json.loads(self.character_summary)
            except json.JSONDecodeError:
                # 如果解析失败，返回默认格式
                return {
                    "characters": [],
                    "voice_mappings": {},
                    "last_updated": None,
                    "total_chapters_analyzed": 0
                }
        
        return self.character_summary
    
    def update_character_summary(self, detected_characters: List[Dict[str, Any]], chapter_id: int = None):
        """
        更新角色汇总信息
        
        Args:
            detected_characters: 新检测到的角色列表
            chapter_id: 来源章节ID（可选，用于记录）
        """
        current_summary = self.get_character_summary()
        existing_characters = {char['name']: char for char in current_summary.get('characters', [])}
        
        # 合并新检测到的角色
        for new_char in detected_characters:
            # 🔥 修复：支持两种数据格式
            if isinstance(new_char, str):
                # 格式1：字符串列表 ['小明', '小红', ...]
                char_name = new_char.strip()
                char_data = {
                    'name': char_name,
                    'gender': '',
                    'age': '',
                    'personality': '',
                    'description': '',
                    'appearances': 1
                }
            elif isinstance(new_char, dict):
                # 格式2：字典列表 [{'name': '小明', ...}, ...]
                char_name = new_char.get('name', '').strip()
                char_data = new_char
            else:
                # 未知格式，跳过
                continue
                
            if not char_name:
                continue
                
            if char_name in existing_characters:
                # 更新现有角色的信息（合并出现次数、章节等）
                existing_char = existing_characters[char_name]
                existing_char['total_appearances'] = existing_char.get('total_appearances', 0) + char_data.get('appearances', 1)
                
                # 合并章节出现记录
                if 'chapters' not in existing_char:
                    existing_char['chapters'] = []
                if chapter_id and chapter_id not in existing_char['chapters']:
                    existing_char['chapters'].append(chapter_id)
                
                # 更新其他属性（如果新的更详细）
                for key in ['gender', 'age', 'personality', 'description']:
                    if char_data.get(key) and (not existing_char.get(key) or len(str(char_data[key])) > len(str(existing_char.get(key, '')))):
                        existing_char[key] = char_data[key]
            else:
                # 添加新角色
                new_character = {
                    'name': char_name,
                    'gender': char_data.get('gender', ''),
                    'age': char_data.get('age', ''),
                    'personality': char_data.get('personality', ''),
                    'description': char_data.get('description', ''),
                    'total_appearances': char_data.get('appearances', 1),
                    'chapters': [chapter_id] if chapter_id else [],
                    'first_detected': datetime.utcnow().isoformat()
                }
                existing_characters[char_name] = new_character
        
        # 更新汇总信息
        new_summary = {
            'characters': list(existing_characters.values()),
            'voice_mappings': current_summary.get('voice_mappings', {}),
            'last_updated': datetime.utcnow().isoformat(),
            'total_chapters_analyzed': current_summary.get('total_chapters_analyzed', 0) + (1 if chapter_id else 0)
        }
        
        # 🔥 关键修复：标记字段已修改
        self.character_summary = new_summary
        flag_modified(self, 'character_summary')
    
    def set_character_voice_mapping(self, character_name: str, voice_id: str):
        """
        设置角色的语音映射
        
        Args:
            character_name: 角色名称
            voice_id: 语音ID
        """
        current_summary = self.get_character_summary()
        current_summary['voice_mappings'][character_name] = voice_id
        current_summary['last_updated'] = datetime.utcnow().isoformat()
        
        # 🔥 关键修复：重新赋值整个字典并标记字段已修改
        self.character_summary = dict(current_summary)  # 创建新的字典对象
        flag_modified(self, 'character_summary')  # 明确告诉SQLAlchemy字段已修改
    
    def get_character_voice_mapping(self, character_name: str) -> Optional[str]:
        """获取角色的语音映射"""
        current_summary = self.get_character_summary()
        return current_summary.get('voice_mappings', {}).get(character_name)
    
    def get_all_character_names(self) -> List[str]:
        """获取所有角色名称列表"""
        current_summary = self.get_character_summary()
        return [char['name'] for char in current_summary.get('characters', [])]
    
    def get_character_count(self) -> int:
        """获取角色总数"""
        current_summary = self.get_character_summary()
        return len(current_summary.get('characters', []))
    
    def get_image_generation_config(self) -> Dict[str, Any]:
        """获取图片生成配置"""
        if not self.image_generation_config:
            return {
                "style": "realistic",
                "steps": 20,
                "guidance": 7.5,
                "model": "flux-dev",
                "seed": -1,
                "batchSize": 1
            }
        
        # 处理字符串格式的数据
        if isinstance(self.image_generation_config, str):
            try:
                return json.loads(self.image_generation_config)
            except json.JSONDecodeError:
                # 如果解析失败，返回默认配置
                return {
                    "style": "realistic",
                    "steps": 20,
                    "guidance": 7.5,
                    "model": "flux-dev",
                    "seed": -1,
                    "batchSize": 1
                }
        
        return self.image_generation_config
    
    def set_image_generation_config(self, config: Dict[str, Any]):
        """设置图片生成配置"""
        # 验证配置格式
        default_config = {
            "style": "realistic",
            "steps": 20,
            "guidance": 7.5,
            "model": "flux-dev",
            "seed": -1,
            "batchSize": 1
        }
        
        # 合并配置，保留默认值
        merged_config = {**default_config, **config}
        
        # 设置配置并标记字段已修改
        self.image_generation_config = merged_config
        flag_modified(self, 'image_generation_config')
    
    def to_dict(self):
        """转换为字典，包含特殊字段处理"""
        result = super().to_dict()
        result['tags'] = self.get_tags()
        result['chapters'] = self.get_chapters()
        result['character_summary'] = self.get_character_summary()
        result['image_generation_config'] = self.get_image_generation_config()
        return result