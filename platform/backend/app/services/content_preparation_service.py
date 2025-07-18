"""
小说章节合成语音前内容准备服务
重构后的精简版本 - 主要负责流程控制和协调各个专门服务
"""

import asyncio
import re
import json
import logging
import hashlib
import os
from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from ..models import BookChapter, VoiceProfile
from ..exceptions import ServiceException
from .chapter_chunker import ChapterChunker
from .ai_tts_optimizer import AITTSOptimizer
from .intelligent_voice_mapper import IntelligentVoiceMapper

logger = logging.getLogger(__name__)


class ContentPreparationService:
    """内容准备服务主控制器 - 重构后的精简版本"""
    
    def __init__(self, db: Session):
        self.db = db
        self.chunker = ChapterChunker()
        self.tts_optimizer = None  # 延迟初始化
        self.voice_mapper = IntelligentVoiceMapper(db)
        self.ollama_detector = None  # 延迟初始化
    
    async def prepare_chapter_for_synthesis(
        self, 
        chapter_id: int,
        user_preferences: Dict = None
    ) -> Dict:
        """准备章节用于语音合成的完整流程"""
        
        try:
            # 1. 获取章节数据
            chapter = self.db.query(BookChapter).filter(BookChapter.id == chapter_id).first()
            if not chapter:
                raise ServiceException(f"章节 {chapter_id} 不存在")
            
            logger.info(f"开始准备章节 {chapter_id}: {chapter.chapter_title}")
            
            # 2. 更新章节状态为处理中
            chapter.analysis_status = 'analyzing'
            self.db.commit()
            
            # 3. 预处理文本
            cleaned_text = self._clean_and_normalize(chapter.content)
            
            # 4. 检查文本长度，决定处理策略
            estimated_tokens = self._estimate_tokens(cleaned_text)
            processing_mode = "distributed" if estimated_tokens > 3000 else "single"
            
            logger.info(f"章节内容长度: {len(cleaned_text)} 字符, 估算 {estimated_tokens} tokens, 使用 {processing_mode} 模式")
            
            # 5. 执行AI分析
            chapter_info = {
                "chapter_id": chapter.id,
                "chapter_title": chapter.chapter_title,
                "chapter_number": chapter.chapter_number,
                "processing_mode": processing_mode
            }
            
            # 🔧 新增：支持TTS优化模式
            tts_optimization_mode = user_preferences and user_preferences.get("tts_optimization", "balanced")
            
            logger.info(f"🔍 处理模式决策: processing_mode={processing_mode}, tts_optimization={tts_optimization_mode}")
            
            # 🚀 强制使用完整AI分析，删除垃圾简化模式
            logger.info("🤖 使用完整AI智能分析模式")
            try:
                # 延迟初始化OllamaCharacterDetector
                if self.ollama_detector is None:
                    logger.info("📦 初始化OllamaCharacterDetector...")
                    try:
                        from ..detectors.ollama_character_detector import OllamaCharacterDetector
                        self.ollama_detector = OllamaCharacterDetector()
                        logger.info("✅ OllamaCharacterDetector初始化成功")
                    except ImportError as e:
                        logger.error(f"❌ 无法导入OllamaCharacterDetector: {str(e)}")
                        raise ServiceException(f"AI分析组件初始化失败: {str(e)}")
                
                # 执行AI分析
                logger.info(f"🔄 开始智能分析，模式: {processing_mode}")
                if processing_mode == "single":
                    analysis_result = await self.ollama_detector.analyze_text(cleaned_text, chapter_info)
                    logger.info("✅ 智能单块分析完成")
                else:
                    analysis_result = await self._analyze_chapter_distributed(cleaned_text, chapter_info)
                    logger.info("✅ 智能分布式分析完成")
                    
            except Exception as e:
                logger.error(f"❌ AI智能分析失败: {str(e)}")
                raise ServiceException(f"AI智能分析失败: {str(e)}")
            
            # 6. 确保有旁白角色
            detected_characters = analysis_result.get('detected_characters', [])
            detected_characters = self._ensure_narrator_character(detected_characters)
            
            # 7. 智能语音映射
            voice_mapping = await self.voice_mapper.intelligent_voice_mapping(detected_characters, user_preferences)
            
            # 🔍 调试：检查voice mapping结果
            logger.info(f"🔊 Voice mapping结果: {voice_mapping}")
            logger.info(f"🎭 所有角色: {[char.get('name') for char in detected_characters]}")
            for char_name, voice_id in voice_mapping.items():
                logger.info(f"🎵 {char_name} -> voice_id: {voice_id}")
            
            # 🔧 检查旁白角色的voice mapping状态
            if '旁白' in voice_mapping:
                logger.info(f"✅ 旁白角色已分配voice_id: {voice_mapping['旁白']}")
            else:
                logger.warning("❌ 旁白角色未分配voice_id，需要用户手动分配")
            
            # 8. 转换为合成格式（应用TTS优化配置）
            # 设置当前章节ID，用于关联角色配音库
            self.current_chapter_id = chapter_id
            synthesis_json = await self._adapt_to_synthesis_format(
                analysis_result, 
                voice_mapping,
                tts_optimization_mode=tts_optimization_mode
            )
            
            # 🔥 新增：最终完整性校验 - 确保synthesis_plan覆盖了原文所有内容
            final_completeness = self._validate_synthesis_completeness(cleaned_text, synthesis_json)
            if not final_completeness:
                logger.warning("最终合成计划完整性校验失败，可能存在内容丢失")
                # 记录详细的差异信息用于调试
                self._log_completeness_details(cleaned_text, synthesis_json)
            
            # 9. 保存分析结果到数据库
            preparation_result = await self._save_preparation_result(
                chapter_id=chapter_id,
                analysis_result=analysis_result,
                synthesis_json=synthesis_json,
                voice_mapping=voice_mapping,
                processing_info={
                    "mode": processing_mode,
                    "total_segments": len(analysis_result.get('segments', [])),
                    "characters_found": len(detected_characters),
                    "estimated_tokens": estimated_tokens,
                    "analysis_method": analysis_result.get('analysis_metadata', {}).get('method', 'ai_enhanced'),
                    "final_completeness_validated": final_completeness  # 🔥 新增：记录最终完整性校验结果
                }
            )
            
            # 10. 更新章节状态为完成
            chapter.analysis_status = 'completed'
            chapter.synthesis_status = 'ready'
            self.db.commit()
            
            logger.info(f"章节 {chapter_id} 智能准备完成，共识别 {len(detected_characters)} 个角色")
            
            # 10.5. 更新书籍角色汇总（高性能）
            try:
                from ..models import Book
                book = self.db.query(Book).filter(Book.id == chapter.book_id).first()
                if book:
                    # 🎭 提取角色信息用于汇总 - 修复数据格式
                    characters_for_summary = []
                    for char in detected_characters:
                        char_name = char.get('name', '').strip()
                        if not char_name:
                            continue
                            
                        # 🔥 修复：确保旁白角色的数据完整性
                        char_data = {
                            'name': char_name,
                            'gender': char.get('gender', char.get('recommended_config', {}).get('gender', '')),
                            'age': char.get('age', char.get('recommended_config', {}).get('age_range', '')),
                            'personality': char.get('personality', char.get('recommended_config', {}).get('personality', '')),
                            'description': char.get('description', f"智能检测到的{char_name}角色"),
                            'appearances': 1  # 本章节出现1次
                        }
                        characters_for_summary.append(char_data)
                        
                        logger.debug(f"📝 准备更新角色汇总: {char_name} -> {char_data}")
                    
                    # 更新书籍角色汇总
                    logger.info(f"🎭 开始更新书籍 {book.id} 的角色汇总，本章识别角色: {[c['name'] for c in characters_for_summary]}")
                    book.update_character_summary(characters_for_summary, chapter_id)
                    self.db.commit()
                    
                    # 📊 验证更新结果
                    updated_summary = book.get_character_summary()
                    
                    # 🔥 关键修复：智能分析完成后自动同步已有的角色配置
                    if updated_summary and 'voice_mappings' in updated_summary:
                        voice_mappings = updated_summary['voice_mappings']
                        if voice_mappings:
                            logger.info(f"🔄 [智能分析后同步] 发现书籍已有角色配置，自动同步到新章节: {voice_mappings}")
                            
                            # 导入同步函数并执行
                            try:
                                from ..api.v1.books import _sync_character_voice_to_synthesis_plans
                                updated_chapters = await _sync_character_voice_to_synthesis_plans(
                                    book.id, voice_mappings, self.db
                                )
                                logger.info(f"✅ [智能分析后同步] 成功同步 {updated_chapters} 个章节的角色配置")
                            except Exception as sync_error:
                                logger.error(f"❌ [智能分析后同步] 同步失败: {sync_error}")
                        else:
                            logger.info(f"📋 [智能分析后同步] 书籍暂无角色配置，跳过同步")
                    else:
                        logger.info(f"📋 [智能分析后同步] 书籍角色汇总格式异常，跳过同步")
                    all_characters = [char['name'] for char in updated_summary.get('characters', [])]
                    logger.info(f"✅ 书籍角色汇总更新完成，当前所有角色: {all_characters}")
                    
                    # 🔍 特别检查旁白角色
                    narrator_exists = any(char['name'] == '旁白' for char in updated_summary.get('characters', []))
                    if narrator_exists:
                        logger.info("🎭 ✅ 旁白角色已成功添加到书籍角色汇总")
                    else:
                        logger.warning("🎭 ❌ 旁白角色未能添加到书籍角色汇总，需要手动检查")
                else:
                    logger.warning(f"未找到章节 {chapter_id} 对应的书籍")
            except Exception as e:
                logger.error(f"更新书籍角色汇总失败: {str(e)}")
                import traceback
                logger.error(f"异常堆栈: {traceback.format_exc()}")
                # 不抛出异常，避免影响主流程
            
            # 11. 返回结果
            return {
                "synthesis_json": synthesis_json,
                "processing_info": {
                    "mode": processing_mode,
                    "total_segments": len(analysis_result.get('segments', [])),
                    "characters_found": len(detected_characters),
                    "estimated_tokens": estimated_tokens,
                    "narrator_added": any(char.get('name') == '旁白' for char in detected_characters),
                    "voice_mapping": voice_mapping,
                    "saved_to_database": True,
                    "preparation_id": preparation_result.get("id")
                }
            }
            
        except Exception as e:
            # 更新章节状态为失败
            if chapter:
                chapter.analysis_status = 'failed'
                self.db.commit()
            
            logger.error(f"章节 {chapter_id} 智能准备失败: {str(e)}")
            raise ServiceException(f"智能准备失败: {str(e)}")

    async def _save_preparation_result(
        self,
        chapter_id: int,
        analysis_result: Dict,
        synthesis_json: Dict,
        voice_mapping: Dict,
        processing_info: Dict
    ) -> Dict:
        """保存智能准备结果到数据库"""
        
        try:
            # 计算内容哈希用于去重
            content_hash = hashlib.md5(
                json.dumps(analysis_result, sort_keys=True).encode('utf-8')
            ).hexdigest()
            
            # 检查是否需要导入analysis_results模型
            try:
                from ..models import AnalysisResult
            except ImportError:
                # 如果没有AnalysisResult模型，创建一个简化的存储方案
                logger.warning("AnalysisResult模型不存在，使用章节字段存储结果")
                
                # 将结果存储在章节的字段中
                chapter = self.db.query(BookChapter).filter(BookChapter.id == chapter_id).first()
                if chapter:
                    # 创建完整的结果数据
                    full_result = {
                        "analysis_result": analysis_result,
                        "synthesis_json": synthesis_json,
                        "voice_mapping": voice_mapping,
                        "processing_info": processing_info,
                        "content_hash": content_hash,
                        "created_at": datetime.utcnow().isoformat(),
                        "version": 1
                    }
                    
                    # 如果章节有analysis_results字段，存储在那里
                    if chapter.analysis_results:
                        chapter.analysis_results[0].original_analysis = json.dumps(full_result, ensure_ascii=False)
                    
                    self.db.commit()
                    
                    return {
                        "id": f"chapter_{chapter_id}",
                        "storage_method": "chapter_field",
                        "content_hash": content_hash
                    }
            
            # 如果有AnalysisResult模型，使用标准存储
            # 由于AnalysisResult的session_id是必需的，但我们的智能准备不属于特定项目会话
            # 我们需要创建一个虚拟的session_id或使用其他存储方式
            
            # 检查是否已有相同章节的智能准备结果
            existing_result = self.db.query(AnalysisResult).filter(
                AnalysisResult.chapter_id == chapter_id,
                AnalysisResult.status == 'completed'
            ).order_by(AnalysisResult.created_at.desc()).first()
            
            if existing_result:
                logger.info(f"章节 {chapter_id} 已有智能准备结果，更新现有记录")
                # 更新现有记录
                existing_result.original_analysis = analysis_result
                existing_result.synthesis_plan = synthesis_json
                existing_result.final_config = {
                    "synthesis_json": synthesis_json,
                    "voice_mapping": voice_mapping,
                    "processing_info": processing_info
                }
                existing_result.updated_at = datetime.utcnow()
                self.db.commit()
                
                return {
                    "id": existing_result.id,
                    "storage_method": "analysis_result_updated",
                    "content_hash": content_hash
                }
            
            # 提取角色信息
            detected_characters = []
            if synthesis_json.get('characters'):
                detected_characters = synthesis_json['characters']
            
            # 创建新的分析结果记录
            # 智能准备不依赖项目session，session_id设为None
            
            new_result = AnalysisResult(
                session_id=None,  # 智能准备独立于项目session
                chapter_id=chapter_id,
                original_analysis=analysis_result,
                detected_characters=detected_characters,
                synthesis_plan=synthesis_json,
                final_config={
                    "synthesis_json": synthesis_json,
                    "voice_mapping": voice_mapping,
                    "processing_info": processing_info
                },
                status='completed',
                processing_time=processing_info.get('processing_time', 0),
                confidence_score=85,  # 默认置信度
                created_at=datetime.utcnow(),
                completed_at=datetime.utcnow()
            )
            
            self.db.add(new_result)
            self.db.commit()
            self.db.refresh(new_result)
            
            logger.info(f"智能准备结果已保存到AnalysisResult表，ID: {new_result.id}")
            
            return {
                "id": new_result.id,
                "storage_method": "analysis_result_created",
                "content_hash": content_hash
            }
            
        except Exception as e:
            logger.error(f"保存智能准备结果失败: {str(e)}")
            logger.error(f"异常详情: {type(e).__name__}: {str(e)}")
            import traceback
            logger.error(f"异常堆栈: {traceback.format_exc()}")
            # 不抛出异常，避免影响主流程
            return {
                "id": None,
                "storage_method": "failed",
                "error": str(e)
            }
    

    
    async def _analyze_chapter_distributed(self, chapter_content: str, chapter_info: Dict) -> Dict:
        """分布式分析章节"""
        
        # 1. 智能分块
        chunks = self.chunker.chunk_chapter(chapter_content)
        logger.info(f"章节分块完成，共 {len(chunks)} 个分块")
        
        # 2. 并行分析多个分块
        chunk_results = await self._analyze_chunks_parallel(chunks, chapter_info)
        
        # 3. 合并分析结果
        merged_result = await self._merge_chunk_results(chunk_results, chapter_info)
        
        return merged_result
    
    async def _analyze_chunks_parallel(self, chunks: List[Dict], chapter_info: Dict) -> List[Dict]:
        """并行分析多个分块"""
        
        # 使用信号量控制并发数
        semaphore = asyncio.Semaphore(3)  # 最大并发数
        
        async def analyze_chunk_with_semaphore(chunk, index):
            async with semaphore:
                chunk_info = {
                    **chapter_info,
                    "chunk_index": index,
                    "total_chunks": len(chunks),
                    "is_chunk": True
                }
                logger.info(f"开始分析分块 {index + 1}/{len(chunks)}")
                
                try:
                    result = await self.ollama_detector.analyze_text(chunk["content"], chunk_info)
                    logger.info(f"分块 {index + 1} 分析完成")
                    return result
                except Exception as e:
                    logger.error(f"分块 {index + 1} AI分析失败: {str(e)}")
                    raise e
        
        # 并行执行分析
        tasks = [
            analyze_chunk_with_semaphore(chunk, i) 
            for i, chunk in enumerate(chunks)
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 检查异常结果
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"分块 {i} AI分析异常: {result}")
                raise ServiceException(f"分布式AI分析失败，分块 {i} 错误: {result}")
        
        return results
    
    async def _merge_chunk_results(self, chunk_results: List[Dict], chapter_info: Dict) -> Dict:
        """合并分块分析结果"""
        
        # 合并所有段落
        all_segments = []
        segment_order = 1
        
        for result in chunk_results:
            for segment in result.get('segments', []):
                segment['order'] = segment_order
                all_segments.append(segment)
                segment_order += 1
        
        # 合并角色信息（去重）
        all_characters = {}
        for result in chunk_results:
            for character in result.get('detected_characters', []):
                char_name = character['name']
                if char_name not in all_characters:
                    all_characters[char_name] = character
                else:
                    # 合并角色信息（取置信度更高的）
                    existing = all_characters[char_name]
                    if character.get('confidence', 0) > existing.get('confidence', 0):
                        all_characters[char_name] = character
        
        return {
            'segments': all_segments,
            'detected_characters': list(all_characters.values()),
            'analysis_metadata': {
                'total_chunks': len(chunk_results),
                'total_segments': len(all_segments),
                'total_characters': len(all_characters),
                'processing_mode': 'distributed'
            }
        }
    

    
    def _ensure_narrator_character(self, detected_characters: List[Dict]) -> List[Dict]:
        """确保角色列表中包含旁白角色"""
        
        # 检查是否已有旁白角色
        has_narrator = any(char['name'] == '旁白' for char in detected_characters)
        
        if not has_narrator:
            # 自动添加旁白角色
            narrator_character = {
                'name': '旁白',
                'confidence': 1.0,
                'recommended_config': {
                    'gender': 'neutral',
                    'age_range': 'adult',
                    'personality': 'calm',
                    'voice_style': 'professional'
                },
                'source': 'system_generated',
                'description': '系统自动添加的旁白角色，用于叙述性文本'
            }
            detected_characters.append(narrator_character)
            logger.info("系统自动添加旁白角色")
        
        return detected_characters
    
    async def _ai_reanalyze_unknown_segments(self, segments: List[Dict], detected_characters: List[Dict]) -> List[Dict]:
        """🤖 AI二次分析：专门处理未知角色的segment"""
        unknown_segments = []
        known_character_names = [char.get('name', '') for char in detected_characters if char.get('name')]
        
        # 收集所有未知角色的segment
        for i, segment in enumerate(segments):
            if segment.get('speaker') == '未知角色':
                unknown_segments.append({
                    'index': i,
                    'segment': segment,
                    'context_before': segments[max(0, i-2):i],  # 前2个segment作为上下文
                    'context_after': segments[i+1:min(len(segments), i+3)]  # 后2个segment作为上下文
                })
        
        if not unknown_segments:
            return segments
        
        logger.info(f"🔍 发现 {len(unknown_segments)} 个未知角色segment，启动AI二次分析")
        
        # 构建AI二次分析prompt
        prompt = self._build_unknown_segment_analysis_prompt(unknown_segments, known_character_names)
        
        try:
            # 延迟初始化OllamaCharacterDetector
            if self.ollama_detector is None:
                from ..detectors.ollama_character_detector import OllamaCharacterDetector
                self.ollama_detector = OllamaCharacterDetector()
            
            # 调用AI进行二次分析
            response = self.ollama_detector._call_ollama(prompt)
            if response:
                analysis_result = self._parse_unknown_segment_response(response)
                
                # 应用AI分析结果
                updated_segments = segments.copy()
                for result in analysis_result:
                    segment_index = result.get('segment_index')
                    new_speaker = result.get('speaker', '').strip()
                    reasoning = result.get('reasoning', '')
                    
                    if segment_index is not None and 0 <= segment_index < len(updated_segments):
                        if new_speaker and new_speaker != '未知角色':
                            updated_segments[segment_index]['speaker'] = new_speaker
                            logger.info(f"✅ AI二次分析修正 segment_{segment_index}: '{new_speaker}' (理由: {reasoning})")
                        else:
                            # AI也无法确定，保持为未知角色
                            logger.warning(f"⚠️ AI二次分析仍无法确定 segment_{segment_index}，保持为未知角色")
                
                return updated_segments
            else:
                logger.warning("AI二次分析调用失败，保持原始结果")
                return segments
                
        except Exception as e:
            logger.error(f"AI二次分析异常: {str(e)}，保持原始结果")
            return segments

    def _build_unknown_segment_analysis_prompt(self, unknown_segments: List[Dict], known_characters: List[str]) -> str:
        """构建未知角色segment的AI分析prompt"""
        
        segments_text = ""
        for i, item in enumerate(unknown_segments):
            segment = item['segment']
            context_before = item['context_before']
            context_after = item['context_after']
            
            segments_text += f"\n=== 未知Segment {item['index']} ===\n"
            
            # 上下文
            if context_before:
                segments_text += "【上文】:\n"
                for ctx in context_before:
                    segments_text += f"  {ctx.get('speaker', '旁白')}: {ctx.get('text', '')}\n"
            
            # 当前未知segment
            segments_text += f"【待分析】: {segment.get('text', '')}\n"
            segments_text += f"【文本类型】: {segment.get('text_type', 'unknown')}\n"
            
            # 下文
            if context_after:
                segments_text += "【下文】:\n"
                for ctx in context_after:
                    segments_text += f"  {ctx.get('speaker', '旁白')}: {ctx.get('text', '')}\n"
        
        prompt = f"""你是专业的中文小说角色识别专家。以下是一些无法确定说话者的文本段落，请根据上下文重新分析。

已知角色列表：{', '.join(known_characters) if known_characters else '无'}

待分析的未知角色段落：
{segments_text}

分析要求：
1. **仔细阅读上下文**：理解前后文的逻辑关系和语境
2. **理解文本类型**：
   - dialogue: 直接对话，需要确定具体说话者
   - inner_monologue: 心理活动，通常是主角的内心想法
   - narration: 叙述文字，通常是旁白
3. **角色一致性**：确保角色名称与已知角色列表一致
4. **逻辑推理**：基于常识和小说惯例进行合理推断

特殊识别规则：
- **间接引述内容**：如果上文提到"某某发来消息"、"某某说"，那么引号内容通常是该角色的话
- **心理活动**：通常属于当前场景的主要角色（通常是主角）
- **对话内容**：需要根据场景和上下文确定说话者
- **叙述文字**：描述环境、动作、声音等的文字通常是旁白
- **无法确定时**：优先选择"旁白"而非保持"未知角色"

重要提示：
- 如果文本是消息内容、电话内容、信件内容等，说话者应该是消息的发送者
- 如果文本是心理活动，说话者通常是当前场景的主角
- 如果文本是纯叙述，说话者应该是"旁白"

输出格式（严格JSON）：
{{
  "analysis_results": [
    {{
      "segment_index": 段落在原列表中的索引,
      "speaker": "确定的说话者名称",
      "reasoning": "详细的分析理由和依据",
      "confidence": 0.8
    }}
  ]
}}

只输出JSON，不要其他内容："""
        
        return prompt

    def _parse_unknown_segment_response(self, response: str) -> List[Dict]:
        """解析AI二次分析的响应"""
        try:
            import json
            
            # 提取JSON部分
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            
            if json_start != -1 and json_end != -1:
                json_str = response[json_start:json_end]
                data = json.loads(json_str)
                
                return data.get('analysis_results', [])
            else:
                logger.error("AI二次分析响应中未找到有效JSON")
                return []
                
        except Exception as e:
            logger.error(f"解析AI二次分析响应失败: {str(e)}")
            return []

    async def _adapt_to_synthesis_format(
        self, 
        analysis_result: Dict, 
        voice_mapping: Dict[str, int],
        available_voices: List[Dict] = None,
        tts_optimization_mode: str = "balanced"
    ) -> Dict:
        """转换分析结果为语音合成格式"""
        segments = analysis_result.get('segments', [])
        detected_characters = analysis_result.get('detected_characters', [])
        
        logger.info(f"🔄 开始转换为合成格式，共 {len(segments)} 个segment")
        
        # 🔥 关键修复：关联角色配音库
        # 获取当前章节所属的书籍，并查找角色配音库中的角色
        chapter_id = getattr(self, 'current_chapter_id', None)
        book_id = None
        character_library = {}
        
        logger.info(f"🔥🔥🔥 [DEBUG] 开始角色配音库关联检查，章节ID: {chapter_id}")
        
        if chapter_id:
            try:
                from ..models import BookChapter, Character
                chapter = self.db.query(BookChapter).filter(BookChapter.id == chapter_id).first()
                if chapter:
                    book_id = chapter.book_id
                    logger.info(f"🔥🔥🔥 [DEBUG] 找到章节{chapter_id}，书籍ID: {book_id}")
                    
                    # 获取该书籍的所有角色配音库角色
                    library_characters = self.db.query(Character).filter(Character.book_id == book_id).all()
                    character_library = {char.name: char for char in library_characters}
                    
                    logger.info(f"🔥🔥🔥 [DEBUG] 📚 [角色配音库关联] 书籍{book_id}共有{len(character_library)}个角色配音库角色: {list(character_library.keys())}")
                    for name, char in character_library.items():
                        logger.info(f"🔥🔥🔥 [DEBUG] 角色配音库角色: {name} -> ID={char.id}, 配置状态={char.is_voice_configured}")
                else:
                    logger.warning(f"🔥🔥🔥 [DEBUG] 章节{chapter_id}不存在")
            except Exception as e:
                logger.error(f"🔥🔥🔥 [DEBUG] 获取角色配音库失败: {str(e)}")
                import traceback
                logger.error(f"🔥🔥🔥 [DEBUG] 异常堆栈: {traceback.format_exc()}")
        else:
            logger.warning(f"🔥🔥🔥 [DEBUG] current_chapter_id 为空，无法关联角色配音库")
        
        # 🤖 新增：AI二次分析处理未知角色
        segments = await self._ai_reanalyze_unknown_segments(segments, detected_characters)
        
        synthesis_plan = []
        
        for i, segment in enumerate(segments):
            text_content = segment.get('text', '').strip()
            if not text_content:
                continue
            
            speaker = segment.get('speaker', '').strip()
            
            # 🔧 现在只处理真正无法确定的情况
            if not speaker:
                speaker = '旁白'
                logger.info(f"🔧 空speaker自动设为旁白: {text_content[:30]}...")
            
            # 🔥 优化：直接从角色配音库获取ID，简化逻辑
            voice_id = None
            character_id = None  # 🚀 新架构：使用character_id
            voice_name = "未分配"
            
            # 1. 优先从角色配音库获取ID（无论是否配置语音）
            if speaker in character_library:
                library_char = character_library[speaker]
                character_id = library_char.id  # 🚀 新架构：使用character_id
                # voice_id = library_char.id     # 🔥 移除：避免ID空间冲突
                voice_name = library_char.name
                logger.info(f"✅ [角色配音库] 角色'{speaker}'直接使用配音库ID: {character_id}")
            else:
                # 2. 如果角色配音库没有，再检查传统映射（应该很少见）
                if voice_mapping.get(speaker):
                    voice_id = voice_mapping.get(speaker)
                    # 🚀 新架构：传统映射的voice_id可能指向VoiceProfile，设为None
                    character_id = None
                    try:
                        from ..models import VoiceProfile
                        voice_profile = self.db.query(VoiceProfile).filter(VoiceProfile.id == voice_id).first()
                        if voice_profile:
                            voice_name = voice_profile.name
                        else:
                            voice_name = f"Voice_{voice_id}"
                        logger.info(f"📢 [传统映射] 角色'{speaker}'使用传统映射: voice_id={voice_id}")
                    except Exception as e:
                        logger.warning(f"获取传统voice_name失败: {str(e)}")
                        voice_name = f"Voice_{voice_id}"
                else:
                    logger.warning(f"⚠️ 角色'{speaker}'既不在角色配音库中，也没有传统映射，需要用户手动分配")
            
            # 🔥 TTS优化：根据模式调整参数
            tts_params = self._get_optimized_tts_params(speaker, tts_optimization_mode, segment)
            
            # 🔥 架构修复：获取章节信息并强制添加到segment_data
            chapter_number = None
            if chapter_id:
                try:
                    from ..models import BookChapter
                    chapter = self.db.query(BookChapter).filter(BookChapter.id == chapter_id).first()
                    if chapter:
                        chapter_number = chapter.chapter_number
                        logger.debug(f"获取章节信息: chapter_id={chapter_id}, chapter_number={chapter_number}")
                    else:
                        logger.error(f"章节ID {chapter_id} 不存在于数据库中")
                        raise ValueError(f"章节ID {chapter_id} 不存在")
                except Exception as e:
                    logger.error(f"获取章节信息失败: {str(e)}")
                    raise ValueError(f"获取章节信息失败: {str(e)}")
            else:
                logger.error("chapter_id为空，无法构建完整的segment数据")
                raise ValueError("chapter_id为空，无法构建完整的segment数据")

            # 🚀 新架构：强制包含章节信息的标准化segment_data
            segment_data = {
                "segment_id": i + 1,
                "chapter_id": chapter_id,           # 🔥 强制添加章节ID
                "chapter_number": chapter_number,   # 🔥 强制添加章节编号
                "text": text_content,
                "speaker": speaker,
                "voice_name": voice_name,
                "text_type": segment.get('text_type', 'dialogue'),
                "confidence": segment.get('confidence', 0.8),
                "detection_rule": segment.get('detection_rule', 'ai_analysis'),
                **tts_params
            }
            
            # 🚀 新架构：严格分离ID空间，确保一致性
            if character_id:
                segment_data["character_id"] = character_id
                # 🔥 关键修复：角色配音库不设置voice_id，避免ID冲突
                # segment_data["voice_id"] = voice_id  # 移除这行，避免与VoiceProfile ID冲突
            else:
                segment_data["voice_id"] = voice_id  # 仅传统映射方式使用
            
            # 🔥 数据完整性验证：使用新的Schema验证segment数据
            try:
                from ..schemas.segment_data import DataIntegrityValidator
                validated_segment = DataIntegrityValidator.validate_segment_data(segment_data)
                logger.debug(f"Segment {i+1} 数据验证通过")
            except Exception as e:
                logger.error(f"Segment {i+1} 数据验证失败: {str(e)}")
                logger.error(f"原始数据: {segment_data}")
                raise ValueError(f"Segment数据不完整: {str(e)}")
            
            synthesis_plan.append(segment_data)
        
        # 🔥 关键修复：构建角色信息时优先使用角色配音库数据
        characters = []
        character_library_mappings = {}  # 用于收集角色配音库的映射
        
        # 🔥 新增：从synthesis_plan中提取所有实际出现的角色
        actual_speakers = set()
        for segment in synthesis_plan:
            speaker = segment.get('speaker')
            if speaker and speaker.strip():
                actual_speakers.add(speaker.strip())
        
        # 🔥 优化：确保detected_characters包含所有实际出现的角色
        detected_character_names = {char.get('name', '') for char in detected_characters}
        missing_characters = actual_speakers - detected_character_names
        
        if missing_characters:
            logger.warning(f"⚠️ [角色汇总修复] 发现synthesis_plan中存在但detected_characters中缺失的角色: {missing_characters}")
            # 为缺失的角色创建默认配置
            for missing_char in missing_characters:
                detected_characters.append({
                    'name': missing_char,
                    'voice_type': 'neutral',
                    'confidence': 0.7,
                    'source': 'synthesis_plan_补充'
                })
                logger.info(f"🔧 [角色汇总修复] 自动补充角色: {missing_char}")
        
        for character in detected_characters:
            char_name = character.get('name', '')
            if not char_name:
                continue
            
            voice_id = None
            character_id = None  # 🚀 新架构：使用character_id
            voice_name = "未分配"
            voice_type = "neutral"
            
            # 🔥 优化：直接从角色配音库获取完整信息并写入JSON
            if char_name in character_library:
                library_char = character_library[char_name]
                # 🔥 关键优化：无论是否配置语音，都使用角色配音库的ID
                character_id = library_char.id  # 🚀 新架构：使用character_id
                # voice_id = library_char.id      # 🔥 移除：避免ID空间冲突
                voice_name = library_char.name
                voice_type = library_char.voice_type or "neutral"
                character_library_mappings[char_name] = str(library_char.id)
                logger.info(f"✅ [角色配音库] 角色'{char_name}'直接使用配音库ID: {character_id}")
            else:
                # 如果角色配音库没有，使用传统映射（但这种情况应该很少）
                if voice_mapping.get(char_name):
                    voice_id = voice_mapping.get(char_name)
                    character_id = None  # 🚀 新架构：传统映射不设置character_id
                    try:
                        from ..models import VoiceProfile
                        voice_profile = self.db.query(VoiceProfile).filter(VoiceProfile.id == voice_id).first()
                        if voice_profile:
                            voice_name = voice_profile.name
                        else:
                            voice_name = f"Voice_{voice_id}"
                    except Exception as e:
                        voice_name = f"Voice_{voice_id}"
                logger.warning(f"⚠️ [传统映射] 角色'{char_name}'不在角色配音库中，使用传统映射: voice_id={voice_id}")
            
            # 计算角色在合成计划中的出现次数
            char_count = len([s for s in synthesis_plan if s.get('speaker') == char_name])
            
            # 🔥 新增：从角色配音库获取完整信息（包括头像）
            avatar_url = None
            if char_name in character_library:
                library_char = character_library[char_name]
                if library_char.avatar_path:
                    filename = os.path.basename(library_char.avatar_path)
                    avatar_url = f"/api/v1/avatars/{filename}"
            
            # 🚀 新架构：构建角色信息
            char_data = {
                "name": char_name,
                "voice_name": voice_name,
                "voice_type": voice_type,
                "count": char_count,
                "in_character_library": char_name in character_library,  # 标记是否在角色配音库中
                "is_voice_configured": char_name in character_library and character_library[char_name].is_voice_configured,  # 从角色配音库判断
                "avatarUrl": avatar_url  # 🔥 新增：头像URL
            }
            
            # 🚀 新架构：严格分离ID空间，确保一致性
            if character_id:
                char_data["character_id"] = character_id
                # 🔥 关键修复：角色配音库不设置voice_id，避免ID冲突
                # char_data["voice_id"] = voice_id  # 移除这行，避免与VoiceProfile ID冲突
            else:
                char_data["voice_id"] = voice_id if voice_id else ""  # 仅传统映射方式使用
            
            characters.append(char_data)
        
        # 🔥 关键修复：如果使用了角色配音库，同步更新书籍的voice_mappings
        if character_library_mappings and chapter_id:
            try:
                from ..models import BookChapter, Book
                chapter = self.db.query(BookChapter).filter(BookChapter.id == chapter_id).first()
                if chapter:
                    book = self.db.query(Book).filter(Book.id == chapter.book_id).first()
                    if book:
                        logger.info(f"🔄 [角色配音库同步] 更新书籍{book.id}的voice_mappings: {character_library_mappings}")
                        # 更新书籍的voice_mappings
                        for char_name, voice_id in character_library_mappings.items():
                            book.set_character_voice_mapping(char_name, voice_id)
                        self.db.commit()
                        logger.info(f"✅ [角色配音库同步] 成功更新书籍voice_mappings")
            except Exception as e:
                logger.error(f"❌ [角色配音库同步] 更新书籍voice_mappings失败: {str(e)}")
                # 不影响主流程，继续执行
        
        # 🔥 最终数据完整性验证：验证整个synthesis_plan
        final_synthesis_data = {
            "project_info": {
                "novel_type": "智能检测",
                "analysis_time": datetime.now().isoformat(),
                "total_segments": len(synthesis_plan),
                "ai_model": "optimized-smart-analysis",
                "detected_characters": len(characters),
                "character_library_linked": len(character_library) > 0  # 标记是否关联了角色配音库
            },
            "synthesis_plan": synthesis_plan,
            "characters": characters
        }
        
        # 🔥 架构级验证：确保整个数据结构的一致性
        try:
            from ..schemas.segment_data import DataIntegrityValidator
            validated_plan = DataIntegrityValidator.validate_synthesis_plan(final_synthesis_data)
            logger.info(f"✅ 合成计划整体验证通过，共 {len(synthesis_plan)} 个segments")
            
            # 记录验证成功的统计信息
            chapter_ids = set(seg.chapter_id for seg in validated_plan.synthesis_plan)
            logger.info(f"✅ 数据完整性验证通过：涉及章节 {sorted(chapter_ids)}")
            
        except Exception as e:
            logger.error(f"❌ 合成计划整体验证失败: {str(e)}")
            # 记录详细的验证失败信息
            logger.error(f"验证失败的数据结构: {final_synthesis_data}")
            raise ValueError(f"数据完整性验证失败，无法保存到数据库: {str(e)}")
        
        # 完全匹配现有系统格式
        return final_synthesis_data

    def _get_optimized_tts_params(self, speaker: str, optimization_mode: str, segment: Dict) -> Dict:
        """获取优化的TTS参数"""
        try:
            # 🎯 智能TTS参数配置 - 基于角色和文本内容
            if not self.tts_optimizer:
                from ..services.ai_tts_optimizer import AITTSOptimizer
                self.tts_optimizer = AITTSOptimizer(self.ollama_detector)
                # 根据优化模式配置TTS分析
                if optimization_mode == "fast":
                    self.tts_optimizer.set_enable_ai_analysis(False)
                    logger.info("🚀 TTS优化器设置为快速模式（禁用AI分析）")
                elif optimization_mode == "quality":
                    self.tts_optimizer.set_enable_ai_analysis(True)
                    logger.info("🎯 TTS优化器设置为质量模式（启用AI分析）")
                else:  # balanced
                    self.tts_optimizer.set_enable_ai_analysis(True)
                    logger.info("⚖️ TTS优化器设置为平衡模式")
            
            # 获取智能TTS参数
            tts_params = self.tts_optimizer.get_smart_tts_params(segment, [])
            return tts_params
            
        except Exception as e:
            logger.warning(f"获取TTS参数失败: {str(e)}，使用默认参数")
            # 返回默认参数
            return {
                "speed": 1.0,
                "pitch": 1.0,
                "volume": 1.0,
                "emotion": "neutral"
            }
    

    
    def _clean_and_normalize(self, text: str) -> str:
        """清理和标准化文本"""
        # 基本清理，保持原文完整性
        text = text.strip()
        # 统一换行符
        text = re.sub(r'\r\n', '\n', text)
        # 移除多余空行（保留段落结构）
        text = re.sub(r'\n{3,}', '\n\n', text)
        return text
    
    def _estimate_tokens(self, text: str) -> int:
        """估算文本token数量"""
        chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
        english_words = len(re.findall(r'[a-zA-Z]+', text))
        return int(chinese_chars * 1.5 + english_words)
    


    async def get_content_stats(self, chapter_id: int, db: Session) -> Dict:
        """
        获取章节内容统计信息
        """
        try:
            from app.models import BookChapter
            chapter = db.query(BookChapter).filter(BookChapter.id == chapter_id).first()
            if not chapter:
                raise ValueError("章节不存在")
            
            # 基本统计
            content = chapter.content or ""
            word_count = len(content.replace(' ', '').replace('\n', ''))
            
            # 使用ChapterChunker进行分块分析
            chunker = ChapterChunker()
            chunks = chunker.chunk_chapter(content)
            
            # 估算处理时间和建议
            estimated_time = len(chunks) * 2  # 每个chunk大约2秒
            processing_recommendation = "fast" if len(chunks) <= 5 else "detailed" if len(chunks) <= 15 else "distributed"
            
            return {
                "chapter_id": chapter_id,
                "chapter_title": chapter.chapter_title,
                "word_count": word_count,
                "chunk_count": len(chunks),
                "estimated_processing_time": estimated_time,
                "processing_recommendation": processing_recommendation,
                "content_preview": content[:200] + "..." if len(content) > 200 else content
            }
            
        except Exception as e:
            logger.error(f"获取内容统计失败: {str(e)}")
            raise

    async def get_synthesis_preview(self, chapter_id: int, db: Session) -> Dict:
        """
        获取章节语音合成预览
        """
        try:
            from app.models import BookChapter
            chapter = db.query(BookChapter).filter(BookChapter.id == chapter_id).first()
            if not chapter:
                raise ValueError("章节不存在")
            
            content = chapter.content or ""
            
            # 快速角色检测（简化版）
            import re
            dialogue_patterns = [
                r'"([^"]*)"',  # 双引号对话
                r'"([^"]*)"',  # 中文双引号
                r'「([^」]*)」',  # 日式引号
            ]
            
            dialogues = []
            for pattern in dialogue_patterns:
                matches = re.findall(pattern, content)
                dialogues.extend(matches)
            
            # 估算角色数量（简化）
            estimated_characters = min(len(set(dialogues[:10])), 8) if dialogues else 1
            
            # 使用ChapterChunker进行分块
            chunker = ChapterChunker()
            chunks = chunker.chunk_chapter(content)
            
            return {
                "chapter_id": chapter_id,
                "chapter_title": chapter.chapter_title,
                "estimated_characters": estimated_characters,
                "dialogue_count": len(dialogues),
                "chunk_count": len(chunks),
                "sample_dialogues": dialogues[:5],  # 前5个对话示例
                "processing_complexity": "simple" if len(chunks) <= 3 else "moderate" if len(chunks) <= 10 else "complex"
            }
            
        except Exception as e:
            logger.error(f"获取合成预览失败: {str(e)}")
            raise

    async def get_preparation_status(self, chapter_id: int, db: Session) -> Dict:
        """
        获取章节智能准备状态
        检查章节是否已经完成智能准备，以及准备的质量
        """
        try:
            from app.models import BookChapter, AnalysisResult
            
            # 获取章节基本信息
            chapter = db.query(BookChapter).filter(BookChapter.id == chapter_id).first()
            if not chapter:
                raise ValueError("章节不存在")
            
            # 检查是否有分析结果
            analysis_result = db.query(AnalysisResult).filter(
                AnalysisResult.chapter_id == chapter_id
            ).order_by(AnalysisResult.created_at.desc()).first()
            
            if analysis_result and analysis_result.synthesis_plan:
                # 有分析结果，检查完整性
                synthesis_plan = analysis_result.synthesis_plan
                if isinstance(synthesis_plan, dict) and 'synthesis_plan' in synthesis_plan:
                    segments_count = len(synthesis_plan['synthesis_plan'])
                    characters_count = len(synthesis_plan.get('characters', []))
                    
                    return {
                        "chapter_id": chapter_id,
                        "preparation_complete": True,
                        "analysis_status": chapter.analysis_status,
                        "synthesis_status": chapter.synthesis_status,
                        "segments_count": segments_count,
                        "characters_count": characters_count,
                        "last_prepared": analysis_result.created_at.isoformat() if analysis_result.created_at else None,
                        "preparation_quality": "good" if segments_count > 0 and characters_count > 0 else "poor"
                    }
            
            # 没有分析结果或结果不完整
            return {
                "chapter_id": chapter_id,
                "preparation_complete": False,
                "analysis_status": chapter.analysis_status,
                "synthesis_status": chapter.synthesis_status,
                "segments_count": 0,
                "characters_count": 0,
                "last_prepared": None,
                "preparation_quality": "none"
            }
            
        except Exception as e:
            logger.error(f"获取章节 {chapter_id} 准备状态失败: {str(e)}")
            return {
                "chapter_id": chapter_id,
                "preparation_complete": False,
                "analysis_status": "unknown",
                "synthesis_status": "unknown",
                "error": str(e)
            }
    
    def _validate_synthesis_completeness(self, original_text: str, synthesis_json: Dict) -> bool:
        """🔥 新增：校验最终合成计划的完整性"""
        try:
            synthesis_plan = synthesis_json.get('synthesis_plan', [])
            if not synthesis_plan:
                logger.warning("合成计划为空")
                return False
            
            # 统计原文字数（去除空格和换行）
            original_chars = len(original_text.replace(' ', '').replace('\n', '').replace('\r', ''))
            
            # 统计synthesis_plan中所有text的字数
            synthesis_chars = sum(
                len(segment.get('text', '').replace(' ', '').replace('\n', '').replace('\r', ''))
                for segment in synthesis_plan
            )
            
            # 计算完整度比例
            completeness_ratio = synthesis_chars / original_chars if original_chars > 0 else 0
            
            logger.info(f"最终合成计划完整性校验: 原文{original_chars}字符，合成计划{synthesis_chars}字符，完整度{completeness_ratio:.2%}")
            
            # 如果差异超过10%，认为不完整
            if completeness_ratio < 0.90:
                logger.warning(f"最终合成计划完整性校验失败: 完整度仅{completeness_ratio:.2%}")
                return False
            
            logger.info("最终合成计划完整性校验通过")
            return True
            
        except Exception as e:
            logger.error(f"最终完整性校验异常: {str(e)}")
            return False
    
    def _log_completeness_details(self, original_text: str, synthesis_json: Dict):
        """🔥 新增：记录完整性校验的详细信息，用于调试"""
        try:
            synthesis_plan = synthesis_json.get('synthesis_plan', [])
            
            logger.info("=== 完整性校验详细信息 ===")
            logger.info(f"原文长度: {len(original_text)} 字符")
            logger.info(f"合成计划段落数: {len(synthesis_plan)}")
            
            # 记录原文的前100字符和后100字符
            original_start = original_text[:100] if len(original_text) > 100 else original_text
            original_end = original_text[-100:] if len(original_text) > 100 else ""
            
            logger.info(f"原文开头: {original_start}")
            if original_end:
                logger.info(f"原文结尾: {original_end}")
            
            # 记录合成计划的第一段和最后一段
            if synthesis_plan:
                first_segment = synthesis_plan[0].get('text', '')
                last_segment = synthesis_plan[-1].get('text', '')
                
                logger.info(f"合成计划第一段: {first_segment}")
                logger.info(f"合成计划最后一段: {last_segment}")
                
                # 检查原文结尾是否在合成计划中
                if original_end and original_end not in ' '.join([seg.get('text', '') for seg in synthesis_plan]):
                    logger.warning(f"原文结尾内容在合成计划中未找到: {original_end}")
            
            logger.info("=== 完整性校验详细信息结束 ===")
            
        except Exception as e:
            logger.error(f"记录完整性详细信息异常: {str(e)}")
    
    def _extract_missing_content(self, original_text: str, synthesis_json: Dict) -> str:
        """🔥 新增：提取丢失的内容，用于调试和修复"""
        try:
            synthesis_plan = synthesis_json.get('synthesis_plan', [])
            synthesis_text = ' '.join([seg.get('text', '') for seg in synthesis_plan])
            
            # 简单的差异检测：找出原文中但不在合成计划中的内容
            missing_parts = []
            
            # 按句子分割原文
            import re
            original_sentences = re.split(r'[。！？]', original_text)
            
            for sentence in original_sentences:
                sentence = sentence.strip()
                if sentence and sentence not in synthesis_text:
                    missing_parts.append(sentence)
            
            if missing_parts:
                missing_content = '；'.join(missing_parts)
                logger.warning(f"检测到丢失的内容片段: {missing_content}")
                return missing_content
            
            return ""
            
        except Exception as e:
            logger.error(f"提取丢失内容异常: {str(e)}")
            return ""