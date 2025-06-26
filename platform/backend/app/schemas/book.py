"""
书籍相关Schema定义
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from .common import BaseResponseModel


class BookCreate(BaseModel):
    """创建书籍请求"""
    title: str = Field(min_length=1, max_length=200, description="书籍标题")
    author: Optional[str] = Field(default=None, max_length=100, description="作者")
    description: Optional[str] = Field(default=None, description="书籍描述")


class BookUpdate(BaseModel):
    """更新书籍请求"""
    title: Optional[str] = Field(default=None, min_length=1, max_length=200, description="书籍标题")
    author: Optional[str] = Field(default=None, max_length=100, description="作者")
    description: Optional[str] = Field(default=None, description="书籍描述")


class BookResponse(BaseResponseModel):
    """书籍响应"""
    title: str = Field(description="书籍标题")
    author: Optional[str] = Field(description="作者")
    description: Optional[str] = Field(description="书籍描述")
    file_path: Optional[str] = Field(description="文件路径")
    file_size: Optional[int] = Field(description="文件大小")
    original_filename: Optional[str] = Field(description="原始文件名")
    total_chapters: int = Field(description="章节总数")
    total_words: int = Field(description="总字数")
    structure_detected: str = Field(description="结构检测状态")
    chapter_detection_config: Optional[Dict[str, Any]] = Field(description="章节检测配置")


class BookStructureStatus(BaseModel):
    """书籍结构状态"""
    book_id: int = Field(description="书籍ID")
    structure_detected: str = Field(description="结构检测状态")
    total_chapters: int = Field(description="章节总数")
    total_words: int = Field(description="总字数")
    chapter_status_counts: Dict[str, int] = Field(description="章节状态统计")
    detection_config: Optional[Dict[str, Any]] = Field(description="检测配置")


class ChapterDetectionConfig(BaseModel):
    """章节检测配置"""
    patterns: Optional[list] = Field(default=None, description="检测模式")
    min_chapter_length: Optional[int] = Field(default=500, description="最小章节长度")
    max_chapter_length: Optional[int] = Field(default=50000, description="最大章节长度")
    auto_title_detection: bool = Field(default=True, description="自动标题检测")
    custom_rules: Optional[Dict[str, Any]] = Field(default=None, description="自定义规则") 