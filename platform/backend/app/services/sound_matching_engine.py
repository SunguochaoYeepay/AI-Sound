"""
环境音智能匹配引擎 - LLM优化版本
支持精确匹配、LLM智能语义匹配和标签匹配
为新的环境音优化流程提供智能关联能力
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import asyncio
import re
import json
from difflib import SequenceMatcher

from app.models.environment_sound import EnvironmentSound
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from app.services.storyboard_analysis.llm_client import LLMClient
from app.utils.llm_config_loader import llm_config_loader

logger = logging.getLogger(__name__)

class MatchResult:
    """匹配结果数据类"""
    def __init__(self, sound_id: int, sound_name: str, match_type: str, 
                 confidence: float, similarity_score: float, reason: str):
        self.sound_id = sound_id
        self.sound_name = sound_name
        self.match_type = match_type  # exact, semantic, tag, fuzzy
        self.confidence = confidence
        self.similarity_score = similarity_score
        self.reason = reason
        self.matched_keywords = []
        
    def to_dict(self) -> Dict[str, Any]:
        return {
            'sound_id': self.sound_id,
            'sound_name': self.sound_name,
            'match_type': self.match_type,
            'confidence': self.confidence,
            'similarity_score': self.similarity_score,
            'reason': self.reason,
            'matched_keywords': self.matched_keywords
        }

class SoundMatchingEngine:
    """环境音智能匹配引擎 - LLM优化版本"""
    
    def __init__(self):
        # 初始化LLM客户端
        self.llm_config = llm_config_loader.get_config()
        self.llm = LLMClient(
            model=self.llm_config["model"], 
            base_url=self.llm_config["base_url"]
        )
        self.llm.timeout = self.llm_config["timeout"]
        
        # 保留基础的关键词映射作为后备方案
        self.BASIC_SEMANTIC_MAP = {
            # 天气类
            '雨声': ['下雨', '雨水', '雨点', '雨滴', '细雨', '暴雨', '小雨', '大雨', '雨珠'],
            '雷声': ['打雷', '雷鸣', '雷电', '闪电', '轰隆', '雷暴'],
            '风声': ['刮风', '大风', '微风', '狂风', '风吹', '呼啸'],
            '雪声': ['下雪', '飘雪', '雪花', '暴雪'],
            
            # 自然类
            '海浪声': ['海洋', '波浪', '潮水', '海潮', '海浪', '海水'],
            '流水声': ['溪水', '河水', '泉水', '瀑布', '水流'],
            '鸟鸣': ['鸟叫', '鸟声', '啁啾', '鸟儿', '飞鸟'],
            '虫鸣': ['虫叫', '蝉鸣', '蛐蛐', '昆虫', '虫声'],
            '森林声': ['树林', '丛林', '树木', '森林'],
            
            # 人造类
            '脚步声': ['走路', '脚步', '踏步', '行走', '跑步'],
            '开门声': ['开门', '关门', '门响', '门声'],
            '汽车声': ['车声', '汽车', '发动机', '马达'],
            '钟声': ['时钟', '钟响', '报时', '敲钟'],
            
            # 环境类
            '火焰声': ['燃烧', '火苗', '篝火', '壁炉', '火堆'],
            '机械声': ['机器', '设备', '工厂', '机械'],
            '音乐声': ['音乐', '乐器', '歌曲', '演奏']
        }
        
        # 优化后的权重配置
        self.MATCH_WEIGHTS = {
            'exact': 1.0,      # 精确匹配
            'llm_semantic': 0.95,  # LLM智能语义匹配
            'basic_semantic': 0.8,  # 基础语义匹配
            'tag': 0.7,        # 标签匹配
            'fuzzy': 0.6,      # 模糊匹配
            'category': 0.5    # 分类匹配
        }
        
        # 最低匹配阈值
        self.MIN_CONFIDENCE_THRESHOLD = 0.4
        
        # 缓存机制
        self.similarity_cache = {}
        self.cache_max_size = 1000
        
        logger.info("[SOUND_MATCHING] 环境音智能匹配引擎(LLM优化版)初始化完成")
    
    async def find_matching_sounds(self, 
                                 environment_keywords: List[str], 
                                 db: Session,
                                 max_results: int = 5) -> List[MatchResult]:
        """
        为环境音关键词找到匹配的已有环境音
        
        Args:
            environment_keywords: 环境音关键词列表
            db: 数据库会话
            max_results: 最大返回结果数
            
        Returns:
            匹配结果列表，按置信度排序
        """
        logger.info(f"[SOUND_MATCHING] 开始匹配关键词: {environment_keywords}")
        
        if not environment_keywords:
            return []
        
        all_matches = []
        
        # 获取所有可用的环境音
        available_sounds = db.query(EnvironmentSound).filter(
            EnvironmentSound.is_public == True,
            EnvironmentSound.generation_status == 'completed'
        ).all()
        
        logger.info(f"[SOUND_MATCHING] 可用环境音数量: {len(available_sounds)}")
        
        for keyword in environment_keywords:
            keyword_matches = await self._find_matches_for_keyword(keyword, available_sounds, db)
            all_matches.extend(keyword_matches)
        
        # 去重和排序
        unique_matches = self._deduplicate_and_rank_matches(all_matches)
        
        # 限制结果数量
        final_matches = unique_matches[:max_results]
        
        logger.info(f"[SOUND_MATCHING] 匹配完成，找到{len(final_matches)}个结果")
        
        return final_matches
    
    async def _find_matches_for_keyword(self, 
                                      keyword: str, 
                                      available_sounds: List[EnvironmentSound],
                                      db: Session) -> List[MatchResult]:
        """为单个关键词查找匹配"""
        matches = []
        keyword_lower = keyword.lower().strip()
        
        logger.info(f"[SOUND_MATCHING] 匹配关键词: '{keyword}'")
        
        for sound in available_sounds:
            sound_name = sound.name.lower()
            
            # 1. 精确匹配
            if keyword_lower == sound_name or keyword_lower in sound_name:
                confidence = self.MATCH_WEIGHTS['exact']
                if keyword_lower == sound_name:
                    confidence = 1.0
                elif len(keyword_lower) >= 3 and keyword_lower in sound_name:
                    confidence = 0.9
                
                match = MatchResult(
                    sound_id=sound.id,
                    sound_name=sound.name,
                    match_type='exact',
                    confidence=confidence,
                    similarity_score=1.0,
                    reason=f"精确匹配关键词 '{keyword}'"
                )
                match.matched_keywords = [keyword]
                matches.append(match)
                continue
            
            # 2. LLM智能语义相似度匹配
            llm_semantic_score = await self._calculate_llm_semantic_similarity(keyword_lower, sound_name)
            if llm_semantic_score >= 0.6:  # 降低阈值，因为LLM更智能
                match = MatchResult(
                    sound_id=sound.id,
                    sound_name=sound.name,
                    match_type='llm_semantic',
                    confidence=self.MATCH_WEIGHTS['llm_semantic'] * llm_semantic_score,
                    similarity_score=llm_semantic_score,
                    reason=f"LLM智能语义匹配 (相似度: {llm_semantic_score:.2f})"
                )
                match.matched_keywords = [keyword]
                matches.append(match)
                continue
            
            # 3. 基础语义相似度匹配（后备方案）
            basic_semantic_score = self._calculate_basic_semantic_similarity(keyword_lower, sound_name)
            if basic_semantic_score >= 0.7:
                match = MatchResult(
                    sound_id=sound.id,
                    sound_name=sound.name,
                    match_type='basic_semantic',
                    confidence=self.MATCH_WEIGHTS['basic_semantic'] * basic_semantic_score,
                    similarity_score=basic_semantic_score,
                    reason=f"基础语义匹配 (相似度: {basic_semantic_score:.2f})"
                )
                match.matched_keywords = [keyword]
                matches.append(match)
                continue
            
            # 4. 标签匹配
            tag_match_score = await self._check_tag_match(keyword, sound, db)
            if tag_match_score >= 0.5:
                match = MatchResult(
                    sound_id=sound.id,
                    sound_name=sound.name,
                    match_type='tag',
                    confidence=self.MATCH_WEIGHTS['tag'] * tag_match_score,
                    similarity_score=tag_match_score,
                    reason=f"标签匹配 (相关度: {tag_match_score:.2f})"
                )
                match.matched_keywords = [keyword]
                matches.append(match)
                continue
            
            # 5. 模糊匹配 (编辑距离)
            fuzzy_score = self._calculate_fuzzy_similarity(keyword_lower, sound_name)
            if fuzzy_score >= 0.6:
                match = MatchResult(
                    sound_id=sound.id,
                    sound_name=sound.name,
                    match_type='fuzzy',
                    confidence=self.MATCH_WEIGHTS['fuzzy'] * fuzzy_score,
                    similarity_score=fuzzy_score,
                    reason=f"模糊匹配 (相似度: {fuzzy_score:.2f})"
                )
                match.matched_keywords = [keyword]
                matches.append(match)
        
        return matches
    
    async def _calculate_llm_semantic_similarity(self, keyword: str, sound_name: str) -> float:
        """使用LLM计算智能语义相似度"""
        try:
            # 检查缓存
            cache_key = f"{keyword}|{sound_name}"
            if cache_key in self.similarity_cache:
                return self.similarity_cache[cache_key]
            
            # 构建LLM提示词
            prompt = f"""你是一个专业的环境音效分析师。请分析以下两个环境音描述的语义相似度：

关键词："{keyword}"
环境音名称："{sound_name}"

请从以下维度分析相似度：
1. 声音类型相似性（如都是自然音、机械音等）
2. 声音特征相似性（如都是持续音、瞬间音等）
3. 场景适用性相似性（如都适合室内、室外等）
4. 情感氛围相似性（如都是紧张、舒缓等）

请返回一个0-1之间的相似度分数，其中：
- 1.0：完全相似或相同
- 0.8-0.9：高度相似
- 0.6-0.7：中等相似
- 0.4-0.5：低度相似
- 0.0-0.3：不相似

请只返回JSON格式：
{{"similarity_score": 0.85, "reason": "都是自然音效，适合户外场景"}}"""

            # 调用LLM
            response = await self.llm.call_json(prompt)
            
            if response and 'similarity_score' in response:
                similarity_score = float(response['similarity_score'])
                
                # 缓存结果
                if len(self.similarity_cache) < self.cache_max_size:
                    self.similarity_cache[cache_key] = similarity_score
                
                logger.debug(f"[LLM_SEMANTIC] '{keyword}' vs '{sound_name}' = {similarity_score}")
                return similarity_score
            else:
                logger.warning(f"[LLM_SEMANTIC] LLM返回格式错误: {response}")
                return 0.0
                
        except Exception as e:
            logger.error(f"[LLM_SEMANTIC] 计算相似度失败: {str(e)}")
            # 降级到基础语义匹配
            return self._calculate_basic_semantic_similarity(keyword, sound_name)
    
    def _calculate_basic_semantic_similarity(self, keyword: str, sound_name: str) -> float:
        """计算基础语义相似度（后备方案）"""
        # 检查是否在基础语义映射中
        for main_keyword, related_words in self.BASIC_SEMANTIC_MAP.items():
            if main_keyword in sound_name:
                # 检查keyword是否是相关词
                for related_word in related_words:
                    if related_word in keyword or keyword in related_word:
                        return 0.9
                # 检查keyword是否与主关键词相似
                if keyword in main_keyword or main_keyword in keyword:
                    return 0.8
        
        # 反向检查
        for main_keyword, related_words in self.BASIC_SEMANTIC_MAP.items():
            if main_keyword in keyword:
                for related_word in related_words:
                    if related_word in sound_name or sound_name in related_word:
                        return 0.85
        
        # 基于字符包含的相似度
        if len(keyword) >= 2 and len(sound_name) >= 2:
            if keyword in sound_name or sound_name in keyword:
                return 0.7
        
        return 0.0
    
    async def _check_tag_match(self, keyword: str, sound: EnvironmentSound, db: Session) -> float:
        """检查标签匹配度"""
        # 暂时禁用标签匹配，因为数据库表还没有tags字段
        return 0.0
        
        # TODO: 等数据库迁移添加tags字段后重新启用
        # 获取环境音的标签（从tags字段）
        if not hasattr(sound, 'tags') or not sound.tags:
            return 0.0
            
        best_score = 0.0
        keyword_lower = keyword.lower()
        
        # sound.tags 是JSON字段，包含标签列表
        tags = sound.tags if isinstance(sound.tags, list) else []
        
        for tag_name in tags:
            if not isinstance(tag_name, str):
                continue
                
            tag_name_lower = tag_name.lower()
            
            # 精确匹配
            if keyword_lower == tag_name_lower:
                best_score = max(best_score, 1.0)
            # 包含匹配
            elif keyword_lower in tag_name_lower or tag_name_lower in keyword_lower:
                best_score = max(best_score, 0.8)
            # 模糊匹配
            else:
                fuzzy_score = SequenceMatcher(None, keyword_lower, tag_name_lower).ratio()
                if fuzzy_score >= 0.7:
                    best_score = max(best_score, fuzzy_score)
        
        return best_score
    
    def _calculate_fuzzy_similarity(self, keyword: str, sound_name: str) -> float:
        """计算模糊相似度（基于编辑距离）"""
        return SequenceMatcher(None, keyword, sound_name).ratio()
    
    def _deduplicate_and_rank_matches(self, matches: List[MatchResult]) -> List[MatchResult]:
        """去重和排序匹配结果"""
        # 按sound_id去重，保留置信度最高的
        sound_matches = {}
        
        for match in matches:
            sound_id = match.sound_id
            if sound_id not in sound_matches or match.confidence > sound_matches[sound_id].confidence:
                sound_matches[sound_id] = match
        
        # 转换为列表并排序
        unique_matches = list(sound_matches.values())
        
        # 过滤低置信度结果
        filtered_matches = [
            match for match in unique_matches 
            if match.confidence >= self.MIN_CONFIDENCE_THRESHOLD
        ]
        
        # 按置信度降序排序
        filtered_matches.sort(key=lambda x: x.confidence, reverse=True)
        
        return filtered_matches
    
    async def search_environment_sounds(self, 
                                      query: str, 
                                      db: Session, 
                                      limit: int = 10) -> List[MatchResult]:
        """
        搜索环境音的公共接口
        
        Args:
            query: 搜索查询
            db: 数据库会话
            limit: 最大返回结果数
            
        Returns:
            匹配结果列表
        """
        logger.info(f"[SOUND_MATCHING] 搜索查询: '{query}'")
        
        # 将查询分割为关键词
        keywords = [query.strip()]
        if ' ' in query:
            keywords.extend(query.split())
        
        # 使用现有的匹配方法
        matches = await self.find_matching_sounds(keywords, db, limit)
        
        logger.info(f"[SOUND_MATCHING] 搜索完成，找到{len(matches)}个结果")
        return matches
    
    async def batch_llm_semantic_analysis(self, 
                                        keyword_sound_pairs: List[Tuple[str, str]]) -> Dict[str, float]:
        """
        批量LLM语义分析，提升性能
        
        Args:
            keyword_sound_pairs: [(keyword, sound_name), ...] 列表
            
        Returns:
            {f"{keyword}|{sound_name}": similarity_score} 字典
        """
        try:
            if not keyword_sound_pairs:
                return {}
            
            # 构建批量分析提示词
            pairs_text = "\n".join([f"{i+1}. 关键词: '{pair[0]}' | 环境音: '{pair[1]}'" 
                                  for i, pair in enumerate(keyword_sound_pairs)])
            
            prompt = f"""你是一个专业的环境音效分析师。请批量分析以下关键词与环境音名称的语义相似度：

{pairs_text}

请从以下维度分析每个配对的相似度：
1. 声音类型相似性（如都是自然音、机械音等）
2. 声音特征相似性（如都是持续音、瞬间音等）
3. 场景适用性相似性（如都适合室内、室外等）
4. 情感氛围相似性（如都是紧张、舒缓等）

请返回JSON格式，包含每个配对的相似度分数（0-1之间）：
{{
  "results": [
    {{"index": 1, "similarity_score": 0.85, "reason": "都是自然音效"}},
    {{"index": 2, "similarity_score": 0.3, "reason": "类型差异较大"}},
    ...
  ]
}}"""

            # 调用LLM
            response = await self.llm.call_json(prompt)
            
            if response and 'results' in response:
                results = {}
                for item in response['results']:
                    index = item.get('index', 0) - 1  # 转换为0基索引
                    if 0 <= index < len(keyword_sound_pairs):
                        keyword, sound_name = keyword_sound_pairs[index]
                        cache_key = f"{keyword}|{sound_name}"
                        similarity_score = float(item.get('similarity_score', 0.0))
                        results[cache_key] = similarity_score
                        
                        # 缓存结果
                        if len(self.similarity_cache) < self.cache_max_size:
                            self.similarity_cache[cache_key] = similarity_score
                
                logger.info(f"[BATCH_LLM] 批量分析了{len(results)}个配对")
                return results
            else:
                logger.warning(f"[BATCH_LLM] LLM返回格式错误: {response}")
                return {}
                
        except Exception as e:
            logger.error(f"[BATCH_LLM] 批量分析失败: {str(e)}")
            return {}
    
    def clear_cache(self):
        """清空缓存"""
        self.similarity_cache.clear()
        logger.info("[SOUND_MATCHING] 缓存已清空")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        return {
            "cache_size": len(self.similarity_cache),
            "cache_max_size": self.cache_max_size,
            "cache_usage": len(self.similarity_cache) / self.cache_max_size
        }

    async def batch_match_analysis_result(self, 
                                        analysis_result: Dict[str, Any], 
                                        db: Session) -> Dict[str, Any]:
        """
        批量匹配分析结果中的所有环境音需求
        
        Args:
            analysis_result: 章节环境音分析结果
            db: 数据库会话
            
        Returns:
            包含匹配信息的增强分析结果
        """
        logger.info("[SOUND_MATCHING] 开始批量匹配分析结果")
        
        # 支持多种数据格式：直接包含environment_tracks 或 chapters嵌套格式
        environment_tracks = analysis_result.get('environment_tracks', [])
        
        # 如果没有直接的environment_tracks，尝试从chapters中提取
        if not environment_tracks and 'chapters' in analysis_result:
            logger.info("[SOUND_MATCHING] 检测到chapters格式，正在提取环境轨道...")
            chapters = analysis_result.get('chapters', [])
            
            # 合并所有章节的环境轨道
            for chapter in chapters:
                chapter_analysis = chapter.get('analysis_result', {})
                chapter_tracks = chapter_analysis.get('environment_tracks', [])
                environment_tracks.extend(chapter_tracks)
                logger.info(f"[SOUND_MATCHING] 从章节提取到{len(chapter_tracks)}个轨道")
        
        if not environment_tracks:
            # 即使没有环境轨道，也要添加matching_summary
            enhanced_result = analysis_result.copy()
            enhanced_result['matching_summary'] = {
                'total_tracks': 0,
                'matched_tracks': 0,
                'need_generation_tracks': 0,
                'match_rate': 0,
                'unique_keywords': 0,
                'matching_timestamp': datetime.now().isoformat()
            }
            logger.info("[SOUND_MATCHING] 没有环境轨道需要匹配")
            return enhanced_result
        
        logger.info(f"[SOUND_MATCHING] 收到{len(environment_tracks)}个环境轨道")
        
        # 收集所有unique关键词
        all_keywords = set()
        for i, track in enumerate(environment_tracks):
            keywords = track.get('environment_keywords', [])
            logger.info(f"[SOUND_MATCHING] 轨道{i+1} (segment_id: {track.get('segment_id')}): 关键词{keywords}")
            all_keywords.update(keywords)
        
        unique_keywords = list(all_keywords)
        logger.info(f"[SOUND_MATCHING] 收集到{len(unique_keywords)}个唯一关键词: {unique_keywords}")
        
        # 批量匹配所有关键词
        matching_results = {}
        for keyword in unique_keywords:
            matches = await self.find_matching_sounds([keyword], db, max_results=3)
            matching_results[keyword] = [match.to_dict() for match in matches]
        
        # 为每个轨道添加匹配信息
        enhanced_tracks = []
        matched_count = 0
        need_generation_count = 0
        
        for track in environment_tracks:
            enhanced_track = track.copy()
            keywords = track.get('environment_keywords', [])
            
            track_matches = []
            best_match = None
            best_confidence = 0.0
            
            # 为轨道找到最佳匹配
            for keyword in keywords:
                keyword_matches = matching_results.get(keyword, [])
                track_matches.extend(keyword_matches)
                
                # 找到最佳匹配
                for match in keyword_matches:
                    if match['confidence'] > best_confidence:
                        best_match = match
                        best_confidence = match['confidence']
            
            # 去重轨道匹配结果
            unique_track_matches = []
            seen_sound_ids = set()
            for match in track_matches:
                sound_id = match['sound_id']
                if sound_id not in seen_sound_ids:
                    unique_track_matches.append(match)
                    seen_sound_ids.add(sound_id)
            
            # 按置信度排序
            unique_track_matches.sort(key=lambda x: x['confidence'], reverse=True)
            
            # 添加匹配信息到轨道
            enhanced_track['matching_results'] = unique_track_matches[:3]  # 最多3个匹配
            enhanced_track['best_match'] = best_match
            enhanced_track['has_match'] = best_match is not None
            enhanced_track['match_confidence'] = best_confidence
            
            # 统计
            if best_match:
                matched_count += 1
            else:
                need_generation_count += 1
            
            enhanced_tracks.append(enhanced_track)
        
        # 构建增强结果
        enhanced_result = analysis_result.copy()
        enhanced_result['environment_tracks'] = enhanced_tracks
        enhanced_result['matching_summary'] = {
            'total_tracks': len(enhanced_tracks),
            'matched_tracks': matched_count,
            'need_generation_tracks': need_generation_count,
            'match_rate': round(matched_count / len(enhanced_tracks) * 100, 1) if enhanced_tracks else 0,
            'unique_keywords': len(unique_keywords),
            'matching_timestamp': datetime.now().isoformat()
        }
        
        logger.info(f"[SOUND_MATCHING] 批量匹配完成: {matched_count}/{len(enhanced_tracks)} 轨道找到匹配")
        
        return enhanced_result
    
    def get_generation_plan(self, analysis_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        生成环境音生成计划
        
        Returns:
            包含需要生成的环境音列表和统计信息的计划
        """
        environment_tracks = analysis_result.get('environment_tracks', [])
        
        # 收集需要生成的环境音
        need_generation = []
        already_matched = []
        
        for track in environment_tracks:
            if not track.get('has_match', False):
                keywords = track.get('environment_keywords', [])
                for keyword in keywords:
                    if keyword not in [item['keyword'] for item in need_generation]:
                        need_generation.append({
                            'keyword': keyword,
                            'track_count': 1,
                            'example_scene': track.get('scene_description', ''),
                            'intensity_level': track.get('intensity_level', 'medium'),
                            'suggested_duration': track.get('duration', 30.0)
                        })
                    else:
                        # 增加使用次数
                        for item in need_generation:
                            if item['keyword'] == keyword:
                                item['track_count'] += 1
                                break
            else:
                best_match = track.get('best_match', {})
                matched_info = {
                    'sound_id': best_match.get('sound_id'),
                    'sound_name': best_match.get('sound_name'),
                    'confidence': best_match.get('confidence', 0.0),
                    'keywords': track.get('environment_keywords', [])
                }
                if matched_info not in already_matched:
                    already_matched.append(matched_info)
        
        # 按使用频次排序需要生成的环境音
        need_generation.sort(key=lambda x: x['track_count'], reverse=True)
        
        generation_plan = {
            'need_generation': need_generation,
            'already_matched': already_matched,
            'statistics': {
                'total_unique_sounds_needed': len(need_generation),
                'total_matched_sounds': len(already_matched),
                'estimated_generation_time': len(need_generation) * 30,  # 估计每个30秒
                'priority_sounds': [item['keyword'] for item in need_generation[:5]]  # 前5个优先级
            },
            'generation_timestamp': datetime.now().isoformat()
        }
        
        return generation_plan 