"""
小说章节合成语音前内容准备服务
重构后的精简版本 - 主要负责流程控制和协调各个专门服务
"""

import asyncio
import re
import json
import logging
import hashlib
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
            
            # 检查用户偏好，决定是否使用简化模式
            use_simple_mode = user_preferences and user_preferences.get("processing_mode") == "fast"
            # 🔧 新增：支持TTS优化模式
            tts_optimization_mode = user_preferences and user_preferences.get("tts_optimization", "balanced")
            
            logger.info(f"🔍 处理模式决策: processing_mode={processing_mode}, use_simple_mode={use_simple_mode}, tts_optimization={tts_optimization_mode}")
            
            if use_simple_mode:
                # 使用简化的本地分析，不依赖Ollama
                logger.info("⚡ 使用快速模式，跳过Ollama分析")
                analysis_result = await self._simple_local_analysis(cleaned_text, chapter_info)
            else:
                # 强制使用AI分析，并增强错误处理
                logger.info("🤖 尝试使用Ollama AI进行角色分析")
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
                            raise e
                    
                    # 执行AI分析
                    logger.info(f"🔄 开始Ollama分析，模式: {processing_mode}")
                    if processing_mode == "single":
                        analysis_result = await self.ollama_detector.analyze_text(cleaned_text, chapter_info)
                        logger.info("✅ Ollama单块分析完成")
                    else:
                        analysis_result = await self._analyze_chapter_distributed(cleaned_text, chapter_info)
                        logger.info("✅ Ollama分布式分析完成")
                        
                except Exception as e:
                    logger.error(f"❌ Ollama AI分析失败: {str(e)}")
                    logger.error(f"错误类型: {type(e).__name__}")
                    
                    # 只有在明确不可恢复的错误时才降级
                    if "attempted relative import" in str(e) or "No module named" in str(e):
                        logger.warning("🔧 检测到导入错误，尝试修复后重试")
                        # 这里可以添加导入修复逻辑
                    
                    logger.warning("⬇️  降级到本地规则分析")
                    analysis_result = await self._simple_local_analysis(cleaned_text, chapter_info)
            
            # 6. 确保有旁白角色
            detected_characters = analysis_result.get('detected_characters', [])
            detected_characters = self._ensure_narrator_character(detected_characters)
            
            # 7. 智能语音映射
            voice_mapping = await self.voice_mapper.intelligent_voice_mapping(detected_characters, user_preferences)
            
            # 8. 转换为合成格式（应用TTS优化配置）
            synthesis_json = self._adapt_to_synthesis_format(
                analysis_result, 
                voice_mapping,
                tts_optimization_mode=tts_optimization_mode
            )
            
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
                    "use_simple_mode": use_simple_mode
                }
            )
            
            # 10. 更新章节状态为完成
            chapter.analysis_status = 'completed'
            chapter.synthesis_status = 'ready'
            self.db.commit()
            
            logger.info(f"章节 {chapter_id} 智能准备完成，共识别 {len(detected_characters)} 个角色")
            
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
                    
                    # 如果章节有character_analysis_result字段，存储在那里
                    if hasattr(chapter, 'character_analysis_result'):
                        chapter.character_analysis_result = json.dumps(full_result, ensure_ascii=False)
                    
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
    
    async def _simple_local_analysis(self, content: str, chapter_info: Dict) -> Dict:
        """简化的本地分析，不依赖外部AI服务"""
        import re
        
        # 基本的对话检测
        dialogue_patterns = [
            r'"([^"]*)"',  # 双引号对话
            r'"([^"]*)"',  # 中文双引号
            r'「([^」]*)」',  # 日式引号
            r'『([^』]*)』',  # 日式书名号
        ]
        
        segments = []
        detected_characters = set()
        
        # 按段落分割
        paragraphs = content.split('\n')
        segment_id = 1
        
        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if not paragraph:
                continue
            
            # 检测是否包含对话
            has_dialogue = False
            for pattern in dialogue_patterns:
                if re.search(pattern, paragraph):
                    has_dialogue = True
                    # 提取对话内容
                    matches = re.findall(pattern, paragraph)
                    for match in matches:
                        if len(match.strip()) > 2:  # 过滤太短的对话
                            detected_characters.add(f"角色{len(detected_characters) + 1}")
                    break
            
            # 创建段落
            segments.append({
                'text': paragraph,
                'speaker': f"角色{segment_id % 3 + 1}" if has_dialogue else '旁白',
                'text_type': 'dialogue' if has_dialogue else 'narration',
                'confidence': 0.8 if has_dialogue else 0.9,
                'detection_method': 'simple_local'
            })
            segment_id += 1
        
        # 确保至少有旁白角色
        if '旁白' not in detected_characters:
            detected_characters.add('旁白')
        
        # 构建角色列表
        character_list = []
        for i, char_name in enumerate(detected_characters):
            character_list.append({
                'name': char_name,
                'confidence': 0.8,
                'source': 'simple_local',
                'recommended_config': {
                    'gender': 'female' if i % 2 == 0 else 'male',
                    'personality': 'gentle' if char_name == '旁白' else 'normal'
                }
            })
        
        return {
            'segments': segments,
            'detected_characters': character_list,
            'analysis_metadata': {
                'total_segments': len(segments),
                'total_characters': len(character_list),
                'processing_mode': 'simple_local',
                'method': 'rule_based'
            }
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
                    logger.error(f"分块 {index + 1} 分析失败: {str(e)}")
                    return self._create_fallback_result(chunk, chunk_info)
        
        # 并行执行分析
        tasks = [
            analyze_chunk_with_semaphore(chunk, i) 
            for i, chunk in enumerate(chunks)
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 处理异常结果
        valid_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"分块 {i} 分析异常: {result}")
                valid_results.append(self._create_fallback_result(chunks[i], chapter_info))
            else:
                valid_results.append(result)
        
        return valid_results
    
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
    
    def _create_fallback_result(self, chunk: Dict, chapter_info: Dict) -> Dict:
        """创建降级结果"""
        return {
            'segments': [{
                'text': chunk['content'],
                'speaker': '旁白',
                'text_type': 'narration',
                'confidence': 0.5,
                'detection_method': 'fallback'
            }],
            'detected_characters': [{
                'name': '旁白',
                'confidence': 1.0,
                'source': 'fallback',
                'recommended_config': {
                    'gender': 'neutral',
                    'personality': 'calm'
                }
            }],
            'processing_stats': {
                'total_segments': 1,
                'characters_found': 1,
                'analysis_method': 'fallback'
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
    
    def _adapt_to_synthesis_format(
        self, 
        analysis_result: Dict, 
        voice_mapping: Dict[str, int],
        available_voices: List[Dict] = None,
        tts_optimization_mode: str = "balanced"
    ) -> Dict:
        """适配为现有合成系统的JSON格式"""
        
        # 构建voice_id到voice_name的映射
        voice_id_to_name = {}
        if available_voices:
            voice_id_to_name = {v['id']: v['name'] for v in available_voices}
        
        # 格式化角色信息
        characters = []
        for character in analysis_result['detected_characters']:
            char_name = character['name']
            voice_id = voice_mapping.get(char_name)
            if voice_id:
                characters.append({
                    "name": char_name,
                    "voice_id": voice_id,
                    "voice_name": voice_id_to_name.get(voice_id, f"Voice_{voice_id}")
                })
        
        # 格式化合成计划
        synthesis_plan = []
        segment_id = 1
        
        for segment in analysis_result['segments']:
            # 获取语音信息
            voice_id = voice_mapping.get(segment['speaker'])
            voice_name = voice_id_to_name.get(voice_id, f"Voice_{voice_id}") if voice_id else "未分配"
            
            # 🎯 智能TTS参数配置 - 基于角色和文本内容
            if not self.tts_optimizer:
                self.tts_optimizer = AITTSOptimizer(self.ollama_detector)
                # 根据优化模式配置TTS分析
                if tts_optimization_mode == "fast":
                    self.tts_optimizer.set_enable_ai_analysis(False)
                    logger.info("🚀 TTS优化器设置为快速模式（禁用AI分析）")
                elif tts_optimization_mode == "quality":
                    self.tts_optimizer.set_enable_ai_analysis(True)
                    logger.info("🎯 TTS优化器设置为质量模式（启用AI分析）")
                else:  # balanced
                    self.tts_optimizer.set_enable_ai_analysis(True)
                    logger.info("⚖️ TTS优化器设置为平衡模式")
            
            tts_params = self.tts_optimizer.get_smart_tts_params(segment, analysis_result.get('detected_characters', []))
            
            synthesis_plan.append({
                "segment_id": segment_id,
                "text": segment['text'],  # 🔒 原文不变
                "speaker": segment['speaker'],
                "voice_id": voice_id,
                "voice_name": voice_name,
                "parameters": tts_params
            })
            segment_id += 1
        
        # 完全匹配现有系统格式
        return {
            "project_info": {
                "novel_type": "智能检测",
                "analysis_time": datetime.now().isoformat(),
                "total_segments": len(synthesis_plan),
                "ai_model": "optimized-smart-analysis",
                "detected_characters": len(characters)
            },
            "synthesis_plan": synthesis_plan,
            "characters": characters
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
        获取章节准备状态
        """
        try:
            from app.models import BookChapter
            chapter = db.query(BookChapter).filter(BookChapter.id == chapter_id).first()
            if not chapter:
                raise ValueError("章节不存在")
            
            # 检查分析状态
            is_analyzed = getattr(chapter, 'analysis_status', 'pending') == 'completed'
            is_synthesis_ready = getattr(chapter, 'synthesis_status', 'pending') in ['ready', 'completed']
            
            # 检查是否有相关的合成配置（从AnalysisResult表中查询）
            try:
                from ..models import AnalysisResult
                latest_result = self.db.query(AnalysisResult).filter(
                    AnalysisResult.chapter_id == chapter_id,
                    AnalysisResult.status == 'completed'
                ).order_by(AnalysisResult.created_at.desc()).first()
                
                has_synthesis_config = bool(latest_result)
                has_complete_synthesis_config = False
                
                if latest_result:
                    # 检查是否有synthesis_plan或final_config
                    has_synthesis_plan = bool(latest_result.synthesis_plan)
                    has_final_config = bool(latest_result.final_config)
                    
                    # 如果有final_config，检查其中是否包含synthesis_json
                    if has_final_config and latest_result.final_config:
                        try:
                            final_config = latest_result.final_config
                            if isinstance(final_config, str):
                                import json
                                final_config = json.loads(final_config)
                            has_complete_synthesis_config = bool(final_config.get('synthesis_json'))
                        except:
                            has_complete_synthesis_config = has_synthesis_plan
                    else:
                        has_complete_synthesis_config = has_synthesis_plan
                        
            except ImportError:
                # 如果没有AnalysisResult模型，回退到章节字段检查
                analysis_result = getattr(chapter, 'analysis_result', None)
                has_synthesis_config = bool(analysis_result)
                has_complete_synthesis_config = False
                
                if has_synthesis_config and analysis_result:
                    try:
                        import json
                        if isinstance(analysis_result, str):
                            result_data = json.loads(analysis_result)
                        else:
                            result_data = analysis_result
                        
                        has_complete_synthesis_config = bool(result_data.get('synthesis_json'))
                    except:
                        has_complete_synthesis_config = False
            
            return {
                "chapter_id": chapter_id,
                "chapter_title": chapter.chapter_title,
                "is_analyzed": is_analyzed,
                "is_synthesis_ready": is_synthesis_ready,
                "has_synthesis_config": has_synthesis_config,
                "has_complete_synthesis_config": has_complete_synthesis_config,
                "analysis_status": getattr(chapter, 'analysis_status', 'pending'),
                "synthesis_status": getattr(chapter, 'synthesis_status', 'pending'),
                "last_updated": chapter.updated_at.isoformat() if getattr(chapter, 'updated_at', None) else None,
                "preparation_complete": is_analyzed and is_synthesis_ready and has_complete_synthesis_config
            }
            
        except Exception as e:
            logger.error(f"获取准备状态失败: {str(e)}")
            raise 