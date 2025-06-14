"""
章节管理API
提供书籍章节管理功能
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Form
from sqlalchemy.orm import Session
from sqlalchemy import desc, asc, func, or_, and_
from typing import List, Optional, Dict, Any
import json
import logging
from datetime import datetime

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
    基于编程识别规则实现
    """
    try:
        # 初始化角色检测器
        detector = EnhancedCharacterDetector(character_analysis=True)
        
        # 处理章节文本
        chapter_info = {
            'id': chapter.id,
            'title': chapter.chapter_title,
            'number': chapter.chapter_number
        }
        
        # 执行角色识别和分析
        analysis_result = detector.process_chapter(chapter.content, chapter_info)
        
        return analysis_result
        
    except Exception as e:
        logger.error(f"分析章节 {chapter.id} 失败: {str(e)}")
        return {
            "chapter_id": chapter.id,
            "chapter_title": chapter.title,
            "chapter_number": chapter.chapter_number,
            "detected_characters": [],
            "segments": [],
            "error": str(e)
        }


class EnhancedCharacterDetector:
    """
    增强的角色检测器
    基于编程识别规则，支持情绪检测
    """
    
    def __init__(self, character_analysis=True):
        self.character_analysis = character_analysis
        
        # 角色性格分析模式（用于推断角色基本属性）
        self.character_traits = {
            'gentle': {
                'keywords': ['温柔', '轻声', '柔声', '细声', '温和', '和蔼', '慈祥'],
                'speech_patterns': ['轻声道', '温和地说', '柔声说'],
                'default_tts': {'time_step': 35, 'p_w': 1.2, 't_w': 2.8}
            },
            'fierce': {
                'keywords': ['凶猛', '暴躁', '粗暴', '凶狠', '狂暴', '霸道'],
                'speech_patterns': ['怒吼', '咆哮', '大喝', '厉声'],
                'default_tts': {'time_step': 28, 'p_w': 1.6, 't_w': 3.2}
            },
            'calm': {
                'keywords': ['沉稳', '冷静', '淡定', '从容', '镇定', '平静'],
                'speech_patterns': ['淡淡地说', '平静地道', '从容说'],
                'default_tts': {'time_step': 32, 'p_w': 1.4, 't_w': 3.0}
            },
            'lively': {
                'keywords': ['活泼', '开朗', '爽朗', '欢快', '兴奋', '热情'],
                'speech_patterns': ['兴奋地说', '欢快地道', '爽朗笑道'],
                'default_tts': {'time_step': 30, 'p_w': 1.3, 't_w': 2.9}
            }
        }
        
        # 排除词汇列表
        self.excluded_words = [
            '这个', '那个', '什么', '哪里', '为什么', '怎么',
            '可是', '但是', '所以', '因为', '如果', '虽然',
            '遇到', '慢慢', '而这', '这一', '那一', '当他', '当她',
            '此时', '此后', '然后', '接着', '最后', '从那', '经过',
            '神奇', '在一', '正发', '无奈', '尽管', '自言自语',
            '心想', '暗想', '暗道', '心道', '想道', '思考'
        ]
    
    def process_chapter(self, chapter_text: str, chapter_info: dict):
        """处理章节文本，返回角色分析结果"""
        
        # 分割文本为段落
        segments = self.segment_text(chapter_text)
        
        # 角色统计
        character_stats = {}
        processed_segments = []
        
        for i, segment_text in enumerate(segments):
            # 检测说话人
            speaker_result = self.detect_speaker_enhanced(segment_text)
            
            # 判断是否为对话
            is_dialogue = speaker_result['speaker'] != '旁白'
            
            # 统计角色信息
            speaker = speaker_result['speaker']
            if speaker not in character_stats:
                character_stats[speaker] = {
                    'name': speaker,
                    'frequency': 0,
                    'speech_samples': [],  # 收集说话样本用于性格分析
                    'first_appearance_segment': i,
                    'is_dialogue_character': is_dialogue
                }
            
            character_stats[speaker]['frequency'] += 1
            
            # 收集说话样本（用于后续性格分析）
            if is_dialogue and len(character_stats[speaker]['speech_samples']) < 10:
                character_stats[speaker]['speech_samples'].append(segment_text)
            
            # 构建段落结果
            processed_segments.append({
                'segment_order': i,
                'text': segment_text,
                'speaker': speaker,
                'confidence': speaker_result['confidence'],
                'detection_rule': speaker_result['rule'],
                'is_dialogue': is_dialogue
            })
        
        # 生成角色列表
        detected_characters = []
        for char_name, stats in character_stats.items():
            if char_name != '旁白':  # 排除旁白
                # 分析角色性格特征
                character_trait = self.analyze_character_trait(stats['speech_samples'])
                
                # 推荐基本信息
                character_info = self.generate_character_info(char_name, stats, character_trait)
                
                detected_characters.append({
                    'name': char_name,
                    'frequency': stats['frequency'],
                    'character_trait': character_trait,
                    'first_appearance': stats['first_appearance_segment'],
                    'is_main_character': stats['frequency'] >= 3,  # 出现3次以上认为是主要角色
                    'recommended_config': character_info
                })
        
        # 按出现频率排序
        detected_characters.sort(key=lambda x: x['frequency'], reverse=True)
        
        return {
            'chapter_id': chapter_info['id'],
            'chapter_title': chapter_info['title'],
            'chapter_number': chapter_info['number'],
            'detected_characters': detected_characters,
            'segments': processed_segments,
            'processing_stats': {
                'total_segments': len(processed_segments),
                'dialogue_segments': len([s for s in processed_segments if s['is_dialogue']]),
                'narration_segments': len([s for s in processed_segments if not s['is_dialogue']]),
                'total_characters': len(detected_characters),
                'main_characters': len([c for c in detected_characters if c['is_main_character']])
            }
        }
    
    def segment_text(self, text: str) -> List[str]:
        """将文本分割为段落"""
        # 按句号、感叹号、问号分割
        import re
        segments = re.split(r'[。！？]', text)
        
        # 清理空段落和过短段落
        cleaned_segments = []
        for segment in segments:
            segment = segment.strip()
            if len(segment) > 5:  # 至少5个字符
                cleaned_segments.append(segment)
        
        return cleaned_segments
    
    def detect_speaker_enhanced(self, text: str) -> dict:
        """
        增强的说话人检测
        基于编程识别规则的7层检测模式
        """
        text = text.strip()
        if not text:
            return {'speaker': '旁白', 'confidence': 0.0, 'rule': 'empty'}
        
        # 1. 混合文本分离模式（最高优先级）
        mixed_result = self.detect_mixed_text(text)
        if mixed_result['matched']:
            return mixed_result
        
        # 2. 直接引语模式
        direct_quote_result = self.detect_direct_quote(text)
        if direct_quote_result['matched']:
            return direct_quote_result
        
        # 3. 对话标记模式
        dialogue_marker_result = self.detect_dialogue_marker(text)
        if dialogue_marker_result['matched']:
            return dialogue_marker_result
        
        # 4. 引号对话模式
        quote_dialogue_result = self.detect_quote_dialogue(text)
        if quote_dialogue_result['matched']:
            return quote_dialogue_result
        
        # 5. 对话动词模式
        dialogue_verb_result = self.detect_dialogue_verb(text)
        if dialogue_verb_result['matched']:
            return dialogue_verb_result
        
        # 6. 姓名模式识别
        name_pattern_result = self.detect_name_pattern(text)
        if name_pattern_result['matched']:
            return name_pattern_result
        
        # 7. 旁白识别模式（最低优先级，兜底策略）
        return {'speaker': '旁白', 'confidence': 0.8, 'rule': 'narration'}
    
    def detect_mixed_text(self, text: str) -> dict:
        """检测混合文本分离模式"""
        import re
        
        # 混合文本模式：叙述+对话标记+对话内容
        patterns = [
            # 匹配：白骨精不胜欢喜，自言自语道："造化！"
            r'^.+?([^，。！？\s]{2,6})[说道讲叫喊问答回复表示][:：]',
            # 匹配：悟空愤怒地喝道："妖怪！"  
            r'^.+?([^，。！？\s]{2,6})[愤怒地|高兴地|悲伤地|惊讶地|淡淡地]*[说道讲叫喊问答回复表示喝][:：]',
            # 匹配：张三说："你好"
            r'^([^，。！？\s]{2,6})[说道讲叫喊问答回复表示][:：]'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                speaker = match.group(1).strip()
                # 清理可能的修饰词和动词
                speaker = re.sub(r'[愤怒地|高兴地|悲伤地|惊讶地|淡淡地|轻声地|大声地|说|道|讲|叫|喊|问|答|回复|表示|喝]', '', speaker)
                
                if self.validate_speaker(speaker):
                    return {
                        'speaker': speaker,
                        'confidence': 0.95,
                        'rule': 'mixed_text',
                        'matched': True
                    }
        
        return {'matched': False}
    
    def detect_direct_quote(self, text: str) -> dict:
        """检测直接引语模式"""
        import re
        
        patterns = [
            r'^([^""''「」『』：:，。！？\s]{2,6})[说道讲叫喊问答回复表示][:：][""''「」『』]',
            r'^([^""''「」『』：:，。！？\s]{2,6})[说道讲叫喊问答回复表示][""''「」『』]'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                speaker = match.group(1).strip()
                if self.validate_speaker(speaker):
                    return {
                        'speaker': speaker,
                        'confidence': 0.9,
                        'rule': 'direct_quote',
                        'matched': True
                    }
        
        return {'matched': False}
    
    def detect_dialogue_marker(self, text: str) -> dict:
        """检测对话标记模式"""
        import re
        
        pattern = r'^([^：:，。！？\s]{2,6})[:：]'
        match = re.search(pattern, text)
        
        if match:
            speaker = match.group(1).strip()
            if self.validate_speaker(speaker):
                return {
                    'speaker': speaker,
                    'confidence': 0.85,
                    'rule': 'dialogue_marker',
                    'matched': True
                }
        
        return {'matched': False}
    
    def detect_quote_dialogue(self, text: str) -> dict:
        """检测引号对话模式"""
        import re
        
        # 检查是否包含引号
        if any(quote in text for quote in ['"', '"', '"', '「', '」', '『', '』', "'", "'"]):
            patterns = [
                # 匹配："好主意！"王五兴奋地说道
                r'[""''「」『』][^""''「」『』]+[""''「」『』]([^，。！？\s]{2,6})[^说道]*[说道]',
                # 匹配：王五说："好主意！"
                r'^([^""''「」『』，。！？\s]{2,6})[^""''「」『』]{0,10}[说道讲叫喊问答回复表示]*[""''「」『』]'
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, text)
                if matches:
                    for speaker in matches:
                        speaker = speaker.strip()
                        # 清理修饰词和动词
                        speaker = re.sub(r'[兴奋地|愤怒地|高兴地|悲伤地|惊讶地|淡淡地|轻声地|大声地|说|道|讲|叫|喊|问|答|回复|表示|喝]', '', speaker)
                        
                        if self.validate_speaker(speaker):
                            return {
                                'speaker': speaker,
                                'confidence': 0.8,
                                'rule': 'quote_dialogue',
                                'matched': True
                            }
        
        return {'matched': False}
    
    def detect_dialogue_verb(self, text: str) -> dict:
        """检测对话动词模式"""
        import re
        
        pattern = r'^([^，。！？\s]{2,6})[说道讲叫喊问答回复表示]'
        match = re.search(pattern, text)
        
        if match:
            speaker = match.group(1).strip()
            if self.validate_speaker(speaker):
                return {
                    'speaker': speaker,
                    'confidence': 0.75,
                    'rule': 'dialogue_verb',
                    'matched': True
                }
        
        return {'matched': False}
    
    def detect_name_pattern(self, text: str) -> dict:
        """检测姓名模式"""
        import re
        
        patterns = [
            r'^([一-龯]{2,4})[^一-龯]',  # 中文姓名
            r'^([A-Z][a-z]+)[^a-z]'     # 英文姓名
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                speaker = match.group(1).strip()
                if self.validate_speaker(speaker):
                    return {
                        'speaker': speaker,
                        'confidence': 0.7,
                        'rule': 'name_pattern',
                        'matched': True
                    }
        
        return {'matched': False}
    
    def validate_speaker(self, speaker: str) -> bool:
        """验证说话人是否有效"""
        if not speaker or len(speaker) < 2 or len(speaker) > 6:
            return False
        
        # 排除标点符号
        if any(char in speaker for char in '。，！？；：'):
            return False
        
        # 排除排除词汇
        if speaker in self.excluded_words:
            return False
        
        # 排除时间词汇
        time_words = ['之后', '以后', '开始', '结束', '时候', '地方']
        if any(word in speaker for word in time_words):
            return False
        
        return True
    
    def analyze_character_trait(self, speech_samples: list) -> dict:
        """分析角色性格特征"""
        if not speech_samples:
            return {
                'trait': 'unknown',
                'confidence': 0.0,
                'description': '暂无足够信息分析性格'
            }
        
        trait_scores = {}
        
        # 分析所有说话样本
        for sample in speech_samples:
            for trait, config in self.character_traits.items():
                score = 0
                
                # 关键词匹配
                for keyword in config['keywords']:
                    if keyword in sample:
                        score += 2
                
                # 说话模式匹配
                for pattern in config['speech_patterns']:
                    if pattern in sample:
                        score += 3
                
                if trait not in trait_scores:
                    trait_scores[trait] = 0
                trait_scores[trait] += score
        
        # 确定主要性格特征
        if max(trait_scores.values()) > 0:
            dominant_trait = max(trait_scores.items(), key=lambda x: x[1])[0]
            confidence = trait_scores[dominant_trait] / (len(speech_samples) * 5)  # 标准化置信度
            
            trait_descriptions = {
                'gentle': '温柔和善，说话轻声细语',
                'fierce': '性格刚烈，说话直接有力',
                'calm': '沉稳冷静，处事从容不迫',
                'lively': '活泼开朗，充满活力'
            }
            
            return {
                'trait': dominant_trait,
                'confidence': min(confidence, 1.0),
                'description': trait_descriptions.get(dominant_trait, '性格特征待分析')
            }
        else:
            return {
                'trait': 'calm',  # 默认为沉稳
                'confidence': 0.3,
                'description': '性格相对平和，无明显特征'
            }
    
    def generate_character_info(self, char_name: str, stats: dict, character_trait: dict) -> dict:
        """生成角色推荐配置信息"""
        
        # 推荐性别
        gender = self.infer_gender(char_name)
        
        # 根据性格特征推荐TTS参数
        trait_name = character_trait['trait']
        default_tts = self.character_traits.get(trait_name, {}).get('default_tts', 
                                                                   {'time_step': 32, 'p_w': 1.4, 't_w': 3.0})
        
        # 生成角色描述
        description = self.generate_character_description(char_name, gender, character_trait, stats)
        
        return {
            'gender': gender,
            'personality': character_trait['trait'],
            'personality_description': character_trait['description'],
            'personality_confidence': character_trait['confidence'],
            'description': description,
            'recommended_tts_params': default_tts,
            'voice_type': f"{gender}_{character_trait['trait']}",  # 如: female_gentle, male_fierce
            'color': self.suggest_character_color(character_trait['trait'])
        }
    
    def infer_gender(self, char_name: str) -> str:
        """推断角色性别"""
        # 男性指示词
        male_indicators = [
            '王', '李', '张', '刘', '陈', '杨', '赵', '黄', '周', '吴', '徐', '孙', '马', '朱', '胡',
            '悟空', '八戒', '沙僧', '唐僧', '师父', '长老', '和尚', '道士', '书生', '公子', '少爷',
            '将军', '大王', '皇帝', '太子', '王子', '先生', '老爷'
        ]
        
        # 女性指示词  
        female_indicators = [
            '小', '美', '雅', '婷', '娜', '丽', '红', '芳', '燕', '玲', '花', '月', '春', '秋',
            '嫦娥', '仙女', '公主', '娘娘', '夫人', '小姐', '姑娘', '妹妹', '姐姐', '奶奶',
            '白骨精', '蜘蛛精', '狐狸精', '观音', '王母'
        ]
        
        # 检查男性指示词
        for indicator in male_indicators:
            if indicator in char_name:
                return 'male'
        
        # 检查女性指示词
        for indicator in female_indicators:
            if indicator in char_name:
                return 'female'
        
        # 默认返回female（因为温柔女声是默认音色）
        return 'female'
    
    def generate_character_description(self, char_name: str, gender: str, character_trait: dict, stats: dict) -> str:
        """生成角色描述"""
        gender_text = "男性" if gender == 'male' else "女性"
        frequency_text = "主要角色" if stats['frequency'] >= 3 else "次要角色"
        
        return f"{char_name}，{gender_text}{frequency_text}，{character_trait['description']}，在文本中出现{stats['frequency']}次。"
    
    def suggest_character_color(self, trait: str) -> str:
        """根据性格特征建议角色颜色"""
        color_mapping = {
            'gentle': '#FFB6C1',    # 浅粉色 - 温柔
            'fierce': '#FF6347',    # 番茄红 - 刚烈  
            'calm': '#4682B4',      # 钢蓝色 - 沉稳
            'lively': '#32CD32',    # 酸橙绿 - 活泼
            'unknown': '#D3D3D3'    # 浅灰色 - 未知
        }
        return color_mapping.get(trait, '#D3D3D3') 