"""
章节智能分块器服务
专门处理大章节的智能分块，解决大模型上下文限制问题
"""

import re
import logging
from typing import List, Dict

logger = logging.getLogger(__name__)


class ChapterChunker:
    """章节智能分块器 - 解决大模型上下文限制"""
    
    def __init__(self, max_tokens: int = 3000):
        self.max_tokens = max_tokens
        self.overlap_tokens = 200  # 重叠token数，保持上下文连贯性
    
    def chunk_chapter(self, chapter_content: str) -> List[Dict]:
        """智能分块章节内容"""
        # 1. 按自然段落分割
        paragraphs = self._split_by_paragraphs(chapter_content)
        
        # 2. 估算token数量
        chunks = []
        current_chunk = []
        current_tokens = 0
        
        for para in paragraphs:
            para_tokens = self._estimate_tokens(para)
            
            # 如果单个段落就超长，需要强制分割
            if para_tokens > self.max_tokens:
                if current_chunk:
                    chunks.append(self._create_chunk(current_chunk))
                    current_chunk = []
                    current_tokens = 0
                
                # 强制分割超长段落
                sub_chunks = self._force_split_paragraph(para)
                chunks.extend(sub_chunks)
                continue
            
            # 检查是否需要新建chunk
            if current_tokens + para_tokens > self.max_tokens:
                chunks.append(self._create_chunk(current_chunk))
                
                # 保持重叠上下文
                overlap_paras = self._get_overlap_context(current_chunk)
                current_chunk = overlap_paras + [para]
                current_tokens = sum(self._estimate_tokens(p) for p in current_chunk)
            else:
                current_chunk.append(para)
                current_tokens += para_tokens
        
        # 处理最后一个chunk
        if current_chunk:
            chunks.append(self._create_chunk(current_chunk))
        
        return chunks
    
    def _split_by_paragraphs(self, text: str) -> List[str]:
        """按自然段落分割文本"""
        # 按双换行符分割段落
        paragraphs = re.split(r'\n\s*\n', text.strip())
        # 过滤空段落
        return [p.strip() for p in paragraphs if p.strip()]
    
    def _estimate_tokens(self, text: str) -> int:
        """估算文本的token数量（中文按字符数估算）"""
        # 简单估算：中文字符 * 1.5 + 英文单词数
        chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
        english_words = len(re.findall(r'[a-zA-Z]+', text))
        return int(chinese_chars * 1.5 + english_words)
    
    def _create_chunk(self, paragraphs: List[str]) -> Dict:
        """创建分块数据"""
        content = "\n\n".join(paragraphs)
        return {
            "content": content,
            "paragraph_count": len(paragraphs),
            "estimated_tokens": self._estimate_tokens(content),
            "chunk_type": "normal"
        }
    
    def _force_split_paragraph(self, paragraph: str) -> List[Dict]:
        """强制分割超长段落"""
        # 按句号分割
        sentences = re.split(r'[。！？]', paragraph)
        chunks = []
        current_chunk = []
        current_tokens = 0
        
        for sentence in sentences:
            if not sentence.strip():
                continue
                
            sentence = sentence.strip() + "。"  # 恢复句号
            sentence_tokens = self._estimate_tokens(sentence)
            
            if current_tokens + sentence_tokens > self.max_tokens:
                if current_chunk:
                    chunks.append(self._create_chunk(current_chunk))
                current_chunk = [sentence]
                current_tokens = sentence_tokens
            else:
                current_chunk.append(sentence)
                current_tokens += sentence_tokens
        
        if current_chunk:
            chunks.append(self._create_chunk(current_chunk))
        
        return chunks
    
    def _get_overlap_context(self, paragraphs: List[str]) -> List[str]:
        """获取重叠上下文"""
        if not paragraphs:
            return []
        
        # 取最后1-2个段落作为重叠上下文
        overlap_tokens = 0
        overlap_paras = []
        
        for para in reversed(paragraphs):
            para_tokens = self._estimate_tokens(para)
            if overlap_tokens + para_tokens <= self.overlap_tokens:
                overlap_paras.insert(0, para)
                overlap_tokens += para_tokens
            else:
                break
        
        return overlap_paras 