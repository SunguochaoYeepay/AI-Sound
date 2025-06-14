"""
章节管理API
提供书籍章节管理功能
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Form, UploadFile, File
from sqlalchemy.orm import Session
from sqlalchemy import desc, asc, func, or_, and_
from typing import List, Optional, Dict, Any
import json
import logging
from datetime import datetime
import re
import requests

from app.database import get_db
from app.models import BookChapter, Book, TextSegment
from app.utils import log_system_event

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/chapters", tags=["Chapters"])

@router.get("")
async def get_chapters(
    book_id: Optional[int] = Query(None, description="书籍ID过滤"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    search: str = Query("", description="搜索关键词"),
    status: str = Query("", description="状态过滤"),
    sort_by: str = Query("chapter_number", description="排序字段"),
    sort_order: str = Query("asc", description="排序方向"),
    db: Session = Depends(get_db)
):
    """获取章节列表"""
    try:
        # 构建查询
        query = db.query(BookChapter)
        
        # 书籍过滤
        if book_id:
            query = query.filter(BookChapter.book_id == book_id)
        
        # 搜索过滤
        if search:
            search_pattern = f"%{search}%"
            query = query.filter(
                or_(
                    BookChapter.title.like(search_pattern),
                    BookChapter.content.like(search_pattern)
                )
            )
        
        # 状态过滤
        if status:
            query = query.filter(BookChapter.analysis_status == status)
        
        # 排序
        sort_field = getattr(BookChapter, sort_by, BookChapter.chapter_number)
        if sort_order == "asc":
            query = query.order_by(asc(sort_field))
        else:
            query = query.order_by(desc(sort_field))
        
        # 统计总数
        total = query.count()
        
        # 分页
        offset = (page - 1) * page_size
        chapters = query.offset(offset).limit(page_size).all()
        
        # 转换为字典格式
        chapter_list = []
        for chapter in chapters:
            chapter_data = chapter.to_dict()
            
            # 添加书籍信息
            if chapter.book:
                chapter_data['book'] = {
                    "id": chapter.book.id,
                    "title": chapter.book.title,
                    "author": chapter.book.author
                }
            
            chapter_list.append(chapter_data)
        
        # 分页信息
        total_pages = (total + page_size - 1) // page_size
        
        return {
            "success": True,
            "data": chapter_list,
            "pagination": {
                "page": page,
                "pageSize": page_size,
                "total": total,
                "totalPages": total_pages,
                "hasMore": page < total_pages
            },
            "filters": {
                "book_id": book_id,
                "search": search,
                "status": status
            }
        }
        
    except Exception as e:
        logger.error(f"获取章节列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取章节列表失败: {str(e)}")

@router.get("/{chapter_id}")
async def get_chapter(
    chapter_id: int,
    db: Session = Depends(get_db)
):
    """获取章节详情"""
    try:
        chapter = db.query(BookChapter).filter(BookChapter.id == chapter_id).first()
        if not chapter:
            raise HTTPException(status_code=404, detail="章节不存在")
        
        chapter_data = chapter.to_dict()
        
        # 添加书籍信息
        if chapter.book:
            chapter_data['book'] = {
                "id": chapter.book.id,
                "title": chapter.book.title,
                "author": chapter.book.author
            }
        
        # 添加关联的文本分段信息
        segments = db.query(TextSegment).filter(
            TextSegment.book_chapter_id == chapter_id
        ).order_by(TextSegment.segment_order).all()
        
        chapter_data['segments'] = [
            {
                "id": seg.id,
                "order": seg.segment_order,
                "text": seg.text_content[:100] + "..." if len(seg.text_content) > 100 else seg.text_content,
                "status": seg.status,
                "detected_speaker": getattr(seg, 'detected_speaker', None)
            }
            for seg in segments
        ]
        
        return {
            "success": True,
            "data": chapter_data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取章节详情失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取章节详情失败: {str(e)}")

@router.patch("/{chapter_id}")
async def update_chapter(
    chapter_id: int,
    title: Optional[str] = Form(None),
    content: Optional[str] = Form(None),
    analysis_status: Optional[str] = Form(None),
    summary: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """更新章节信息"""
    try:
        chapter = db.query(BookChapter).filter(BookChapter.id == chapter_id).first()
        if not chapter:
            raise HTTPException(status_code=404, detail="章节不存在")
        
        # 更新字段
        if title is not None:
            if not title.strip():
                raise HTTPException(status_code=400, detail="章节标题不能为空")
            chapter.title = title.strip()
        
        if content is not None:
            chapter.content = content
            # 更新字数统计
            chapter.word_count = len(content.strip())
        
        if analysis_status is not None:
            if analysis_status not in ['pending', 'processing', 'completed', 'failed']:
                raise HTTPException(status_code=400, detail="无效的分析状态")
            chapter.analysis_status = analysis_status
        
        if summary is not None:
            chapter.summary = summary
        
        chapter.updated_at = datetime.utcnow()
        db.commit()
        
        # 记录更新日志
        await log_system_event(
            db=db,
            level="info",
            message=f"章节更新: {chapter.title}",
            module="chapters",
            details={"chapter_id": chapter_id}
        )
        
        return {
            "success": True,
            "message": "章节更新成功",
            "data": chapter.to_dict()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新章节失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"更新失败: {str(e)}")

@router.delete("/{chapter_id}")
async def delete_chapter(
    chapter_id: int,
    force: bool = Query(False, description="强制删除"),
    db: Session = Depends(get_db)
):
    """删除章节"""
    try:
        chapter = db.query(BookChapter).filter(BookChapter.id == chapter_id).first()
        if not chapter:
            raise HTTPException(status_code=404, detail="章节不存在")
        
        # 检查是否有关联的文本分段
        segment_count = db.query(func.count(TextSegment.id)).filter(
            TextSegment.book_chapter_id == chapter_id
        ).scalar()
        
        if not force and segment_count > 0:
            raise HTTPException(
                status_code=400, 
                detail=f"章节关联了 {segment_count} 个文本分段，请使用强制删除"
            )
        
        chapter_title = chapter.title
        
        # 删除关联的文本分段
        db.query(TextSegment).filter(TextSegment.book_chapter_id == chapter_id).delete()
        
        # 删除章节
        db.delete(chapter)
        db.commit()
        
        # 记录删除日志
        await log_system_event(
            db=db,
            level="info",
            message=f"章节删除: {chapter_title}",
            module="chapters",
            details={"chapter_id": chapter_id, "force": force}
        )
        
        return {
            "success": True,
            "message": "章节删除成功"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除章节失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"删除失败: {str(e)}")

@router.post("/{chapter_id}/split")
async def split_chapter(
    chapter_id: int,
    split_position: int = Form(..., description="分割位置"),
    new_title: str = Form(..., description="新章节标题"),
    db: Session = Depends(get_db)
):
    """分割章节"""
    try:
        chapter = db.query(BookChapter).filter(BookChapter.id == chapter_id).first()
        if not chapter:
            raise HTTPException(status_code=404, detail="章节不存在")
        
        if not chapter.content:
            raise HTTPException(status_code=400, detail="章节内容为空，无法分割")
        
        content_length = len(chapter.content)
        if split_position <= 0 or split_position >= content_length:
            raise HTTPException(status_code=400, detail="分割位置无效")
        
        if not new_title.strip():
            raise HTTPException(status_code=400, detail="新章节标题不能为空")
        
        # 分割内容
        original_content = chapter.content[:split_position]
        new_content = chapter.content[split_position:]
        
        # 更新原章节
        chapter.content = original_content
        chapter.word_count = len(original_content.strip())
        chapter.updated_at = datetime.utcnow()
        
        # 创建新章节
        new_chapter = BookChapter(
            book_id=chapter.book_id,
            chapter_number=chapter.chapter_number + 1,
            title=new_title.strip(),
            content=new_content,
            word_count=len(new_content.strip()),
            analysis_status='pending',
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        # 更新后续章节的编号
        db.query(BookChapter).filter(
            BookChapter.book_id == chapter.book_id,
            BookChapter.chapter_number > chapter.chapter_number
        ).update({
            BookChapter.chapter_number: BookChapter.chapter_number + 1
        })
        
        db.add(new_chapter)
        db.commit()
        db.refresh(new_chapter)
        
        # 记录分割日志
        await log_system_event(
            db=db,
            level="info",
            message=f"章节分割: {chapter.title} -> {new_title}",
            module="chapters",
            details={
                "original_chapter_id": chapter_id,
                "new_chapter_id": new_chapter.id,
                "split_position": split_position
            }
        )
        
        return {
            "success": True,
            "message": "章节分割成功",
            "data": {
                "original_chapter": chapter.to_dict(),
                "new_chapter": new_chapter.to_dict()
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"分割章节失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"分割失败: {str(e)}")

@router.post("/{chapter_id}/merge")
async def merge_chapters(
    chapter_id: int,
    target_chapter_id: int = Form(..., description="目标章节ID"),
    merge_direction: str = Form("after", description="合并方向: before/after"),
    db: Session = Depends(get_db)
):
    """合并章节"""
    try:
        if chapter_id == target_chapter_id:
            raise HTTPException(status_code=400, detail="不能与自己合并")
        
        chapter = db.query(BookChapter).filter(BookChapter.id == chapter_id).first()
        target_chapter = db.query(BookChapter).filter(BookChapter.id == target_chapter_id).first()
        
        if not chapter:
            raise HTTPException(status_code=404, detail="源章节不存在")
        if not target_chapter:
            raise HTTPException(status_code=404, detail="目标章节不存在")
        
        if chapter.book_id != target_chapter.book_id:
            raise HTTPException(status_code=400, detail="只能合并同一本书的章节")
        
        if merge_direction not in ["before", "after"]:
            raise HTTPException(status_code=400, detail="合并方向必须是 before 或 after")
        
        # 合并内容
        if merge_direction == "after":
            # 将目标章节内容合并到当前章节后面
            merged_content = chapter.content + "\n\n" + target_chapter.content
            merged_title = chapter.title
            keep_chapter = chapter
            delete_chapter = target_chapter
        else:
            # 将当前章节内容合并到目标章节前面
            merged_content = chapter.content + "\n\n" + target_chapter.content
            merged_title = target_chapter.title
            keep_chapter = target_chapter
            delete_chapter = chapter
        
        # 更新保留的章节
        keep_chapter.content = merged_content
        keep_chapter.word_count = len(merged_content.strip())
        keep_chapter.updated_at = datetime.utcnow()
        
        # 删除合并的章节
        delete_chapter_number = delete_chapter.chapter_number
        db.delete(delete_chapter)
        
        # 更新后续章节编号
        db.query(BookChapter).filter(
            BookChapter.book_id == chapter.book_id,
            BookChapter.chapter_number > delete_chapter_number
        ).update({
            BookChapter.chapter_number: BookChapter.chapter_number - 1
        })
        
        db.commit()
        
        # 记录合并日志
        await log_system_event(
            db=db,
            level="info",
            message=f"章节合并: {chapter.title} + {target_chapter.title}",
            module="chapters",
            details={
                "chapter_id": chapter_id,
                "target_chapter_id": target_chapter_id,
                "merge_direction": merge_direction,
                "kept_chapter_id": keep_chapter.id
            }
        )
        
        return {
            "success": True,
            "message": "章节合并成功",
            "data": keep_chapter.to_dict()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"合并章节失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"合并失败: {str(e)}")

@router.get("/{chapter_id}/statistics")
async def get_chapter_statistics(
    chapter_id: int,
    db: Session = Depends(get_db)
):
    """获取章节统计信息"""
    try:
        chapter = db.query(BookChapter).filter(BookChapter.id == chapter_id).first()
        if not chapter:
            raise HTTPException(status_code=404, detail="章节不存在")
        
        # 获取分段统计
        segment_stats = db.query(
            TextSegment.status,
            func.count(TextSegment.id).label('count')
        ).filter(TextSegment.book_chapter_id == chapter_id).group_by(TextSegment.status).all()
        
        status_counts = {stat.status: stat.count for stat in segment_stats}
        
        # 计算基础统计
        total_segments = sum(status_counts.values())
        
        return {
            "success": True,
            "data": {
                "chapter_id": chapter_id,
                "title": chapter.title,
                "word_count": chapter.word_count,
                "total_segments": total_segments,
                "segment_status_counts": status_counts,
                "analysis_status": chapter.analysis_status,
                "created_at": chapter.created_at.isoformat() if chapter.created_at else None,
                "updated_at": chapter.updated_at.isoformat() if chapter.updated_at else None
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取章节统计失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取统计失败: {str(e)}")

@router.post("/batch-character-analysis")
async def batch_character_analysis(
    request: dict,
    db: Session = Depends(get_db)
):
    """
    批量分析章节中的角色
    基于编程识别规则，从选定章节中发现所有角色
    """
    try:
        chapter_ids = request.get("chapter_ids", [])
        detection_method = request.get("detection_method", "programming")
        emotion_detection = request.get("emotion_detection", True)
        
        if not chapter_ids:
            raise HTTPException(status_code=400, detail="未提供章节ID列表")
        
        results = []
        
        for chapter_id in chapter_ids:
            chapter = db.query(BookChapter).filter(BookChapter.id == chapter_id).first()
            if not chapter:
                logger.warning(f"章节 {chapter_id} 不存在，跳过")
                continue
                
            # 使用增强的角色识别分析章节
            analysis_result = await analyze_chapter_characters(
                chapter, 
                detection_method, 
                emotion_detection
            )
            
            results.append(analysis_result)
        
        return {
            "success": True,
            "data": results,
            "message": f"成功分析 {len(results)} 个章节，发现角色信息"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"批量角色分析失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"分析失败: {str(e)}")


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


class AdvancedCharacterDetector:
    """
    高级角色检测器 - 基于多重规则和启发式方法
    """
    
    def __init__(self):
        # 对话标识符模式
        self.dialogue_patterns = [
            # 直接引语模式
            r'([^，。！？\s]{2,4})[说道讲问答回应喊叫嘟囔嘀咕][:：]?"([^"]+)"',
            r'"([^"]+)"[，。]?([^，。！？\s]{2,4})[说道讲问答]',
            
            # 冒号对话模式
            r'([^，。！？\s]{2,4})[：:]"([^"]+)"',
            r'([^，。！？\s]{2,4})[：:]\s*([^，。！？\n]+)',
            
            # 标记对话模式
            r'【([^】]+)】[：:]?([^，。！？\n]*)',
            r'〖([^〗]+)〗[：:]?([^，。！？\n]*)',
            
            # 动作描述中的角色
            r'([^，。！？\s]{2,4})[走来去到站坐躺跑跳]',
            r'([^，。！？\s]{2,4})[看见听到想起记得]',
            r'([^，。！？\s]{2,4})[笑哭怒喜惊]',
            
            # 称呼模式
            r'([^，。！？\s]{2,4})[师父师傅大人先生小姐]',
            r'[师父师傅大人先生小姐]([^，。！？\s]{2,4})',
        ]
        
        # 排除词汇 - 常见的非角色词汇
        self.excluded_words = {
            '这个', '那个', '什么', '哪里', '为什么', '怎么', '可是', '但是', '所以', '因为',
            '如果', '虽然', '遇到', '慢慢', '而这', '这一', '那一', '当他', '当她', '此时',
            '此后', '然后', '接着', '最后', '从那', '经过', '神奇', '在一', '正发', '无奈',
            '尽管', '自言', '心想', '暗想', '暗道', '心道', '想道', '思考', '突然', '忽然',
            '原来', '果然', '竟然', '居然', '当然', '自然', '显然', '明显', '清楚', '知道',
            '看到', '听到', '感到', '觉得', '认为', '以为', '似乎', '好像', '仿佛', '犹如'
        }
        
        # 角色性格关键词
        self.personality_keywords = {
            'gentle': ['温柔', '轻声', '柔声', '细声', '温和', '和蔼', '慈祥', '温柔地', '轻声道'],
            'fierce': ['凶猛', '暴躁', '粗暴', '凶狠', '狂暴', '霸道', '怒吼', '咆哮', '大喝', '厉声'],
            'calm': ['沉稳', '冷静', '淡定', '从容', '镇定', '平静', '淡淡地', '平静地', '从容说'],
            'lively': ['活泼', '开朗', '爽朗', '欢快', '兴奋', '热情', '兴奋地', '欢快地', '爽朗笑'],
            'wise': ['智慧', '睿智', '聪明', '机智', '深思', '沉思', '思索', '深思熟虑'],
            'brave': ['勇敢', '英勇', '无畏', '果敢', '坚毅', '刚强', '勇气', '胆量']
        }
        
        # 性别推断关键词
        self.gender_keywords = {
            'male': ['师父', '师傅', '大人', '先生', '公子', '少爷', '老爷', '爷爷', '父亲', '爸爸'],
            'female': ['小姐', '姑娘', '夫人', '娘子', '女士', '奶奶', '母亲', '妈妈', '阿姨']
        }
    
    def analyze_text(self, text: str, chapter_info: dict):
        """分析文本中的角色"""
        
        # 1. 分段处理
        segments = self._split_into_segments(text)
        
        # 2. 角色提取
        character_candidates = self._extract_characters(segments)
        
        # 3. 角色验证和过滤
        valid_characters = self._validate_characters(character_candidates, text)
        
        # 4. 角色属性分析
        analyzed_characters = self._analyze_character_attributes(valid_characters, text)
        
        # 5. 构建返回结果
        return {
            "chapter_id": chapter_info['chapter_id'],
            "chapter_title": chapter_info['chapter_title'],
            "chapter_number": chapter_info['chapter_number'],
            "detected_characters": analyzed_characters,
            "segments": [],  # 可以后续添加段落分析
            "processing_stats": {
                "total_segments": len(segments),
                "dialogue_segments": len([s for s in segments if self._is_dialogue(s)]),
                "characters_found": len(analyzed_characters)
            }
        }
    
    def _split_into_segments(self, text: str):
        """将文本分割为段落"""
        import re
        # 按句号、感叹号、问号分割，保留标点
        segments = re.split(r'([。！？])', text)
        
        # 重新组合句子
        sentences = []
        for i in range(0, len(segments)-1, 2):
            if i+1 < len(segments):
                sentence = segments[i] + segments[i+1]
                if sentence.strip():
                    sentences.append(sentence.strip())
        
        return sentences
    
    def _extract_characters(self, segments):
        """从段落中提取角色候选"""
        import re
        character_mentions = {}
        
        for segment_idx, segment in enumerate(segments):
            for pattern in self.dialogue_patterns:
                matches = re.findall(pattern, segment)
                for match in matches:
                    # 处理不同的匹配组
                    if isinstance(match, tuple):
                        for name in match:
                            if name and len(name) >= 2 and len(name) <= 6:
                                if self._is_valid_character_name(name):
                                    if name not in character_mentions:
                                        character_mentions[name] = {
                                            'frequency': 0,
                                            'segments': [],
                                            'contexts': []
                                        }
                                    character_mentions[name]['frequency'] += 1
                                    character_mentions[name]['segments'].append(segment_idx)
                                    character_mentions[name]['contexts'].append(segment)
                    else:
                        name = match
                        if name and len(name) >= 2 and len(name) <= 6:
                            if self._is_valid_character_name(name):
                                if name not in character_mentions:
                                    character_mentions[name] = {
                                        'frequency': 0,
                                        'segments': [],
                                        'contexts': []
                                    }
                                character_mentions[name]['frequency'] += 1
                                character_mentions[name]['segments'].append(segment_idx)
                                character_mentions[name]['contexts'].append(segment)
        
        return character_mentions
    
    def _is_valid_character_name(self, name: str) -> bool:
        """验证是否为有效的角色名"""
        # 过滤排除词汇
        if name in self.excluded_words:
            return False
        
        # 过滤纯数字或特殊字符
        import re
        if re.match(r'^[\d\s\W]+$', name):
            return False
        
        # 过滤过短或过长的名字
        if len(name) < 2 or len(name) > 6:
            return False
        
        # 过滤常见的非角色词汇
        non_character_patterns = [
            r'^[的地得]',  # 助词开头
            r'[的地得]$',  # 助词结尾
            r'^[在从到]',  # 介词开头
            r'^[和与及]',  # 连词开头
        ]
        
        for pattern in non_character_patterns:
            if re.match(pattern, name):
                return False
        
        return True
    
    def _validate_characters(self, candidates: dict, full_text: str):
        """验证和过滤角色候选"""
        valid_characters = {}
        
        for name, data in candidates.items():
            # 频率过滤：至少出现2次
            if data['frequency'] >= 2:
                valid_characters[name] = data
            # 或者在全文中有多次提及
            elif full_text.count(name) >= 3:
                data['frequency'] = full_text.count(name)
                valid_characters[name] = data
        
        return valid_characters
    
    def _analyze_character_attributes(self, characters: dict, full_text: str):
        """分析角色属性"""
        analyzed_characters = []
        
        for name, data in characters.items():
            # 分析性格特征
            personality = self._analyze_personality(data['contexts'])
            
            # 推断性别
            gender = self._infer_gender(name, data['contexts'])
            
            # 生成角色配置
            character_config = {
                'name': name,
                'frequency': data['frequency'],
                'character_trait': {
                    'trait': personality['trait'],
                    'confidence': personality['confidence'],
                    'description': personality['description']
                },
                'first_appearance': min(data['segments']) + 1 if data['segments'] else 1,
                'is_main_character': data['frequency'] >= 5,  # 出现5次以上为主要角色
                'recommended_config': {
                    'gender': gender,
                    'personality': personality['trait'],
                    'personality_description': personality['description'],
                    'personality_confidence': personality['confidence'],
                    'description': f'{name}，{gender}角色，{personality["description"]}，在文本中出现{data["frequency"]}次。',
                    'recommended_tts_params': self._get_tts_params(personality['trait']),
                    'voice_type': f'{gender}_{personality["trait"]}',
                    'color': self._get_character_color(personality['trait'])
                }
            }
            
            analyzed_characters.append(character_config)
        
        # 按频率排序
        analyzed_characters.sort(key=lambda x: x['frequency'], reverse=True)
        
        return analyzed_characters
    
    def _analyze_personality(self, contexts: list):
        """分析角色性格"""
        personality_scores = {trait: 0 for trait in self.personality_keywords.keys()}
        
        # 统计性格关键词
        for context in contexts:
            for trait, keywords in self.personality_keywords.items():
                for keyword in keywords:
                    if keyword in context:
                        personality_scores[trait] += 1
        
        # 找出最高分的性格特征
        if max(personality_scores.values()) > 0:
            dominant_trait = max(personality_scores, key=personality_scores.get)
            confidence = min(personality_scores[dominant_trait] / len(contexts), 1.0)
        else:
            dominant_trait = 'calm'  # 默认性格
            confidence = 0.3
        
        trait_descriptions = {
            'gentle': '性格温柔，说话轻声细语',
            'fierce': '性格刚烈，说话直接有力',
            'calm': '性格沉稳，处事冷静',
            'lively': '性格活泼，充满活力',
            'wise': '智慧睿智，深思熟虑',
            'brave': '勇敢果敢，无所畏惧'
        }
        
        return {
            'trait': dominant_trait,
            'confidence': confidence,
            'description': trait_descriptions.get(dominant_trait, '性格温和')
        }
    
    def _infer_gender(self, name: str, contexts: list):
        """推断角色性别"""
        male_score = 0
        female_score = 0
        
        # 基于称呼推断
        for context in contexts:
            for keyword in self.gender_keywords['male']:
                if keyword in context:
                    male_score += 1
            for keyword in self.gender_keywords['female']:
                if keyword in context:
                    female_score += 1
        
        # 基于名字推断（简单规则）
        common_male_chars = ['龙', '虎', '豹', '鹰', '狼', '雄', '强', '刚', '勇', '威']
        common_female_chars = ['凤', '燕', '莺', '花', '月', '雪', '玉', '珠', '美', '丽']
        
        for char in common_male_chars:
            if char in name:
                male_score += 0.5
        
        for char in common_female_chars:
            if char in name:
                female_score += 0.5
        
        return 'male' if male_score > female_score else 'female'
    
    def _get_tts_params(self, personality: str):
        """根据性格获取TTS参数"""
        params_map = {
            'gentle': {'time_step': 35, 'p_w': 1.2, 't_w': 2.8},
            'fierce': {'time_step': 28, 'p_w': 1.6, 't_w': 3.2},
            'calm': {'time_step': 32, 'p_w': 1.4, 't_w': 3.0},
            'lively': {'time_step': 30, 'p_w': 1.3, 't_w': 2.9},
            'wise': {'time_step': 34, 'p_w': 1.3, 't_w': 3.1},
            'brave': {'time_step': 29, 'p_w': 1.5, 't_w': 3.1}
        }
        return params_map.get(personality, {'time_step': 32, 'p_w': 1.4, 't_w': 3.0})
    
    def _get_character_color(self, personality: str):
        """根据性格获取角色颜色"""
        color_map = {
            'gentle': '#FFB6C1',  # 浅粉色
            'fierce': '#FF6347',  # 番茄红
            'calm': '#06b6d4',   # 青色
            'lively': '#32CD32', # 绿色
            'wise': '#9370DB',   # 紫色
            'brave': '#FF8C00'   # 橙色
        }
        return color_map.get(personality, '#06b6d4')
    
    def _is_dialogue(self, segment: str):
        """判断段落是否包含对话"""
        dialogue_indicators = ['"', '"', '"', '：', ':', '说', '道', '问', '答', '叫', '喊']
        return any(indicator in segment for indicator in dialogue_indicators)

class OllamaCharacterDetector:
    """
    基于Ollama大模型的智能角色检测器
    """
    
    def __init__(self, model_name: str = "gemma3:27b", ollama_url: str = "http://localhost:11434"):
        self.model_name = model_name
        self.ollama_url = ollama_url
        self.api_url = f"{ollama_url}/api/generate"
        
    def analyze_text(self, text: str, chapter_info: dict) -> dict:
        """使用Ollama分析文本中的角色"""
        try:
            # 构建提示词
            prompt = self._build_character_analysis_prompt(text)
            
            # 调用Ollama API
            response = self._call_ollama(prompt)
            
            if response:
                # 解析Ollama返回的结果
                characters = self._parse_ollama_response(response)
                
                return {
                    "chapter_id": chapter_info['chapter_id'],
                    "chapter_title": chapter_info['chapter_title'],
                    "chapter_number": chapter_info['chapter_number'],
                    "detected_characters": characters,
                    "segments": [],
                    "processing_stats": {
                        "total_segments": len(text.split('。')),
                        "dialogue_segments": len([s for s in text.split('。') if any(marker in s for marker in ['"', '说', '道', '：'])]),
                        "characters_found": len(characters),
                        "analysis_method": "ollama_ai"
                    }
                }
            else:
                # 如果Ollama调用失败，回退到规则方法
                logger.warning("Ollama调用失败，回退到规则方法")
                fallback_detector = AdvancedCharacterDetector()
                return fallback_detector.analyze_text(text, chapter_info)
                
        except Exception as e:
            logger.error(f"Ollama角色分析失败: {str(e)}")
            # 回退到规则方法
            fallback_detector = AdvancedCharacterDetector()
            return fallback_detector.analyze_text(text, chapter_info)
    
    def _build_character_analysis_prompt(self, text: str) -> str:
        """构建角色分析提示词"""
        prompt = f"""请分析以下文本中的所有角色，并以JSON格式返回结果。

文本内容：
{text[:2000]}  # 限制文本长度避免token过多

请识别文本中的所有角色，并为每个角色提供以下信息：
1. 完整的角色名称（如"孙悟空"而不是"悟空说"或"空"）
2. 在文本中的出现频次
3. 性别（male/female）
4. 性格特征（从以下选择：gentle温柔、fierce刚烈、calm沉稳、lively活泼、wise智慧、brave勇敢）
5. 性格描述
6. 是否为主要角色（出现5次以上）

注意事项：
- 忽略标点符号和动作描述词
- 合并相同角色的不同称呼（如"悟空"和"孙悟空"）
- 排除非角色词汇（如"这个"、"那个"、"什么"等）
- 确保角色名称完整且准确

请严格按照以下JSON格式返回：
```json
[
  {{
    "name": "角色完整名称",
    "frequency": 出现次数,
    "gender": "male/female",
    "personality": "性格类型",
    "personality_description": "性格描述",
    "is_main_character": true/false,
    "confidence": 0.8
  }}
]
```

只返回JSON数据，不要其他解释文字。"""
        
        return prompt
    
    def _call_ollama(self, prompt: str) -> Optional[str]:
        """调用Ollama API"""
        try:
            payload = {
                "model": self.model_name,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.1,  # 降低随机性，提高一致性
                    "top_p": 0.9,
                    "max_tokens": 2000
                }
            }
            
            response = requests.post(
                self.api_url,
                json=payload,
                timeout=60  # 60秒超时
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get('response', '')
            else:
                logger.error(f"Ollama API调用失败: {response.status_code} - {response.text}")
                return None
                
        except requests.exceptions.Timeout:
            logger.error("Ollama API调用超时")
            return None
        except Exception as e:
            logger.error(f"Ollama API调用异常: {str(e)}")
            return None
    
    def _parse_ollama_response(self, response: str) -> List[Dict]:
        """解析Ollama返回的JSON结果"""
        try:
            # 提取JSON部分
            json_start = response.find('[')
            json_end = response.rfind(']') + 1
            
            if json_start != -1 and json_end != -1:
                json_str = response[json_start:json_end]
                characters_data = json.loads(json_str)
                
                # 转换为标准格式
                processed_characters = []
                for char_data in characters_data:
                    if isinstance(char_data, dict) and 'name' in char_data:
                        # 验证和清理角色名
                        name = self._clean_character_name(char_data.get('name', ''))
                        if name and len(name) >= 2:
                            processed_char = {
                                'name': name,
                                'frequency': char_data.get('frequency', 1),
                                'character_trait': {
                                    'trait': char_data.get('personality', 'calm'),
                                    'confidence': char_data.get('confidence', 0.8),
                                    'description': char_data.get('personality_description', '性格特征待分析')
                                },
                                'first_appearance': 1,
                                'is_main_character': char_data.get('is_main_character', False),
                                'recommended_config': {
                                    'gender': char_data.get('gender', 'female'),
                                    'personality': char_data.get('personality', 'calm'),
                                    'personality_description': char_data.get('personality_description', '性格特征待分析'),
                                    'personality_confidence': char_data.get('confidence', 0.8),
                                    'description': f"{name}，{char_data.get('gender', 'female')}角色，{char_data.get('personality_description', '性格特征待分析')}，在文本中出现{char_data.get('frequency', 1)}次。",
                                    'recommended_tts_params': self._get_tts_params(char_data.get('personality', 'calm')),
                                    'voice_type': f"{char_data.get('gender', 'female')}_{char_data.get('personality', 'calm')}",
                                    'color': self._get_character_color(char_data.get('personality', 'calm'))
                                }
                            }
                            processed_characters.append(processed_char)
                
                # 按频率排序
                processed_characters.sort(key=lambda x: x['frequency'], reverse=True)
                return processed_characters
            
            else:
                logger.error("无法从Ollama响应中提取JSON数据")
                return []
                
        except json.JSONDecodeError as e:
            logger.error(f"解析Ollama JSON响应失败: {str(e)}")
            logger.error(f"原始响应: {response}")
            return []
        except Exception as e:
            logger.error(f"处理Ollama响应异常: {str(e)}")
            return []
    
    def _clean_character_name(self, name: str) -> str:
        """清理角色名称"""
        if not name:
            return ""
        
        # 移除标点符号
        name = re.sub(r'["""''：:，。！？\s]', '', name)
        
        # 移除常见的动作词后缀
        action_suffixes = ['说', '道', '讲', '问', '答', '叫', '喊', '笑', '哭', '走', '来', '去']
        for suffix in action_suffixes:
            if name.endswith(suffix) and len(name) > len(suffix):
                name = name[:-len(suffix)]
        
        # 移除常见前缀
        prefixes = ['"', '"', '【', '〖']
        for prefix in prefixes:
            if name.startswith(prefix):
                name = name[1:]
        
        return name.strip()
    
    def _get_tts_params(self, personality: str) -> Dict:
        """根据性格获取TTS参数"""
        params_map = {
            'gentle': {'time_step': 35, 'p_w': 1.2, 't_w': 2.8},
            'fierce': {'time_step': 28, 'p_w': 1.6, 't_w': 3.2},
            'calm': {'time_step': 32, 'p_w': 1.4, 't_w': 3.0},
            'lively': {'time_step': 30, 'p_w': 1.3, 't_w': 2.9},
            'wise': {'time_step': 34, 'p_w': 1.3, 't_w': 3.1},
            'brave': {'time_step': 29, 'p_w': 1.5, 't_w': 3.1}
        }
        return params_map.get(personality, {'time_step': 32, 'p_w': 1.4, 't_w': 3.0})
    
    def _get_character_color(self, personality: str) -> str:
        """根据性格获取角色颜色"""
        color_map = {
            'gentle': '#FFB6C1',  # 浅粉色
            'fierce': '#FF6347',  # 番茄红
            'calm': '#06b6d4',   # 青色
            'lively': '#32CD32', # 绿色
            'wise': '#9370DB',   # 紫色
            'brave': '#FF8C00'   # 橙色
        }
        return color_map.get(personality, '#06b6d4') 