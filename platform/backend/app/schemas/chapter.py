"""
章节相关Schema定义
"""

from pydantic import BaseModel, Field
from typing import Optional
from .common import BaseResponseModel


class ChapterCreate(BaseModel):
    """创建章节请求"""
    book_id: int = Field(description="书籍ID")
    chapter_number: int = Field(ge=1, description="章节号")
    chapter_title: Optional[str] = Field(default=None, max_length=200, description="章节标题")
    content: str = Field(min_length=1, description="章节内容")


class ChapterUpdate(BaseModel):
    """更新章节请求"""
    chapter_title: Optional[str] = Field(default=None, max_length=200, description="章节标题")
    content: Optional[str] = Field(default=None, min_length=1, description="章节内容")


class ChapterResponse(BaseResponseModel):
    """章节响应"""
    book_id: int = Field(description="书籍ID")
    chapter_number: int = Field(description="章节号")
    chapter_title: Optional[str] = Field(description="章节标题")
    content: str = Field(description="章节内容")
    word_count: int = Field(description="字数统计")
    analysis_status: str = Field(description="分析状态")
    synthesis_status: str = Field(description="合成状态")


class ChapterSplitRequest(BaseModel):
    """章节分割请求"""
    split_points: list[int] = Field(description="分割点位置列表")
    new_titles: Optional[list[str]] = Field(default=None, description="新章节标题列表")


class ChapterMergeRequest(BaseModel):
    """章节合并请求"""
    target_chapters: list[int] = Field(min_items=2, description="要合并的章节ID列表")
    new_title: Optional[str] = Field(default=None, description="合并后的章节标题") 