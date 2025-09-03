"""
上下文管理系统
实现智能上下文保持和关联分析，提升分析连贯性
"""

import json
import logging
from typing import Dict, Any, List, Optional, Set
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from app.services.intelligent_text_segmenter import intelligent_segmenter, TextSegment

logger = logging.getLogger(__name__)

class ContextType(Enum):
    """上下文类型枚举"""
    CHARACTER = "character"        # 角色上下文
    SCENE = "scene"               # 场景上下文
    PLOT = "plot"                 # 情节上下文
    EMOTION = "emotion"           # 情感上下文
    TIME = "time"                 # 时间上下文
    LOCATION = "location"         # 地点上下文
    RELATIONSHIP = "relationship" # 关系上下文

@dataclass
class ContextItem:
    """上下文项数据类"""
    context_type: ContextType
    key: str
    value: Any
    confidence: float
    source_segment: int
    timestamp: datetime
    metadata: Dict[str, Any]

@dataclass
class ContextState:
    """上下文状态数据类"""
    session_id: str
    chapter_id: int
    current_segment: int
    context_items: Dict[ContextType, List[ContextItem]]
    context_graph: Dict[str, List[str]]
    last_updated: datetime

class ContextManager:
    """上下文管理器"""
    
    def __init__(self):
        self.context_states: Dict[str, ContextState] = {}
        self.context_rules = self._initialize_context_rules()
        self.similarity_threshold = 0.7
    
    def _initialize_context_rules(self) -> Dict[ContextType, Dict[str, Any]]:
        """初始化上下文规则"""
        return {
            ContextType.CHARACTER: {
                "description": "角色上下文规则",
                "priority": 1,
                "max_history": 10,
                "similarity_threshold": 0.8,
                "extraction_patterns": [
                    r'([^，。！？]+)(?:说|道|问|答|想|觉得|认为)',
                    r'([^，。！？]+)(?:的|地|得)([^，。！？]+)',
                    r'([^，。！？]+)(?:是|为|成为|变成)([^，。！？]+)'
                ]
            },
            ContextType.SCENE: {
                "description": "场景上下文规则",
                "priority": 2,
                "max_history": 8,
                "similarity_threshold": 0.75,
                "extraction_patterns": [
                    r'在([^，。！？]+)(?:中|里|内|上|下)',
                    r'([^，。！？]+)(?:的|地|得)([^，。！？]+)',
                    r'([^，。！？]+)(?:时|时候|期间)'
                ]
            },
            ContextType.PLOT: {
                "description": "情节上下文规则",
                "priority": 3,
                "max_history": 12,
                "similarity_threshold": 0.7,
                "extraction_patterns": [
                    r'([^，。！？]+)(?:后|之后|然后|接着)',
                    r'([^，。！？]+)(?:前|之前|以前|原先)',
                    r'([^，。！？]+)(?:因为|由于|所以|因此)'
                ]
            },
            ContextType.EMOTION: {
                "description": "情感上下文规则",
                "priority": 4,
                "max_history": 6,
                "similarity_threshold": 0.8,
                "extraction_patterns": [
                    r'([^，。！？]+)(?:感到|觉得|认为|感觉)([^，。！？]+)',
                    r'([^，。！？]+)(?:的|地|得)([^，。！？]+)',
                    r'([^，。！？]+)(?:表情|神态|语气)([^，。！？]+)'
                ]
            },
            ContextType.TIME: {
                "description": "时间上下文规则",
                "priority": 5,
                "max_history": 5,
                "similarity_threshold": 0.9,
                "extraction_patterns": [
                    r'([^，。！？]+)(?:时|时候|期间|时刻)',
                    r'([^，。！？]+)(?:前|之前|以前|原先)',
                    r'([^，。！？]+)(?:后|之后|然后|接着)'
                ]
            },
            ContextType.LOCATION: {
                "description": "地点上下文规则",
                "priority": 6,
                "max_history": 7,
                "similarity_threshold": 0.85,
                "extraction_patterns": [
                    r'在([^，。！？]+)(?:中|里|内|上|下)',
                    r'([^，。！？]+)(?:的|地|得)([^，。！？]+)',
                    r'([^，。！？]+)(?:附近|周围|旁边)'
                ]
            },
            ContextType.RELATIONSHIP: {
                "description": "关系上下文规则",
                "priority": 7,
                "max_history": 8,
                "similarity_threshold": 0.8,
                "extraction_patterns": [
                    r'([^，。！？]+)(?:的|地|得)([^，。！？]+)',
                    r'([^，。！？]+)(?:和|与|跟|同)([^，。！？]+)',
                    r'([^，。！？]+)(?:对|向|给|为)([^，。！？]+)'
                ]
            }
        }
    
    def create_context_session(
        self,
        session_id: str,
        chapter_id: int
    ) -> ContextState:
        """创建上下文会话"""
        context_state = ContextState(
            session_id=session_id,
            chapter_id=chapter_id,
            current_segment=0,
            context_items={context_type: [] for context_type in ContextType},
            context_graph={},
            last_updated=datetime.now()
        )
        
        self.context_states[session_id] = context_state
        logger.info(f"创建上下文会话: {session_id}, 章节: {chapter_id}")
        return context_state
    
    def update_context(
        self,
        session_id: str,
        segment: TextSegment,
        segment_index: int
    ) -> ContextState:
        """更新上下文"""
        if session_id not in self.context_states:
            raise ValueError(f"上下文会话 '{session_id}' 不存在")
        
        context_state = self.context_states[session_id]
        context_state.current_segment = segment_index
        context_state.last_updated = datetime.now()
        
        # 提取上下文信息
        self._extract_context_from_segment(context_state, segment, segment_index)
        
        # 更新上下文图
        self._update_context_graph(context_state)
        
        # 清理过期上下文
        self._cleanup_expired_context(context_state)
        
        logger.info(f"更新上下文: {session_id}, 分割 {segment_index}")
        return context_state
    
    def _extract_context_from_segment(
        self,
        context_state: ContextState,
        segment: TextSegment,
        segment_index: int
    ):
        """从分割中提取上下文信息"""
        content = segment.content
        
        for context_type, rules in self.context_rules.items():
            # 使用规则提取上下文
            extracted_items = self._extract_by_rules(content, context_type, rules, segment_index)
            
            # 添加到上下文状态
            if context_type not in context_state.context_items:
                context_state.context_items[context_type] = []
            
            context_state.context_items[context_type].extend(extracted_items)
    
    def _extract_by_rules(
        self,
        content: str,
        context_type: ContextType,
        rules: Dict[str, Any],
        segment_index: int
    ) -> List[ContextItem]:
        """根据规则提取上下文"""
        import re
        
        extracted_items = []
        patterns = rules["extraction_patterns"]
        
        for pattern in patterns:
            matches = re.finditer(pattern, content)
            for match in matches:
                # 提取关键信息
                key = self._extract_context_key(match, context_type)
                value = self._extract_context_value(match, context_type)
                
                if key and value:
                    # 计算置信度
                    confidence = self._calculate_extraction_confidence(match, content, context_type)
                    
                    # 创建上下文项
                    context_item = ContextItem(
                        context_type=context_type,
                        key=key,
                        value=value,
                        confidence=confidence,
                        source_segment=segment_index,
                        timestamp=datetime.now(),
                        metadata={
                            "pattern": pattern,
                            "match_text": match.group(0),
                            "position": match.span()
                        }
                    )
                    
                    extracted_items.append(context_item)
        
        return extracted_items
    
    def _extract_context_key(self, match, context_type: ContextType) -> Optional[str]:
        """提取上下文键"""
        try:
            if context_type == ContextType.CHARACTER:
                # 角色上下文：提取角色名称
                return match.group(1).strip()
            elif context_type == ContextType.SCENE:
                # 场景上下文：提取场景描述
                return match.group(1).strip()
            elif context_type == ContextType.PLOT:
                # 情节上下文：提取情节关键词
                return match.group(1).strip()
            elif context_type == ContextType.EMOTION:
                # 情感上下文：提取情感主体
                return match.group(1).strip()
            elif context_type == ContextType.TIME:
                # 时间上下文：提取时间描述
                return match.group(1).strip()
            elif context_type == ContextType.LOCATION:
                # 地点上下文：提取地点描述
                return match.group(1).strip()
            elif context_type == ContextType.RELATIONSHIP:
                # 关系上下文：提取关系主体
                return match.group(1).strip()
            else:
                return match.group(1).strip() if match.groups() else None
        except (IndexError, AttributeError):
            return None
    
    def _extract_context_value(self, match, context_type: ContextType) -> Optional[str]:
        """提取上下文值"""
        try:
            if context_type == ContextType.CHARACTER:
                # 角色上下文：提取角色特征或行为
                if len(match.groups()) >= 2:
                    return match.group(2).strip()
                return "mentioned"
            elif context_type == ContextType.SCENE:
                # 场景上下文：提取场景特征
                if len(match.groups()) >= 2:
                    return match.group(2).strip()
                return "described"
            elif context_type == ContextType.PLOT:
                # 情节上下文：提取情节发展
                if len(match.groups()) >= 2:
                    return match.group(2).strip()
                return "developed"
            elif context_type == ContextType.EMOTION:
                # 情感上下文：提取情感描述
                if len(match.groups()) >= 2:
                    return match.group(2).strip()
                return "expressed"
            elif context_type == ContextType.TIME:
                # 时间上下文：提取时间描述
                if len(match.groups()) >= 2:
                    return match.group(2).strip()
                return "specified"
            elif context_type == ContextType.LOCATION:
                # 地点上下文：提取地点描述
                if len(match.groups()) >= 2:
                    return match.group(2).strip()
                return "specified"
            elif context_type == ContextType.RELATIONSHIP:
                # 关系上下文：提取关系描述
                if len(match.groups()) >= 2:
                    return match.group(2).strip()
                return "established"
            else:
                return match.group(2).strip() if len(match.groups()) >= 2 else "extracted"
        except (IndexError, AttributeError):
            return "extracted"
    
    def _calculate_extraction_confidence(
        self,
        match,
        content: str,
        context_type: ContextType
    ) -> float:
        """计算提取置信度"""
        confidence = 0.6  # 基础置信度
        
        # 匹配长度因子
        match_length = len(match.group(0))
        if 5 <= match_length <= 50:
            confidence += 0.2
        elif match_length > 50:
            confidence += 0.1
        
        # 位置因子（句子开头或结尾）
        start_pos = match.start()
        end_pos = match.end()
        
        if start_pos < 20 or end_pos > len(content) - 20:
            confidence += 0.1
        
        # 上下文类型特定因子
        if context_type == ContextType.CHARACTER:
            # 角色名称通常较短且明确
            if 2 <= len(match.group(1)) <= 8:
                confidence += 0.1
        elif context_type == ContextType.TIME:
            # 时间描述通常包含时间词汇
            time_keywords = ['时', '时候', '期间', '前', '后', '之前', '之后']
            if any(keyword in match.group(0) for keyword in time_keywords):
                confidence += 0.1
        
        return min(confidence, 1.0)
    
    def _update_context_graph(self, context_state: ContextState):
        """更新上下文图"""
        # 构建上下文项之间的关联关系
        context_graph = {}
        
        for context_type, items in context_state.context_items.items():
            for item in items:
                key = f"{context_type.value}:{item.key}"
                
                if key not in context_graph:
                    context_graph[key] = []
                
                # 查找相关上下文项
                related_items = self._find_related_context_items(item, context_state)
                for related in related_items:
                    related_key = f"{related.context_type.value}:{related.key}"
                    if related_key not in context_graph[key]:
                        context_graph[key].append(related_key)
        
        context_state.context_graph = context_graph
    
    def _find_related_context_items(
        self,
        item: ContextItem,
        context_state: ContextState
    ) -> List[ContextItem]:
        """查找相关的上下文项"""
        related_items = []
        
        # 基于相似性和时间接近性查找相关项
        for context_type, items in context_state.context_items.items():
            for other_item in items:
                if other_item == item:
                    continue
                
                # 检查相似性
                if self._are_items_related(item, other_item):
                    related_items.append(other_item)
        
        return related_items
    
    def _are_items_related(self, item1: ContextItem, item2: ContextItem) -> bool:
        """检查两个上下文项是否相关"""
        # 时间接近性
        time_diff = abs((item1.timestamp - item2.timestamp).total_seconds())
        if time_diff > 300:  # 5分钟内
            return False
        
        # 分割接近性
        segment_diff = abs(item1.source_segment - item2.source_segment)
        if segment_diff > 3:  # 相邻3个分割内
            return False
        
        # 内容相似性
        similarity = self._calculate_item_similarity(item1, item2)
        return similarity >= self.similarity_threshold
    
    def _calculate_item_similarity(self, item1: ContextItem, item2: ContextItem) -> float:
        """计算两个上下文项的相似性"""
        # 基于键和值的相似性计算
        key_similarity = self._calculate_text_similarity(item1.key, item2.key)
        value_similarity = self._calculate_text_similarity(str(item1.value), str(item2.value))
        
        # 加权平均
        return key_similarity * 0.7 + value_similarity * 0.3
    
    def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """计算文本相似性"""
        # 简单的基于词汇的相似性计算
        words1 = set(text1.split())
        words2 = set(text2.split())
        
        if not words1 and not words2:
            return 1.0
        
        intersection = len(words1 & words2)
        union = len(words1 | words2)
        
        return intersection / union if union > 0 else 0.0
    
    def _cleanup_expired_context(self, context_state: ContextState):
        """清理过期的上下文"""
        current_time = datetime.now()
        
        for context_type, items in context_state.context_items.items():
            rules = self.context_rules[context_type]
            max_history = rules["max_history"]
            
            # 按时间排序，保留最新的项
            sorted_items = sorted(items, key=lambda x: x.timestamp, reverse=True)
            context_state.context_items[context_type] = sorted_items[:max_history]
    
    def get_context_summary(
        self,
        session_id: str,
        context_types: Optional[List[ContextType]] = None
    ) -> Dict[str, Any]:
        """获取上下文摘要"""
        if session_id not in self.context_states:
            return {}
        
        context_state = self.context_states[session_id]
        
        if context_types is None:
            context_types = list(ContextType)
        
        summary = {
            "session_id": context_state.session_id,
            "chapter_id": context_state.chapter_id,
            "current_segment": context_state.current_segment,
            "last_updated": context_state.last_updated.isoformat(),
            "context_summary": {}
        }
        
        for context_type in context_types:
            if context_type in context_state.context_items:
                items = context_state.context_items[context_type]
                summary["context_summary"][context_type.value] = {
                    "count": len(items),
                    "recent_items": [
                        {
                            "key": item.key,
                            "value": str(item.value),
                            "confidence": item.confidence,
                            "segment": item.source_segment
                        }
                        for item in items[-5:]  # 最近5项
                    ]
                }
        
        return summary
    
    def get_context_for_segment(
        self,
        session_id: str,
        segment_index: int,
        context_types: Optional[List[ContextType]] = None
    ) -> Dict[str, Any]:
        """获取特定分割的上下文"""
        if session_id not in self.context_states:
            return {}
        
        context_state = self.context_states[session_id]
        
        if context_types is None:
            context_types = list(ContextType)
        
        segment_context = {
            "segment_index": segment_index,
            "context_items": {},
            "related_context": {}
        }
        
        for context_type in context_types:
            if context_type in context_state.context_items:
                items = context_state.context_items[context_type]
                
                # 当前分割的上下文
                current_items = [item for item in items if item.source_segment == segment_index]
                segment_context["context_items"][context_type.value] = [
                    {
                        "key": item.key,
                        "value": str(item.value),
                        "confidence": item.confidence
                    }
                    for item in current_items
                ]
                
                # 相关上下文（相邻分割）
                related_items = []
                for item in items:
                    if abs(item.source_segment - segment_index) <= 2:
                        related_items.append({
                            "key": item.key,
                            "value": str(item.value),
                            "confidence": item.confidence,
                            "segment": item.source_segment
                        })
                
                segment_context["related_context"][context_type.value] = related_items
        
        return segment_context
    
    def get_context_graph(self, session_id: str) -> Dict[str, List[str]]:
        """获取上下文图"""
        if session_id not in self.context_states:
            return {}
        
        return self.context_states[session_id].context_graph.copy()
    
    def merge_context_sessions(
        self,
        source_session_id: str,
        target_session_id: str
    ) -> bool:
        """合并上下文会话"""
        if source_session_id not in self.context_states or target_session_id not in self.context_states:
            return False
        
        source_state = self.context_states[source_session_id]
        target_state = self.context_states[target_session_id]
        
        # 合并上下文项
        for context_type in ContextType:
            if context_type in source_state.context_items:
                if context_type not in target_state.context_items:
                    target_state.context_items[context_type] = []
                
                target_state.context_items[context_type].extend(
                    source_state.context_items[context_type]
                )
        
        # 更新上下文图
        self._update_context_graph(target_state)
        
        # 清理过期上下文
        self._cleanup_expired_context(target_state)
        
        # 删除源会话
        del self.context_states[source_session_id]
        
        logger.info(f"合并上下文会话: {source_session_id} -> {target_session_id}")
        return True

# 创建全局上下文管理器实例
context_manager = ContextManager()
