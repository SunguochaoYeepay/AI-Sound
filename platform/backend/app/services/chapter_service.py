"""
章节管理服务
处理书籍章节的检测、分割、合并等操作
"""

import re
import hashlib
import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func

from ..models import Book, BookChapter
from ..exceptions import ServiceException
from ..detectors import ProgrammaticCharacterDetector, AdvancedCharacterDetector, OllamaCharacterDetector

logger = logging.getLogger(__name__)


class ChapterDetectionConfig:
    """章节检测配置类"""
    def __init__(
        self,
        method: str = "auto",
        patterns: List[str] = None,
        min_length: int = 500,
        max_length: int = 50000
    ):
        self.method = method
        self.patterns = patterns or [
            r"^第[一二三四五六七八九十\d]+[章节]",
            r"^Chapter \d+",
            r"^\d+\."
        ]
        self.min_length = min_length
        self.max_length = max_length


class ChapterDetector:
    """智能章节检测器"""
    
    def __init__(self, config: ChapterDetectionConfig):
        self.config = config
        
    def detect(self, content: str) -> List[Dict[str, Any]]:
        """检测章节分割点"""
        if self.config.method == "auto":
            return self._auto_detect(content)
        elif self.config.method == "regex":
            return self._regex_detect(content)
        else:
            raise ServiceException(f"不支持的检测方法: {self.config.method}")
    
    def _auto_detect(self, content: str) -> List[Dict[str, Any]]:
        """自动检测章节"""
        chapters = []
        lines = content.split('\n')
        current_chapter = {"title": "", "content": "", "start_line": 0}
        chapter_num = 1
        
        for i, line in enumerate(lines):
            line = line.strip()
            
            # 检查是否匹配章节标题模式
            is_chapter_title = False
            for pattern in self.config.patterns:
                if re.match(pattern, line):
                    is_chapter_title = True
                    break
            
            if is_chapter_title and current_chapter["content"]:
                # 完成当前章节
                if len(current_chapter["content"]) >= self.config.min_length:
                    chapters.append({
                        "chapter_number": chapter_num,
                        "title": current_chapter["title"] or f"第{chapter_num}章",
                        "content": current_chapter["content"].strip(),
                        "word_count": len(current_chapter["content"])
                    })
                    chapter_num += 1
                
                # 开始新章节
                current_chapter = {
                    "title": line,
                    "content": "",
                    "start_line": i
                }
            else:
                # 添加到当前章节内容
                if line:  # 跳过空行
                    current_chapter["content"] += line + "\n"
        
        # 处理最后一个章节
        if current_chapter["content"] and len(current_chapter["content"]) >= self.config.min_length:
            chapters.append({
                "chapter_number": chapter_num,
                "title": current_chapter["title"] or f"第{chapter_num}章",
                "content": current_chapter["content"].strip(),
                "word_count": len(current_chapter["content"])
            })
        
        return chapters
    
    def _regex_detect(self, content: str) -> List[Dict[str, Any]]:
        """基于正则表达式的章节检测"""
        # 实现更高级的正则检测逻辑
        # 这里先使用简化版本
        return self._auto_detect(content)


class ChapterService:
    """章节管理服务类"""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def detect_chapters_auto(self, book_id: int, config: ChapterDetectionConfig) -> List[Dict[str, Any]]:
        """自动检测书籍章节"""
        # 获取书籍
        book = self.db.query(Book).filter(Book.id == book_id).first()
        if not book:
            raise ServiceException("书籍不存在")
        
        # 检查是否已经分过章节
        existing_chapters = self.db.query(BookChapter).filter(BookChapter.book_id == book_id).count()
        if existing_chapters > 0:
            raise ServiceException("该书籍已经分过章节，请先清除现有章节")
        
        # 执行章节检测
        detector = ChapterDetector(config)
        chapters_data = detector.detect(book.content)
        
        if not chapters_data:
            raise ServiceException("未检测到有效章节")
        
        # 保存章节到数据库
        chapters = []
        for chapter_data in chapters_data:
            chapter = BookChapter(
                book_id=book_id,
                chapter_number=chapter_data["chapter_number"],
                chapter_title=chapter_data["title"],
                content=chapter_data["content"],
                word_count=chapter_data["word_count"]
            )
            self.db.add(chapter)
            chapters.append(chapter)
        
        # 更新书籍状态
        book.structure_status = 'structured'
        book.total_chapters = len(chapters)
        book.chapter_detection_method = config.method
        
        self.db.commit()
        
        return [chapter.to_dict() for chapter in chapters]
    
    async def get_chapters(self, book_id: int) -> List[Dict[str, Any]]:
        """获取书籍章节列表"""
        chapters = self.db.query(BookChapter).filter(
            BookChapter.book_id == book_id
        ).order_by(BookChapter.chapter_number).all()
        
        return [chapter.to_dict() for chapter in chapters]
    
    async def create_chapter(self, book_id: int, chapter_data: Dict[str, Any]) -> Dict[str, Any]:
        """手动创建章节"""
        # 验证书籍存在
        book = self.db.query(Book).filter(Book.id == book_id).first()
        if not book:
            raise ServiceException("书籍不存在")
        
        # 获取下一个章节编号
        max_number = self.db.query(func.max(BookChapter.chapter_number)).filter(
            BookChapter.book_id == book_id
        ).scalar() or 0
        
        # 创建章节
        chapter = BookChapter(
            book_id=book_id,
            chapter_number=max_number + 1,
            chapter_title=chapter_data.get("title", f"第{max_number + 1}章"),
            content=chapter_data["content"],
            word_count=len(chapter_data["content"])
        )
        
        self.db.add(chapter)
        self.db.commit()
        
        return chapter.to_dict()
    
    async def update_chapter(self, chapter_id: int, chapter_data: Dict[str, Any]) -> Dict[str, Any]:
        """更新章节信息"""
        chapter = self.db.query(BookChapter).filter(BookChapter.id == chapter_id).first()
        if not chapter:
            raise ServiceException("章节不存在")
        
        # 更新字段
        if "title" in chapter_data:
            chapter.chapter_title = chapter_data["title"]
        if "content" in chapter_data:
            chapter.content = chapter_data["content"]
            chapter.word_count = len(chapter_data["content"])
        
        self.db.commit()
        return chapter.to_dict()
    
    async def split_chapter(self, chapter_id: int, split_point: int) -> List[Dict[str, Any]]:
        """分割章节"""
        chapter = self.db.query(BookChapter).filter(BookChapter.id == chapter_id).first()
        if not chapter:
            raise ServiceException("章节不存在")
        
        content = chapter.content
        if split_point <= 0 or split_point >= len(content):
            raise ServiceException("分割点位置无效")
        
        # 分割内容
        content1 = content[:split_point].strip()
        content2 = content[split_point:].strip()
        
        if len(content1) < 100 or len(content2) < 100:
            raise ServiceException("分割后的章节内容过短")
        
        # 更新原章节
        chapter.content = content1
        chapter.word_count = len(content1)
        
        # 创建新章节
        new_chapter = BookChapter(
            book_id=chapter.book_id,
            chapter_number=chapter.chapter_number + 0.1,  # 临时编号
            chapter_title=f"{chapter.chapter_title} (续)",
            content=content2,
            word_count=len(content2)
        )
        self.db.add(new_chapter)
        
        # 重新排序章节编号
        await self._reorder_chapters(chapter.book_id)
        
        self.db.commit()
        
        return [chapter.to_dict(), new_chapter.to_dict()]
    
    async def merge_chapters(self, chapter_ids: List[int]) -> Dict[str, Any]:
        """合并章节"""
        if len(chapter_ids) < 2:
            raise ServiceException("至少需要选择2个章节进行合并")
        
        # 获取章节并按编号排序
        chapters = self.db.query(BookChapter).filter(
            BookChapter.id.in_(chapter_ids)
        ).order_by(BookChapter.chapter_number).all()
        
        if len(chapters) != len(chapter_ids):
            raise ServiceException("部分章节不存在")
        
        # 检查章节是否连续
        book_id = chapters[0].book_id
        for chapter in chapters:
            if chapter.book_id != book_id:
                raise ServiceException("不能合并不同书籍的章节")
        
        # 合并内容
        merged_title = chapters[0].chapter_title
        merged_content = "\n\n".join([ch.content for ch in chapters])
        merged_word_count = sum([ch.word_count for ch in chapters])
        
        # 更新第一个章节
        first_chapter = chapters[0]
        first_chapter.chapter_title = merged_title
        first_chapter.content = merged_content
        first_chapter.word_count = merged_word_count
        
        # 删除其他章节
        for chapter in chapters[1:]:
            self.db.delete(chapter)
        
        # 重新排序章节编号
        await self._reorder_chapters(book_id)
        
        self.db.commit()
        
        return first_chapter.to_dict()
    
    async def delete_chapters(self, book_id: int) -> bool:
        """删除书籍的所有章节"""
        self.db.query(BookChapter).filter(BookChapter.book_id == book_id).delete()
        
        # 重置书籍状态
        book = self.db.query(Book).filter(Book.id == book_id).first()
        if book:
            book.structure_status = 'raw'
            book.total_chapters = 0
        
        self.db.commit()
        return True
    
    async def _reorder_chapters(self, book_id: int):
        """重新排序章节编号"""
        chapters = self.db.query(BookChapter).filter(
            BookChapter.book_id == book_id
        ).order_by(BookChapter.chapter_number).all()
        
        for i, chapter in enumerate(chapters, 1):
            chapter.chapter_number = i
    
    def get_chapter_stats(self, book_id: int) -> Dict[str, Any]:
        """获取章节统计信息"""
        stats = self.db.query(
            func.count(BookChapter.id).label('total_chapters'),
            func.sum(BookChapter.word_count).label('total_words'),
            func.avg(BookChapter.word_count).label('avg_words'),
            func.min(BookChapter.word_count).label('min_words'),
            func.max(BookChapter.word_count).label('max_words')
        ).filter(BookChapter.book_id == book_id).first()
        
        return {
            "total_chapters": stats.total_chapters or 0,
            "total_words": stats.total_words or 0,
            "average_words": round(stats.avg_words or 0),
            "min_words": stats.min_words or 0,
            "max_words": stats.max_words or 0
        }


async def analyze_chapter_characters(chapter: BookChapter, detection_method: str, emotion_detection: bool):
    """
    分析单个章节的角色
    基于编程识别规则实现 - 增强版
    """
    try:
        logger.info(f"开始分析章节 {chapter.id}: {chapter.chapter_title}")
        
        content = chapter.content or ""
        if not content.strip():
            return {
                "chapter_id": chapter.id,
                "chapter_title": chapter.chapter_title,
                "chapter_number": chapter.chapter_number,
                "detected_characters": [],
                "segments": [],
                "processing_stats": {"total_segments": 0, "dialogue_segments": 0, "characters_found": 0}
            }
        
        # 优先使用Ollama智能检测器
        try:
            detector = OllamaCharacterDetector()
            logger.info(f"使用Ollama AI进行角色分析")
        except Exception as e:
            logger.warning(f"Ollama检测器初始化失败，使用规则检测器: {str(e)}")
            detector = AdvancedCharacterDetector()
        
        # 执行角色分析
        if isinstance(detector, OllamaCharacterDetector):
            analysis_result = await detector.analyze_text(content, {
                'chapter_id': chapter.id,
                'chapter_title': chapter.chapter_title,
                'chapter_number': chapter.chapter_number
            })
        else:
            analysis_result = detector.analyze_text(content, {
                'chapter_id': chapter.id,
                'chapter_title': chapter.chapter_title,
                'chapter_number': chapter.chapter_number
            })
        
        return analysis_result
        
    except Exception as e:
        logger.error(f"分析章节 {chapter.id} 失败: {str(e)}")
        return {
            "chapter_id": chapter.id,
            "chapter_title": chapter.chapter_title or "未知章节",
            "chapter_number": chapter.chapter_number,
            "detected_characters": [],
            "segments": [],
            "error": str(e)
        }


def get_chapter_content_stats(chapter: BookChapter) -> Dict[str, Any]:
    """获取章节内容统计信息"""
    import re
    
    content = chapter.content
    
    # 基本统计
    char_count = len(content)
    chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', content))
    english_words = len(re.findall(r'[a-zA-Z]+', content))
    
    # 估算token数量
    estimated_tokens = int(chinese_chars * 1.5 + english_words)
    
    # 段落统计
    paragraphs = re.split(r'\n\s*\n', content.strip())
    paragraph_count = len([p for p in paragraphs if p.strip()])
    
    # 对话统计
    dialogue_markers = ['"', '"', '"', '「', '」', '『', '』', "'", "'"]
    dialogue_count = sum(content.count(marker) for marker in dialogue_markers)
    
    # 推荐处理模式
    if estimated_tokens <= 3000:
        recommended_mode = "single"
        estimated_time = "30-60秒"
    else:
        recommended_mode = "distributed"
        estimated_time = "60-120秒"
    
    return {
        "chapter_info": {
            "id": chapter.id,
            "title": chapter.chapter_title
        },
        "content_stats": {
            "total_characters": char_count,
            "chinese_characters": chinese_chars,
            "english_words": english_words,
            "estimated_tokens": estimated_tokens,
            "paragraph_count": paragraph_count,
            "dialogue_markers": dialogue_count
        },
        "processing_recommendation": {
            "recommended_mode": recommended_mode,
            "estimated_time": estimated_time,
            "complexity": "simple" if estimated_tokens <= 1500 else "medium" if estimated_tokens <= 3000 else "complex"
        }
    }


def get_synthesis_preview(chapter: BookChapter, max_segments: int = 10) -> Dict[str, Any]:
    """获取章节合成预览"""
    # 使用简单的角色检测器进行快速预览
    detector = ProgrammaticCharacterDetector()
    
    # 取前1000字符进行预览分析
    preview_text = chapter.content[:1000] if len(chapter.content) > 1000 else chapter.content
    
    # 分析文本段落
    segments = detector.segment_text_with_speakers(preview_text)
    
    # 提取角色信息
    character_stats = detector.extract_dialogue_characters(segments)
    
    # 限制预览段落数量
    preview_segments = segments[:max_segments]
    
    return {
        "chapter_info": {
            "id": chapter.id,
            "title": chapter.chapter_title,
            "content_length": len(chapter.content),
            "preview_length": len(preview_text)
        },
        "preview_segments": preview_segments,
        "detected_characters": [
            {"name": name, "segment_count": count}
            for name, count in character_stats.items()
        ],
        "statistics": {
            "total_segments": len(segments),
            "preview_segments": len(preview_segments),
            "character_count": len(character_stats),
            "is_truncated": len(chapter.content) > 1000
        }
    } 