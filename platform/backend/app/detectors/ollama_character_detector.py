"""
Ollama AI角色检测器
使用大语言模型进行智能角色识别和分析
"""

import json
import logging
import os
import requests
import time
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class OllamaCharacterDetector:
    """基于Ollama的角色检测器 - 优化版使用14B模型"""
    
    def __init__(self, model_name: str = "auto", ollama_url: str = None):
        self.base_model_name = model_name
        self.model_name = model_name  # 初始化时设置默认值
        self.api_url = ollama_url or "http://localhost:11434/api/generate"
        self.logger = logging.getLogger(__name__)
        
        # 读取系统设置
        self.settings = self._load_system_settings()
        
        # 智能模型选择策略
        self.model_selection_strategy = {
            "short_text_threshold": 2000,  # 短文本阈值
            "long_text_threshold": 6000,   # 长文本阈值
            "short_model": "qwen2.5:14b",  # 短文本使用14B高精度模型
            "long_model": "qwen2.5:7b"     # 长文本使用7B高速模型
        }
        
        mode = "快速模式" if self.settings.get("fastModeEnabled", True) else "标准模式"
        self.logger.info(f"🚀 OllamaCharacterDetector 初始化完成，分析模式: {mode}")
    
    def _load_system_settings(self) -> dict:
        """加载系统设置"""
        try:
            import os
            config_file = os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                "config", "data", "system_settings.json"
            )
            if os.path.exists(config_file):
                import json
                with open(config_file, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                    return settings.get("ai", {})
        except Exception as e:
            self.logger.warning(f"无法加载系统设置，使用默认值: {e}")
        
        # 默认快速模式设置
        return {
            "fastModeEnabled": True,
            "analysisTimeout": 60,
            "enableSecondaryCheck": False
        }

    def _select_optimal_model(self, text: str) -> str:
        """🎯 智能模型选择：根据文本长度选择最优模型"""
        if self.base_model_name != "auto":
            # 如果用户手动指定模型，直接使用
            selected_model = self.base_model_name
            self.logger.info(f"🎯 使用指定模型: {selected_model}")
        else:
            text_length = len(text)
            strategy = self.model_selection_strategy
            
            if text_length <= strategy["short_text_threshold"]:
                # 短文本：使用14B高精度模型
                selected_model = strategy["short_model"]
                self.logger.info(f"📝 短文本({text_length}字符) → 使用高精度模型: {selected_model}")
            elif text_length >= strategy["long_text_threshold"]:
                # 长文本：使用7B高速模型
                selected_model = strategy["long_model"]
                self.logger.info(f"📄 长文本({text_length}字符) → 使用高速模型: {selected_model}")
            else:
                # 中等文本：使用14B模型但调整参数
                selected_model = strategy["short_model"]
                self.logger.info(f"📝 中等文本({text_length}字符) → 使用平衡模型: {selected_model}")
        
        # 保存选择的模型名称到实例变量
        self.model_name = selected_model
        return selected_model

    def _get_model_options(self) -> Dict:
        """🎯 获取平衡的分析参数 - 修复内容丢失问题"""
        if self.model_name == "qwen2.5:14b":
            # 14B模型：确保输出完整性
            return {
                "temperature": 0.2,    # 低温度确保稳定性
                "top_p": 0.9,          # 标准采样
                "max_tokens": 8000,    # 足够的输出长度确保完整性
                "num_ctx": 8192        # 足够的上下文长度
            }
        else:
            # 7B模型：平衡速度和完整性
            return {
                "temperature": 0.3,    # 适中温度
                "top_p": 0.9,          # 快速采样
                "max_tokens": 6000,    # 充足的输出长度
                "num_ctx": 6144        # 充足的上下文
            }

    def _smart_chunk_text(self, text: str, max_chunk_size: int = 3000) -> List[Dict]:
        """🚀 智能分块：按段落和句子边界分块，避免截断"""
        import re
        
        # 如果文本较短，不需要分块
        if len(text) <= max_chunk_size:
            return [{"chunk_id": 0, "text": text, "start_pos": 0, "end_pos": len(text)}]
        
        logger.info(f"文本过长({len(text)}字符)，开始智能分块(最大{max_chunk_size}字符/块)")
        
        chunks = []
        chunk_id = 0
        
        # 首先按双换行符分段
        paragraphs = text.split('\n\n')
        current_chunk = ""
        current_start = 0
        
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
                
            # 如果加入当前段落后超过限制，先保存当前块
            if len(current_chunk) + len(para) > max_chunk_size and current_chunk:
                # 保存当前块
                chunks.append({
                    "chunk_id": chunk_id,
                    "text": current_chunk.strip(),
                    "start_pos": current_start,
                    "end_pos": current_start + len(current_chunk)
                })
                chunk_id += 1
                current_start += len(current_chunk)
                current_chunk = para + "\n\n"
            else:
                current_chunk += para + "\n\n"
        
        # 保存最后一个块
        if current_chunk.strip():
            chunks.append({
                "chunk_id": chunk_id,
                "text": current_chunk.strip(),
                "start_pos": current_start,
                "end_pos": current_start + len(current_chunk)
            })
        
        # 如果某个块仍然过大，按句子进一步分块
        final_chunks = []
        for chunk in chunks:
            if len(chunk["text"]) > max_chunk_size:
                sub_chunks = self._split_by_sentences(chunk["text"], max_chunk_size, chunk["start_pos"])
                final_chunks.extend(sub_chunks)
            else:
                final_chunks.append(chunk)
        
        logger.info(f"智能分块完成：{len(text)}字符 → {len(final_chunks)}块，平均{len(text)//len(final_chunks)}字符/块")
        return final_chunks
    
    def _split_by_sentences(self, text: str, max_size: int, start_offset: int = 0) -> List[Dict]:
        """按句子边界进一步分块"""
        import re
        
        # 按句号、问号、感叹号分句
        sentences = re.split(r'([。！？][""]?)', text)
        chunks = []
        chunk_id = len(chunks)
        current_chunk = ""
        current_start = start_offset
        
        i = 0
        while i < len(sentences):
            sentence = sentences[i]
            # 如果是标点符号，与前一句合并
            if i + 1 < len(sentences) and sentences[i + 1] in ['。', '！', '？', '"', '"']:
                sentence += sentences[i + 1]
                i += 2
            else:
                i += 1
            
            if len(current_chunk) + len(sentence) > max_size and current_chunk:
                chunks.append({
                    "chunk_id": chunk_id,
                    "text": current_chunk.strip(),
                    "start_pos": current_start,
                    "end_pos": current_start + len(current_chunk)
                })
                chunk_id += 1
                current_start += len(current_chunk)
                current_chunk = sentence
            else:
                current_chunk += sentence
        
        # 保存最后一个块
        if current_chunk.strip():
            chunks.append({
                "chunk_id": chunk_id,
                "text": current_chunk.strip(),
                "start_pos": current_start,
                "end_pos": current_start + len(current_chunk)
            })
        
        return chunks
    
    def _merge_chunk_results(self, chunk_results: List[Dict]) -> Dict:
        """🔗 合并分块分析结果"""
        merged_segments = []
        merged_characters = {}
        total_order = 0
        
        for chunk_result in chunk_results:
            chunk_id = chunk_result.get("chunk_id", 0)
            
            # 合并segments，调整order
            for segment in chunk_result.get("segments", []):
                segment["order"] = total_order
                segment["chunk_id"] = chunk_id  # 标记来源块
                merged_segments.append(segment)
                total_order += 1
            
            # 合并characters，按名字去重
            for char in chunk_result.get("characters", []):
                char_name = char["name"]
                if char_name in merged_characters:
                    # 合并频次和置信度
                    existing = merged_characters[char_name]
                    existing["frequency"] += char.get("frequency", 1)
                    
                    # 🔧 修复：正确获取confidence字段
                    char_confidence = char.get("confidence", 0.5)
                    if char_confidence is None:
                        # 尝试从character_trait中获取
                        char_trait = char.get("character_trait", {})
                        char_confidence = char_trait.get("confidence", 0.5)
                    
                    existing_confidence = existing.get("confidence", 0.5)
                    if existing_confidence is None:
                        existing_trait = existing.get("character_trait", {})
                        existing_confidence = existing_trait.get("confidence", 0.5)
                    
                    # 设置更高的置信度
                    if "character_trait" in existing:
                        existing["character_trait"]["confidence"] = max(existing_confidence, char_confidence)
                    else:
                        existing["confidence"] = max(existing_confidence, char_confidence)
                    
                    # 保留更详细的描述
                    char_desc = char.get("personality_description", "")
                    existing_desc = existing.get("personality_description", "")
                    if len(char_desc) > len(existing_desc):
                        existing["personality_description"] = char_desc
                        # 同时更新recommended_config中的描述
                        if "recommended_config" in existing:
                            existing["recommended_config"]["personality_description"] = char_desc
                else:
                    merged_characters[char_name] = char
        
        # 转换为列表并按频次排序
        characters_list = list(merged_characters.values())
        characters_list.sort(key=lambda x: x.get("frequency", 0), reverse=True)
        
        logger.info(f"分块结果合并完成：{len(merged_segments)}个段落，{len(characters_list)}个角色")
        
        return {
            "segments": merged_segments,
            "characters": characters_list
        }
    
    async def analyze_text(self, text: str, chapter_info: dict) -> dict:
        """使用Ollama分析文本中的角色 - 支持智能分块处理"""
        # 🔧 使用统一的WebSocket管理器
        try:
            from app.websocket.manager import websocket_manager
            
            async def send_analysis_progress(session_id, progress, message):
                await websocket_manager.publish_to_topic(
                    f"analysis_session_{session_id}",
                    {
                        "type": "progress_update",
                        "data": {
                            "progress": progress,
                            "message": message,
                            "session_id": session_id
                        }
                    }
                )
        except ImportError:
            # 如果导入失败，定义一个mock函数
            async def send_analysis_progress(session_id, progress, message):
                logger.info(f"[进度 {progress}%] {message}")
            logger.warning("无法导入websocket_manager，使用日志记录进度")
        
        start_time = time.time()
        session_id = chapter_info.get('session_id', chapter_info['chapter_id'])
        
        try:
            # 发送开始分析进度
            await send_analysis_progress(session_id, 10, f"开始分析章节: {chapter_info['chapter_title']}")
            
            # 🚀 智能分块处理：长文本自动分块
            text_length = len(text)
            
            # 🎯 智能模型选择
            self.model_name = self._select_optimal_model(text)
            
            # 🎯 简化分块策略：提高阈值减少分块
            if self.model_name == "qwen2.5:14b":
                chunk_threshold = 6000  # 14B模型：6000字符启用分块
                max_chunk_size = 4000   # 14B模型：每块4000字符
            else:
                chunk_threshold = 8000  # 7B模型：8000字符启用分块  
                max_chunk_size = 5000   # 7B模型：每块5000字符
            
            if text_length > chunk_threshold:
                logger.info(f"文本长度{text_length}字符，启用智能分块处理({self.model_name})")
                await send_analysis_progress(session_id, 20, f"文本较长({text_length}字符)，启用智能分块处理...")
                
                # 智能分块
                chunks = self._smart_chunk_text(text, max_chunk_size=max_chunk_size)
                await send_analysis_progress(session_id, 30, f"已分为{len(chunks)}个块，开始逐块分析...")
                
                # 逐块分析
                chunk_results = []
                progress_step = 50 / len(chunks)  # 50%的进度用于分块分析
                
                for i, chunk in enumerate(chunks):
                    chunk_progress = 30 + int(i * progress_step)
                    await send_analysis_progress(session_id, chunk_progress, f"分析第{i+1}/{len(chunks)}块...")
                    
                    chunk_result = await self._analyze_single_chunk(chunk["text"], chunk["chunk_id"])
                    chunk_result["chunk_id"] = chunk["chunk_id"]
                    chunk_results.append(chunk_result)
                
                await send_analysis_progress(session_id, 80, "正在合并分块分析结果...")
                
                # 合并分块结果
                result = self._merge_chunk_results(chunk_results)
                
                # 完整性校验（基于原文）
                completeness_valid = self._validate_completeness(text, result['segments'])
                
                analysis_method = f"ollama_ai_chunked_{len(chunks)}_blocks"
                
            else:
                logger.info(f"文本长度{text_length}字符，使用单次分析")
                await send_analysis_progress(session_id, 30, "正在调用AI模型进行角色识别...")
                
                # 直接单次分析
                result = await self._analyze_single_text(text)
                completeness_valid = self._validate_completeness(text, result['segments'])
                analysis_method = "ollama_ai_single"
                chunks = []  # 单次分析时为空列表
            
            processing_time = time.time() - start_time
            
            await send_analysis_progress(session_id, 100, f"分析完成，识别到{len(result['characters'])}个角色")
            
            # 智能分析阶段：返回所有识别到的角色（不过滤已存在的）
            all_characters = result['characters']
            
            # 🔥 修复：保留已有的processing_stats字段，特别是secondary_check_applied
            existing_stats = result.get('processing_stats', {})
            
            return {
                "chapter_id": chapter_info['chapter_id'],
                "chapter_title": chapter_info['chapter_title'],
                "chapter_number": chapter_info['chapter_number'],
                "detected_characters": all_characters,  # 返回所有角色
                "segments": result['segments'],
                "processing_stats": {
                    # 保留已有的字段
                    **existing_stats,
                    # 更新或添加新的字段
                    "total_segments": len(result['segments']),
                    "dialogue_segments": len([s for s in result['segments'] if s['text_type'] == 'dialogue']),
                    "narration_segments": len([s for s in result['segments'] if s['text_type'] == 'narration']),
                    "characters_found": len(result['characters']),
                    "new_characters_found": len(result['characters']),
                    "analysis_method": analysis_method,
                    "processing_time": round(processing_time, 2),
                    "text_length": len(text),
                    "ai_model": self.model_name,
                    "completeness_validated": completeness_valid,  # 🔥 新增：完整性校验结果
                    "chunk_count": len(chunks) if text_length > chunk_threshold else 1  # 🔥 新增：分块数量
                }
            }
                
        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"❌ Ollama角色分析异常失败: {str(e)}")
            await send_analysis_progress(session_id, 0, f"AI分析失败: {str(e)}")
            raise Exception(f"Ollama角色分析失败: {str(e)}")
    
    async def _analyze_single_text(self, text: str) -> Dict:
        """单次分析文本（不分块）"""
        
        # 🔥 修复：在分析前选择最优模型
        self._select_optimal_model(text)
        
        max_retries = 3
        response = None
        
        for attempt in range(max_retries):
            try:
                prompt = self._build_comprehensive_analysis_prompt(text)
                response = self._call_ollama(prompt)
                
                if response:
                    break
                else:
                    logger.warning(f"第{attempt + 1}次尝试失败，Ollama返回空响应")
                    if attempt < max_retries - 1:
                        time.sleep(2)  # 等待2秒后重试
                    
            except Exception as e:
                logger.error(f"第{attempt + 1}次尝试异常: {str(e)}")
                if attempt < max_retries - 1:
                    time.sleep(2)  # 等待2秒后重试
                else:
                    raise e
        
        if response:
            # 解析Ollama返回的完整结果
            result = self._parse_comprehensive_response(response)
            
            # 🔥 修复：增加内容完整性校验和重试
            logger.info(f"🔍 调用完整性校验前 - result keys: {list(result.keys())}")
            segments_list = result.get('segments', [])
            logger.info(f"🔍 调用完整性校验前 - segments数量: {len(segments_list)}")
            if len(segments_list) > 0:
                first_seg = segments_list[0]
                logger.info(f"🔍 第一个segment: order={first_seg.get('order')}, text_len={len(first_seg.get('text', ''))}, speaker='{first_seg.get('speaker')}'")
            
            completeness_valid = self._validate_completeness(text, result['segments'])
            if not completeness_valid:
                logger.warning("内容完整性校验失败，尝试重新分析")
                
                # 如果完整性校验失败，尝试使用更详细的提示词重新分析
                detailed_prompt = self._build_detailed_analysis_prompt(text)
                retry_response = self._call_ollama(detailed_prompt)
                
                if retry_response:
                    retry_result = self._parse_comprehensive_response(retry_response)
                    retry_completeness = self._validate_completeness(text, retry_result['segments'])
                    
                    if retry_completeness:
                        result = retry_result
                        logger.info("重新分析成功，内容完整性校验通过")
                    else:
                        logger.warning("重新分析仍未通过完整性校验，使用原结果并记录警告")
            
            # 🚀 根据系统设置决定是否启用二次检查机制
            if self.settings.get("enableSecondaryCheck", False):
                result = await self._secondary_check_analysis(text, result)
            else:
                self.logger.info("快速模式：跳过二次检查机制")
            
            return result
        else:
            # Ollama调用失败，直接抛出错误
            logger.error("❌ Ollama API调用失败，没有返回有效响应")
            raise Exception("Ollama API调用失败，没有返回有效响应")
    
    async def _secondary_check_analysis(self, original_text: str, primary_result: Dict) -> Dict:
        """🚀 二次检查机制：通用验证和修复"""
        logger.info("🔍 执行通用二次检查...")
        
        segments = primary_result['segments']
        
        # 1. 基础完整性验证
        refined_segments = self._validate_and_fix_completeness(original_text, segments)
        
        # 2. 通用格式标准化（移除过度具体的正则表达式匹配）
        refined_segments = self._universal_format_normalization(refined_segments)
        
        # 3. 更新结果
        primary_result['segments'] = refined_segments
        
        # 确保processing_stats字段存在
        if 'processing_stats' not in primary_result:
            primary_result['processing_stats'] = {}
        
        primary_result['processing_stats']['total_segments'] = len(refined_segments)
        primary_result['processing_stats']['dialogue_segments'] = len([s for s in refined_segments if s['text_type'] == 'dialogue'])
        primary_result['processing_stats']['narration_segments'] = len([s for s in refined_segments if s['text_type'] == 'narration'])
        primary_result['processing_stats']['secondary_check_applied'] = True
        primary_result['processing_stats']['model_version'] = "qwen2.5:14b"
        
        logger.info(f"✅ 通用二次检查完成，段落数: {len(refined_segments)}")
        return primary_result

    def _universal_format_normalization(self, segments: List[Dict]) -> List[Dict]:
        """通用格式标准化：基于语义而非特定模式"""
        normalized_segments = []
        
        for segment in segments:
            text = segment['text'].strip()
            speaker = segment['speaker'].strip()
            text_type = segment['text_type']
            
            # 1. 标准化角色名称
            if speaker and speaker != '旁白':
                # 移除常见的说话标记
                speaker = speaker.replace('说', '').replace('道', '').replace('：', '').replace(':', '').strip()
            
            # 2. 标准化文本内容
            if text:
                # 移除多余的空格和换行
                text = ' '.join(text.split())
                
                # 确保引号内容被正确识别为对话
                if text.startswith('"') and text.endswith('"') and text_type == 'narration':
                    text = text[1:-1]  # 移除引号
                    text_type = 'dialogue'
                elif text.startswith('"') and text.endswith('"') and text_type == 'dialogue':
                    text = text[1:-1]  # 移除引号
            
            # 3. 验证speaker和text_type的一致性
            if text_type == 'dialogue' and speaker == '旁白':
                # 对话不应该是旁白，尝试从文本中提取角色
                speaker = self._extract_speaker_from_context(text) or '未知角色'
            elif text_type == 'narration' and speaker != '旁白':
                # 叙述应该是旁白
                speaker = '旁白'
            
            # 4. 过滤空内容
            if text:
                normalized_segments.append({
                    'order': segment['order'],
                    'text': text,
                    'speaker': speaker,
                    'confidence': segment.get('confidence', 0.9),
                    'detection_rule': segment.get('detection_rule', 'ai_analysis'),
                    'text_type': text_type
                })
        
        return normalized_segments

    def _extract_speaker_from_context(self, text: str) -> Optional[str]:
        """从上下文中提取说话者（简化版）"""
        # 简单的角色名提取，不使用复杂的正则表达式
        import re
        
        # 查找可能的角色名（2-4个中文字符）
        potential_names = re.findall(r'[一-龯]{2,4}', text)
        
        # 过滤掉常见的非角色词汇
        excluded_words = ['这个', '那个', '什么', '哪里', '为什么', '怎么', '可是', '但是', '所以', '因为', '如果', '虽然', '然后', '接着', '最后', '此时', '此后', '突然', '忽然', '显然', '明显', '似乎', '好像', '仿佛', '原来', '只见', '只听', '只觉', '但见', '但听', '却见', '却听', '便见']
        
        for name in potential_names:
            if name not in excluded_words and len(name) >= 2:
                return name
        
        return None

    def _detect_and_refine_mixed_sentences(self, segments: List[Dict]) -> List[Dict]:
        """检测并精细化分割混合句子 - 通用版本"""
        import re
        
        # 新的通用方法：不使用特定的正则表达式模式
        # 而是基于语义特征来判断是否需要分离
        
        logger.info("🔍 使用通用混合句子检测...")
        
        refined_segments = []
        
        for segment in segments:
            text = segment['text'].strip()
            
            # 通用检测原则：如果一个segment包含引号和非引号内容，可能需要分离
            # 但不使用复杂的正则表达式，而是基于简单的语义判断
            
            # 1. 检查是否包含引号
            has_quotes = '"' in text or '"' in text or "'" in text or "'" in text
            
            # 2. 检查是否包含明显的动作描述词汇
            action_words = ['说', '道', '叫', '喊', '问', '答', '回复', '表示', '勒马', '转身', '起身', '坐下', '走向', '奔来', '离开', '停下', '举手', '放下', '抬头', '低头', '点头', '摇头', '皱眉', '微笑', '冷笑', '叹气', '咳嗽', '清嗓', '发来', '消息', '震动', '打断']
            
            has_action_words = any(word in text for word in action_words)
            
            # 3. 如果既包含引号又包含动作词汇，可能是混合文本
            if has_quotes and has_action_words and len(text) > 10:
                logger.info(f"检测到可能的混合文本: {text[:50]}...")
                
                # 不进行复杂的分离处理，而是记录日志并保持原样
                # 让改进的提示词在第一次分析时处理这种情况
                logger.info("依赖改进的提示词处理混合文本，不进行后处理分离")
            
            # 保持原segment不变
            refined_segments.append(segment)
        
        logger.info(f"通用混合句子检测完成，保持{len(refined_segments)}个segment不变")
        return refined_segments

    def _basic_format_normalization(self, segments: List[Dict]) -> List[Dict]:
        """基础格式标准化 - 简化版，适配14B模型"""
        normalized_segments = []
        
        for segment in segments:
            text = segment['text'].strip()
            speaker = segment['speaker']
            
            # 基础清理：去除多余引号
            if text.startswith('"') and text.endswith('"'):
                text = text[1:-1]
            
            # 确保旁白标记正确
            if text.startswith('旁白：'):
                text = text[3:].strip()
                speaker = '旁白'
            
            # 基础角色名规范化
            if speaker and speaker != '旁白':
                speaker = speaker.replace('：', '').replace(':', '').strip()
            
            segment['text'] = text
            segment['speaker'] = speaker
            normalized_segments.append(segment)
        
        return normalized_segments

    def _refine_grammar_structure(self, segments: List[Dict]) -> List[Dict]:
        """精细化语法结构分析"""
        import re
        
        refined_segments = []
        
        for segment in segments:
            text = segment['text'].strip()
            
            # 处理引号内容
            if '"' in text or '"' in text or "'" in text or "'" in text:
                # 标准化引号
                text = text.replace('"', '"').replace('"', '"').replace("'", '"').replace("'", '"')
                
                # 如果整个文本被引号包围，这是纯对话
                if text.startswith('"') and text.endswith('"') and text.count('"') == 2:
                    segment['text'] = text[1:-1]  # 去掉引号
                    segment['text_type'] = 'dialogue'
                elif text.startswith('"') and text.endswith('"') and text.count('"') > 2:
                    # 复杂嵌套引号，需要特殊处理
                    pass  # 暂时保持原样
            
            # 处理旁白标记
            if text.startswith('旁白：') or text.startswith('旁白:'):
                segment['text'] = text[3:].strip()
                segment['speaker'] = '旁白'
                segment['text_type'] = 'narration'
            
            # 修正错误分类：检测明显应该是旁白的内容
            if segment['text_type'] == 'dialogue' and segment['speaker'] != '旁白':
                # 检测通用描述性动词和词汇模式
                narration_indicators = [
                    # 基础动作动词
                    '走', '跑', '站', '坐', '躺', '起身', '抬头', '低头', '转身', '回头',
                    '看', '望', '盯', '瞧', '瞄', '瞅', '观察', '注视', '凝视',
                    '说', '讲', '道', '言', '语', '话', '声', '音', '响', '听',
                    '想', '思', '念', '忆', '记', '忘', '知', '觉', '感', '察',
                    '拿', '取', '抓', '握', '放', '扔', '递', '交', '给', '送',
                    # 通用连接词和副词
                    '然后', '接着', '随即', '立即', '马上', '顿时', '突然', '忽然',
                    '只见', '只听', '只觉', '但见', '但听', '却见', '却听', '便见',
                    '原来', '显然', '明显', '似乎', '好像', '仿佛', '如同', '犹如',
                    # 描述性词汇
                    '发现', '意识到', '察觉', '感到', '觉得', '认为', '以为', '料想'
                ]
                
                # 如果包含太多描述性词汇，可能是旁白
                narration_count = sum(1 for indicator in narration_indicators if indicator in text)
                if narration_count >= 2:  # 包含2个或更多描述性词汇
                    segment['text_type'] = 'narration'
                    segment['speaker'] = '旁白'
                    segment['confidence'] = 0.9
                    segment['detection_rule'] = 'secondary_check_narration_fix'
            
            refined_segments.append(segment)
        
        return refined_segments

    def _validate_and_fix_completeness(self, original_text: str, segments: List[Dict]) -> List[Dict]:
        """验证并修复文本完整性"""
        # 合并所有分段文本
        combined_text = ''.join([seg['text'] for seg in segments])
        
        # 计算完整度
        original_clean = ''.join(original_text.split())
        combined_clean = ''.join(combined_text.split())
        
        completeness_ratio = len(combined_clean) / len(original_clean) if original_clean else 0
        
        if completeness_ratio < 0.9:
            logger.warning(f"完整性不足({completeness_ratio:.2%})，尝试修复...")
            
            # 查找遗漏的文本部分
            missing_parts = []
            original_lines = original_text.strip().split('\n')
            processed_lines = set()
            
            for segment in segments:
                # 找到原文中对应的行
                for line in original_lines:
                    if line.strip() and line.strip() in segment['text']:
                        processed_lines.add(line.strip())
            
            # 添加遗漏的行
            for line in original_lines:
                if line.strip() and line.strip() not in processed_lines:
                    missing_parts.append(line.strip())
            
            # 将遗漏部分添加为旁白
            for i, missing in enumerate(missing_parts):
                segments.append({
                    'order': len(segments) + i + 1,
                    'text': missing,
                    'speaker': '旁白',
                    'confidence': 0.8,
                    'detection_rule': 'completeness_fix',
                    'text_type': 'narration'
                })
            
            logger.info(f"修复完成，添加了{len(missing_parts)}个遗漏段落")
        
        # 重新排序
        segments.sort(key=lambda x: x['order'])
        for i, segment in enumerate(segments):
            segment['order'] = i + 1
        
        return segments

    async def _analyze_single_chunk(self, chunk_text: str, chunk_id: int) -> Dict:
        """分析单个分块"""
        logger.info(f"开始分析第{chunk_id}块，长度{len(chunk_text)}字符")
        
        try:
            prompt = self._build_comprehensive_analysis_prompt(chunk_text)
            response = self._call_ollama(prompt)
            
            if response:
                result = self._parse_comprehensive_response(response)
                
                # 🔥 根据系统设置决定是否启用分块的二次检查
                if self.settings.get("enableSecondaryCheck", False):
                    result = await self._secondary_check_analysis(chunk_text, result)
                else:
                    self.logger.debug("快速模式：跳过分块二次检查")
                
                logger.info(f"第{chunk_id}块分析完成：{len(result.get('segments', []))}段落，{len(result.get('characters', []))}个角色")
                return result
            else:
                logger.warning(f"第{chunk_id}块分析失败，返回空结果")
                return {"segments": [], "characters": []}
                
        except Exception as e:
            logger.error(f"第{chunk_id}块分析异常: {str(e)}")
            return {"segments": [], "characters": []}
    
    def _validate_completeness(self, original_text: str, segments: List[Dict]) -> bool:
        """🔥 新增：校验分析结果的完整性"""
        try:
            # 统计原文字数（去除空格和换行）
            original_chars = len(original_text.replace(' ', '').replace('\n', '').replace('\r', ''))
            
            # 🔍 调试：检查segments参数
            logger.info(f"🔍 完整性校验 - segments数量: {len(segments)}")
            if len(segments) > 0:
                logger.info(f"🔍 第一个segment示例: {segments[0]}")
                logger.info(f"🔍 最后一个segment示例: {segments[-1]}")
            else:
                logger.error(f"❌ segments为空列表！这是问题所在")
            
            # 统计segments字数（去除空格和换行）
            segment_chars = sum(len(seg.get('text', '').replace(' ', '').replace('\n', '').replace('\r', '')) for seg in segments)
            
            # 🔍 调试：详细统计信息
            if segment_chars == 0 and len(segments) > 0:
                logger.warning(f"异常：有{len(segments)}个segments但总字数为0，检查segments内容")
                for i, seg in enumerate(segments[:3]):  # 只检查前3个
                    text = seg.get('text', '')
                    logger.warning(f"Segment {i}: text='{text}', length={len(text)}")
            
            # 计算完整度比例
            completeness_ratio = segment_chars / original_chars if original_chars > 0 else 0
            
            logger.info(f"内容完整性校验: 原文{original_chars}字符，分析结果{segment_chars}字符，完整度{completeness_ratio:.2%}")
            
            # 根据快速模式调整完整性阈值
            if self.settings.get("fastModeEnabled", True):
                min_ratio = 0.75  # 快速模式：75%以上认为可接受
            else:
                min_ratio = 0.85  # 标准模式：85%以上认为完整
            
            if completeness_ratio < min_ratio:
                logger.warning(f"内容完整性校验失败: 完整度仅{completeness_ratio:.2%}，阈值{min_ratio:.0%}")
                return False
            
            # 检查是否有明显的文本遗漏（通过关键词检查）
            original_keywords = self._extract_keywords(original_text)
            segment_text = ' '.join([seg.get('text', '') for seg in segments])
            segment_keywords = self._extract_keywords(segment_text)
            
            missing_keywords = original_keywords - segment_keywords
            missing_ratio = len(missing_keywords) / len(original_keywords) if original_keywords else 0
            
            # 根据快速模式调整关键词丢失容忍度
            if self.settings.get("fastModeEnabled", True):
                max_missing = 0.3  # 快速模式：允许30%关键词丢失
            else:
                max_missing = 0.2  # 标准模式：允许20%关键词丢失
            
            if missing_ratio > max_missing:
                logger.warning(f"关键词完整性校验失败: 丢失{missing_ratio:.1%}关键词，阈值{max_missing:.0%}")
                return False
            
            logger.info("内容完整性校验通过")
            return True
            
        except Exception as e:
            logger.error(f"完整性校验异常: {str(e)}")
            return False  # 校验异常时认为不完整，触发重试
    
    def _extract_keywords(self, text: str) -> set:
        """提取文本中的关键词用于完整性校验"""
        import re
        
        # 提取中文词汇（2-4个字符的词）
        chinese_words = set(re.findall(r'[\u4e00-\u9fff]{2,4}', text))
        
        # 提取人名、地名等专有名词（通常包含特定字符）
        proper_nouns = set(re.findall(r'[\u4e00-\u9fff]*[王李张刘陈杨黄赵吴周][\u4e00-\u9fff]*', text))
        
        # 提取引号内的对话关键词
        dialogue_keywords = set(re.findall(r'["""]([^"""]{2,10})["""]', text))
        
        # 合并所有关键词，取前50个最重要的
        all_keywords = chinese_words | proper_nouns | dialogue_keywords
        return set(list(all_keywords)[:50])  # 限制关键词数量，提高效率
    
    def _build_detailed_analysis_prompt(self, text: str) -> str:
        """🔥 新增：构建更详细的分析提示词，用于重试时确保完整性"""
        prompt = f"""你是一个专业的中文小说文本分析专家。请仔细分析以下小说文本，确保不遗漏任何内容。

**重要提醒：必须分析完整的文本内容，每个句子都要包含在结果中！**

文本：
{text}

详细分析要求：
1. **完整性第一**：确保每个句子、每个段落都被分析到
2. **逐句分段**：按句号、问号、感叹号等标点符号分段
3. **角色识别**：准确识别所有说话的角色
4. **对话分离**：将"某某说：'内容'"分为两段

分段策略：
- 每个完整的句子作为一个segment
- 对话前的动作描述（如"林渊说："）单独成段，标记为旁白
- 引号内的对话内容单独成段，标记为相应角色
- 心理活动按同样规则处理

**🎵 声音描述规则**：
- "娇喝声带着怒意" → 旁白（描述声音特征）
- "笑声传来" → 旁白（描述声音现象）
- "话音刚落" → 旁白（描述说话状态）
- 只有引号内的实际话语才是角色对话！

**📝 间接引述对话通用规则**：
当遇到"某某[动作]：'内容'"格式时，必须分离：
- 动作描述部分 → 旁白
- 引述内容部分 → 相应角色
- 适用于：说道、写道、下旨、传话、告知、命令、询问等所有引述形式

**🗨️ 自言自语和心理活动特殊处理**：
- "自言自语道："、"暗自想道："、"心中念叨："等描述是旁白
- 引号内的实际内容才是角色的话语或心理活动
- 示例："白骨精自言自语道：'造化！'" → 分为两段：
  * "白骨精自言自语道：" → 旁白
  * "造化！" → 白骨精

输出要求：
- 必须包含原文的每个字符（除了标点符号的调整）
- segment数量应该与原文句子数量基本对应
- 不能跳过任何内容段落

输出格式（严格JSON）：
{{
  "segments": [
    {{"order": 1, "text": "完整的句子内容", "speaker": "说话者", "text_type": "dialogue/narration/inner_monologue", "confidence": 0.9}}
  ],
  "characters": [
    {{"name": "角色名", "frequency": 出现次数, "gender": "male/female/neutral", "personality": "calm/brave/gentle", "personality_description": "性格描述", "is_main_character": true/false, "confidence": 0.8}}
  ]
}}

**再次强调：不能遗漏任何文本内容！每个句子都必须在segments中体现！**"""
        
        return prompt

    def _detect_novel_type(self, text: str) -> str:
        """🆕 检测小说类型，为后续分析提供上下文"""
        # 取文本前1000字符进行类型分析
        sample_text = text[:1000] if len(text) > 1000 else text
        
        prompt = f"""你是一个专业的中文小说类型识别专家。请分析以下小说文本片段，判断其所属类型。

文本片段：
{sample_text}

请根据以下特征判断小说类型：

**古代/古装小说**：
- 时代背景：古代中国、朝代、皇帝、官员
- 语言特色：文言文色彩、古代称谓
- 关键词：陛下、皇上、公主、王爷、大人、臣、奴婢、府邸、朝廷

**现代/都市小说**：
- 时代背景：现代社会、城市生活
- 科技元素：手机、电脑、网络、汽车、公司、博物馆
- 关键词：老板、经理、同事、手机、短信、电话、网络、公司、博物馆、导师

**武侠/仙侠小说**：
- 武功元素：内力、剑法、轻功、修炼
- 江湖背景：门派、掌门、弟子、江湖
- 关键词：师父、掌门、弟子、内力、真气、剑气、门派

**玄幻/奇幻小说**：
- 魔法元素：法术、魔法、异能、魔兽
- 异世界：大陆、王国、魔法师、战士
- 关键词：魔法、法术、魔兽、大陆、王国、异能
- 注意：如果同时包含现代元素（手机、博物馆、导师）优先判断为现代小说

**科幻小说**：
- 科技元素：未来科技、机器人、太空、时间旅行
- 关键词：机器人、外星人、太空、未来、科技、实验室

**军事/历史小说**：
- 军事元素：战争、军队、将军、士兵
- 关键词：将军、士兵、战争、军队、战场、作战

只需要输出类型名称，从以下选项中选择一个：
- ancient（古代/古装）
- modern（现代/都市）
- wuxia（武侠/仙侠）
- fantasy（玄幻/奇幻）
- scifi（科幻）
- military（军事/历史）
- unknown（无法确定）

只输出类型名称，不要其他内容："""

        try:
            response = self._call_ollama(prompt)
            if response:
                # 提取类型名称
                novel_type = response.strip().lower()
                if novel_type in ['ancient', 'modern', 'wuxia', 'fantasy', 'scifi', 'military']:
                    self.logger.info(f"检测到小说类型: {novel_type}")
                    return novel_type
                else:
                    self.logger.warning(f"未识别的小说类型: {novel_type}，使用默认类型")
                    return 'unknown'
            else:
                self.logger.error("小说类型检测失败，使用默认类型")
                return 'unknown'
        except Exception as e:
            self.logger.error(f"小说类型检测异常: {str(e)}，使用默认类型")
            return 'unknown'

    def _build_type_aware_analysis_prompt(self, text: str, novel_type: str) -> str:
        """🆕 基于小说类型构建专门的分析提示词 - 简化版适配14B模型"""
        
        prompt = f"""你是中文小说文本分析专家，使用qwen2.5:14b模型。请分析以下小说文本。

文本：{text[:4000] if len(text) > 4000 else text}

核心任务：
1. 按句子分段，识别每段的说话者
2. 区分对话、旁白、心理独白
3. 保持角色名称一致性

关键原则：
- 引号内容 = 角色对话
- 描述动作 = 旁白
- "角色说：'话语'" = 分为两段：动作(旁白) + 话语(角色)

输出JSON格式：
{{
  "segments": [
    {{"order": 1, "text": "文本内容", "speaker": "说话者", "text_type": "dialogue/narration/inner_monologue", "confidence": 0.9}}
  ],
  "characters": [
    {{"name": "角色名", "frequency": 出现次数, "gender": "male/female/neutral", "personality": "calm/brave/gentle", "is_main_character": true/false, "confidence": 0.8}}
  ]
}}

只输出JSON，不要其他文字。"""
        
        return prompt

    def _build_comprehensive_analysis_prompt(self, text: str) -> str:
        """构建平衡的分析提示词 - 确保完整性"""
        
        prompt = f"""你是专业的中文小说文本分析专家。请完整分析以下文本，确保不遗漏任何内容。

**⚠️ 重要：必须处理所有文本内容，不能遗漏任何句子！**

核心任务：
1. 按句子分段，识别每段的说话者
2. 分离混合格式："角色说：'对话'" → 两段：动作(旁白) + 对话(角色)  
3. 引号内容=角色对话，描述动作=旁白
4. 确保所有文本都在segments中体现

关键规则：
- 每个完整句子都要成为一个segment
- "XX说："等动作描述 → 旁白
- 引号内的实际话语 → 对应角色
- 纯描述性文字 → 旁白

文本：
{text}

**完整性要求：**
- segments总字数应接近原文字数
- 每个句子都必须包含在某个segment中
- 不能跳过任何内容段落

输出JSON格式：
{{
  "segments": [
    {{"order": 1, "text": "完整文本内容", "speaker": "说话者", "text_type": "dialogue/narration", "confidence": 0.9}}
  ],
  "characters": [
    {{"name": "角色名", "frequency": 出现次数, "gender": "male/female/neutral", "is_main_character": true/false, "confidence": 0.8}}
  ]
}}

只输出JSON，确保包含所有文本内容。"""
        
        return prompt

    def _call_ollama(self, prompt: str) -> Optional[str]:
        """调用Ollama API"""
        try:
            payload = {
                "model": self.model_name,
                "prompt": prompt,
                "stream": False,
                "options": self._get_model_options()
            }
            
            timeout = self.settings.get("analysisTimeout", 60)
            response = requests.post(
                self.api_url,
                json=payload,
                timeout=timeout  # 从系统设置读取超时时间
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
    
    def _parse_comprehensive_response(self, response: str) -> Dict:
        """解析Ollama返回的综合分析结果"""
        try:
            # 检查response是否为None或空
            if not response or response.strip() == '':
                logger.error("Ollama响应为空或None")
                return {
                    'segments': [],
                    'detected_characters': [],
                    'analysis_summary': {'total_segments': 0, 'total_characters': 0}
                }
            
            # 记录原始响应用于调试
            logger.info(f"Ollama原始响应: {response[:500]}...")
            
            # 提取JSON部分
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            
            if json_start != -1 and json_end != -1:
                json_str = response[json_start:json_end]
                data = json.loads(json_str)
                
                logger.info(f"解析的JSON数据: {json.dumps(data, ensure_ascii=False, indent=2)}")
                
                # 处理segments
                segments = []
                for i, seg_data in enumerate(data.get('segments', [])):
                    # 支持新的text_type: inner_monologue
                    text_type = seg_data.get('text_type', 'narration')
                    if text_type not in ['dialogue', 'narration', 'inner_monologue']:
                        text_type = 'narration'  # 默认为旁白
                        
                    # 🔧 修复：正确处理空的speaker字段
                    speaker = seg_data.get('speaker', '') or ''  # 确保不是None
                    if isinstance(speaker, str):
                        speaker = speaker.strip()
                    else:
                        speaker = ''
                    
                    if not speaker:  # 处理空字符串、None、或只有空格的情况
                        if text_type in ['narration', 'inner_monologue']:
                            speaker = '旁白'
                        else:
                            speaker = '未知角色'
                    
                    segments.append({
                        'order': seg_data.get('order', i + 1),
                        'text': seg_data.get('text', ''),
                        'speaker': speaker,
                        'confidence': seg_data.get('confidence', 0.8),
                        'detection_rule': 'ollama_ai',
                        'text_type': text_type
                    })
                
                # 处理characters
                characters = []
                for char_data in data.get('characters', []):
                    if isinstance(char_data, dict) and 'name' in char_data:
                        name = char_data.get('name', '')
                        if name and len(name) >= 2:
                            characters.append({
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
                                    'gender': self._infer_gender_smart(name, char_data.get('gender', 'unknown')),
                                    'personality': char_data.get('personality', 'calm'),
                                    'personality_description': char_data.get('personality_description', '性格特征待分析'),
                                    'personality_confidence': char_data.get('confidence', 0.8),
                                    'description': f"{name}，{self._infer_gender_smart(name, char_data.get('gender', 'unknown'))}角色，{char_data.get('personality_description', '性格特征待分析')}，在文本中出现{char_data.get('frequency', 1)}次。",
                                    'recommended_tts_params': self._get_tts_params(char_data.get('personality', 'calm')),
                                    'voice_type': f"{self._infer_gender_smart(name, char_data.get('gender', 'unknown'))}_{char_data.get('personality', 'calm')}",
                                    'color': self._get_character_color(char_data.get('personality', 'calm'))
                                }
                            })
                
                result = {
                    'segments': segments,
                    'characters': characters
                }
                
                # 🔍 调试：检查解析结果
                logger.debug(f"解析完成 - segments数量: {len(segments)}")
                logger.debug(f"解析完成 - characters数量: {len(characters)}")
                if len(segments) > 0:
                    logger.debug(f"解析完成 - 第一个segment: {segments[0]}")
                
                return result
            
            else:
                logger.error("无法从Ollama响应中提取JSON数据")
                return {'segments': [], 'characters': []}
                
        except json.JSONDecodeError as e:
            logger.error(f"解析Ollama JSON响应失败: {str(e)}")
            logger.error(f"原始响应: {response}")
            return {'segments': [], 'characters': []}
        except Exception as e:
            logger.error(f"处理Ollama响应异常: {str(e)}")
            return {'segments': [], 'characters': []}

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
    
    def _infer_gender_smart(self, name: str, ai_gender: str) -> str:
        """智能推断角色性别 - 完全依赖AI判断，移除硬编码"""
        # 如果AI已经正确识别了性别，直接使用
        if ai_gender and ai_gender in ['male', 'female', 'neutral']:
            return ai_gender
        
        # 如果AI没有返回性别信息，调用专门的性别识别AI
        try:
            gender = self._ai_infer_gender(name)
            if gender in ['male', 'female', 'neutral']:
                logger.info(f"AI推断角色 '{name}' 性别: {gender}")
                return gender
        except Exception as e:
            logger.warning(f"AI性别推断失败: {str(e)}")
        
        # 默认返回unknown，让用户手动选择
        logger.warning(f"无法推断角色 '{name}' 的性别")
        return 'unknown'
    
    def _ai_infer_gender(self, character_name: str) -> str:
        """使用AI推断角色性别"""
        try:
            prompt = f"""请判断角色 "{character_name}" 的性别。

判断规则：
1. 基于中文姓名的常见特征
2. 基于文学作品中的角色设定
3. 基于称谓、头衔的语义含义

返回格式（只返回一个词）：
- male（男性）
- female（女性）  
- neutral（中性，如旁白、叙述者）

角色名：{character_name}
性别："""

            response = self._call_ollama(prompt)
            if response:
                # 提取性别判断
                gender = response.strip().lower()
                if 'male' in gender and 'female' not in gender:
                    return 'male'
                elif 'female' in gender:
                    return 'female'
                elif 'neutral' in gender:
                    return 'neutral'
            
            return 'unknown'
            
        except Exception as e:
            logger.error(f"AI性别推断异常: {str(e)}")
            return 'unknown' 