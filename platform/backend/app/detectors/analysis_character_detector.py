"""
书籍分析模块专用角色检测器
基于Ollama AI进行智能角色识别和分析
专门为书籍分析模块优化，与智能准备模块完全隔离
"""

import json
import logging
import os
import requests
import time
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class AnalysisCharacterDetector:
    """书籍分析模块专用角色检测器 - 基于Ollama AI，专门为分析模块优化"""
    
    def __init__(self, model_name: str = "auto", ollama_url: str = None):
        self.base_model_name = model_name
        self.model_name = model_name  # 初始化时设置默认值
        from app.utils.llm_config_loader import llm_config_loader
        config = llm_config_loader.get_config()
        self.api_url = ollama_url or f"{config['base_url']}/api/generate"
        self.logger = logging.getLogger(__name__)
        
        # 读取系统设置
        self.settings = self._load_system_settings()
        
        # 分析模块专用模型选择策略
        from app.utils.llm_config_loader import llm_config_loader
        config = llm_config_loader.get_config()
        self.model_selection_strategy = {
            "short_text_threshold": 2000,  # 短文本阈值
            "long_text_threshold": 6000,   # 长文本阈值
            "short_model": config["model"],  # 使用统一配置的模型
            "long_model": config["model"]    # 使用统一配置的模型
        }
        
        mode = "快速模式" if self.settings.get("fastModeEnabled", True) else "标准模式"
        self.logger.info(f"🔍 AnalysisCharacterDetector 初始化完成，分析模式: {mode}")
    
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
                self.logger.debug(f"📝 文本{text_length}字符 → 模型: {selected_model}")
            elif text_length >= strategy["long_text_threshold"]:
                # 长文本：使用7B高速模型
                selected_model = strategy["long_model"]
                self.logger.debug(f"📄 文本{text_length}字符 → 模型: {selected_model}")
            else:
                # 中等文本：使用7B高速模型，避免超时
                selected_model = strategy["long_model"]
                self.logger.debug(f"📝 文本{text_length}字符 → 模型: {selected_model}")
        
        # 保存选择的模型名称到实例变量
        self.model_name = selected_model
        return selected_model

    def _get_model_options(self) -> Dict:
        """🎯 获取分析模块专用的模型参数"""
        if "14b" in self.model_name:
            # 14B模型：确保输出完整性
            return {
                "temperature": 0.2,    # 低温度确保稳定性
                "top_p": 0.9,          # 标准采样
                "max_tokens": 8000,    # 足够的输出长度确保完整性
                "num_ctx": 8192        # 足够的上下文长度
            }
        else:
            # 7B模型：优化速度，减少输出长度
            return {
                "temperature": 0.3,    # 适中温度
                "top_p": 0.9,          # 快速采样
                "max_tokens": 4000,    # 减少输出长度以加快速度
                "num_ctx": 4096        # 减少上下文长度以加快速度
            }

    async def analyze_text(self, text: str, chapter_info: dict) -> dict:
        """书籍分析模块专用的文本分析方法"""
        start_time = time.time()
        session_id = chapter_info.get('session_id', chapter_info['chapter_id'])
        
        try:
            # 🎯 智能模型选择
            self.model_name = self._select_optimal_model(text)
            
            # 🎯 分析模块专用分块策略
            if "14b" in self.model_name:
                chunk_threshold = 6000  # 14B模型：6000字符启用分块
                max_chunk_size = 4000   # 14B模型：每块4000字符
            else:
                chunk_threshold = 8000  # 7B模型：8000字符启用分块  
                max_chunk_size = 5000   # 7B模型：每块5000字符
            
            text_length = len(text)
            
            if text_length > chunk_threshold:
                logger.info(f"文本长度{text_length}字符，启用分析模块专用分块处理({self.model_name})")
                # 智能分块
                chunks = self._smart_chunk_text(text, max_chunk_size=max_chunk_size)
                # 逐块分析
                chunk_results = []
                
                for i, chunk in enumerate(chunks):
                    chunk_result = await self._analyze_single_chunk(chunk["text"], chunk["chunk_id"], session_id)
                    chunk_result["chunk_id"] = chunk["chunk_id"]
                    chunk_results.append(chunk_result)
                
                # 合并分块结果
                result = self._merge_chunk_results(chunk_results)
                completeness_valid = self._validate_completeness(text, result['segments'])
                analysis_method = f"analysis_chunked_{len(chunks)}_blocks"
                
            else:
                logger.info(f"文本长度{text_length}字符，使用单次分析")
                # 直接单次分析
                result = await self._analyze_single_text(text, session_id)
                completeness_valid = self._validate_completeness(text, result['segments'])
                analysis_method = "analysis_single"
                chunks = []  # 单次分析时为空列表
            
            processing_time = time.time() - start_time
            
            # 返回分析模块专用格式
            all_characters = result['characters']
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
                    "completeness_validated": completeness_valid,
                    "chunk_count": len(chunks) if text_length > chunk_threshold else 1,
                    "module": "analysis"  # 标记为分析模块
                }
            }
                
        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"❌ 分析模块角色分析失败: {str(e)}")
            raise Exception(f"分析模块角色分析失败: {str(e)}")
    
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
                    
                    # 设置更高的置信度
                    char_confidence = char.get("confidence", 0.5)
                    existing_confidence = existing.get("confidence", 0.5)
                    
                    if "character_trait" in existing:
                        existing["character_trait"]["confidence"] = max(existing_confidence, char_confidence)
                    else:
                        existing["confidence"] = max(existing_confidence, char_confidence)
                    
                    # 保留更详细的描述
                    char_desc = char.get("personality_description", "")
                    existing_desc = existing.get("personality_description", "")
                    if len(char_desc) > len(existing_desc):
                        existing["personality_description"] = char_desc
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

    async def _analyze_single_text(self, text: str, session_id: str = None) -> Dict:
        """单次分析文本（不分块）"""
        
        # 🔥 在分析前选择最优模型
        self._select_optimal_model(text)
        
        max_retries = 3
        response = None
        
        for attempt in range(max_retries):
            try:
                prompt = self._build_analysis_prompt(text)
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
            result = self._parse_response(response)
            
            # 内容完整性校验
            completeness_valid = self._validate_completeness(text, result['segments'])
            if not completeness_valid:
                logger.warning("内容完整性校验失败，尝试重新分析")
                
                # 如果完整性校验失败，尝试使用更详细的提示词重新分析
                detailed_prompt = self._build_detailed_analysis_prompt(text)
                retry_response = self._call_ollama(detailed_prompt)
                
                if retry_response:
                    retry_result = self._parse_response(retry_response)
                    retry_completeness = self._validate_completeness(text, retry_result['segments'])
                    
                    if retry_completeness:
                        result = retry_result
                        logger.info("重新分析成功，内容完整性校验通过")
            
            return result
        else:
            # Ollama调用失败，直接抛出错误
            logger.error("❌ Ollama API调用失败，没有返回有效响应")
            raise Exception("Ollama API调用失败，没有返回有效响应")

    async def _analyze_single_chunk(self, chunk_text: str, chunk_id: int, session_id: str = None) -> Dict:
        """分析单个分块"""
        logger.info(f"开始分析第{chunk_id}块，长度{len(chunk_text)}字符")
        
        try:
            prompt = self._build_analysis_prompt(chunk_text)
            response = self._call_ollama(prompt)
            
            if response:
                result = self._parse_response(response)
                logger.info(f"第{chunk_id}块分析完成：{len(result.get('segments', []))}段落，{len(result.get('characters', []))}个角色")
                return result
            else:
                logger.warning(f"第{chunk_id}块分析失败，返回空结果")
                return {"segments": [], "characters": []}
                
        except Exception as e:
            logger.error(f"第{chunk_id}块分析异常: {str(e)}")
            return {"segments": [], "characters": []}

    def _build_analysis_prompt(self, text: str) -> str:
        """构建分析模块专用的分析提示词"""
        prompt = f"""你是专业的中文小说文本分析专家。请完整分析以下文本，确保不遗漏任何内容。

**⚠️ 重要：必须处理所有文本内容，不能遗漏任何句子！**

核心任务：
1. 按句子分段，识别每段的说话者
2. 分离混合格式："角色说：'对话'" → 两段：动作(旁白) + "对话"(角色，保留引号)  
3. 引号内容=角色对话（保留引号），描述动作=旁白
4. 确保所有文本都在segments中体现，包括引号

**🔥 混合句子分离规则（重要）：**
- 当遇到"动作描述+说话动词+引号内容"的混合格式时，必须分离为两段
- 示例："接过玉佩轻声道：'多谢萧公子。'" → 分离为：
  * 第一段："接过玉佩轻声道：" → speaker: "旁白", text_type: "narration"
  * 第二段："多谢萧公子。" → speaker: "林薇", text_type: "dialogue"
- 说话动词包括：说、道、喊、叫、问、答、轻声道、喊道、叫道、轻声问道等

**🎯 说话者识别规则（重要）：**
- **直接对话**：有引号且明确说话者的内容 → speaker = 具体角色名，text_type = "dialogue"
- **心理活动**：描述角色内心想法、感受、思考的内容 → speaker = "旁白"，text_type = "inner_monologue"
- **动作描述**：描述角色行为、环境、场景的内容 → speaker = "旁白"，text_type = "narration"
- **环境描述**：描述场景、氛围、背景的内容 → speaker = "旁白"，text_type = "narration"

文本：
{text}

**完整性要求：**
- segments总字数应接近原文字数
- 每个句子都必须包含在某个segment中
- 不能跳过任何内容段落
- **每个segment的speaker字段必须有值！**

输出JSON格式：
{{
  "segments": [
    {{"order": 1, "text": "完整文本内容", "speaker": "说话者", "text_type": "dialogue/narration", "confidence": 0.9}}
  ],
  "characters": [
    {{"name": "角色名", "frequency": 出现次数, "gender": "male/female/neutral", "is_main_character": true/false, "confidence": 0.8}}
  ]
}}

只输出JSON，确保包含所有文本内容，且每个segment的speaker字段都有明确的值。"""
        
        return prompt

    def _build_detailed_analysis_prompt(self, text: str) -> str:
        """构建更详细的分析提示词，用于重试时确保完整性"""
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
                timeout=timeout
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

    def _parse_response(self, response: str) -> Dict:
        """解析Ollama返回的分析结果"""
        try:
            # 检查response是否为None或空
            if not response or response.strip() == '':
                logger.error("Ollama响应为空或None")
                return {
                    'segments': [],
                    'characters': []
                }
            
            # 记录原始响应用于调试
            logger.debug(f"Ollama响应: {len(response)}字符")
            
            # 提取JSON部分
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            
            if json_start != -1 and json_end != -1:
                json_str = response[json_start:json_end]
                data = json.loads(json_str)
                
                logger.debug(f"JSON解析成功: {len(data.get('segments', []))}个segments")
                
                # 处理segments
                segments = []
                for i, seg_data in enumerate(data.get('segments', [])):
                    # 支持新的text_type: inner_monologue
                    text_type = seg_data.get('text_type', 'narration')
                    if text_type not in ['dialogue', 'narration', 'inner_monologue']:
                        text_type = 'narration'  # 默认为旁白
                        
                    # 正确处理空的speaker字段
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
                        'voice_name': speaker,  # 确保voice_name与speaker一致
                        'confidence': seg_data.get('confidence', 0.8),
                        'detection_rule': 'analysis_ai',
                        'text_type': text_type
                    })
                
                # 合并相邻的旁白
                segments = self._merge_adjacent_narration(segments)
                
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
                
                # 调试：检查解析结果
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

    def _merge_adjacent_narration(self, segments: List[Dict]) -> List[Dict]:
        """合并相邻的旁白段落（包括心理活动）"""
        if not segments:
            return segments
        
        merged_segments = []
        current_narration = None
        
        for segment in segments:
            # 合并所有旁白类型的内容（narration和inner_monologue，且speaker为旁白）
            if (segment.get('speaker') == '旁白' and 
                segment.get('text_type') in ['narration', 'inner_monologue']):
                if current_narration is None:
                    # 开始新的旁白段落
                    current_narration = segment.copy()
                else:
                    # 合并到当前旁白段落
                    current_narration['text'] += segment['text']
                    # 更新置信度为平均值
                    current_narration['confidence'] = (current_narration['confidence'] + segment['confidence']) / 2
                    # 如果合并了不同类型的旁白，保持为narration类型
                    if current_narration['text_type'] != segment['text_type']:
                        current_narration['text_type'] = 'narration'
            else:
                # 如果不是旁白（对话等），先保存当前的旁白段落（如果有）
                if current_narration is not None:
                    merged_segments.append(current_narration)
                    current_narration = None
                # 添加当前段落
                merged_segments.append(segment)
        
        # 处理最后一个旁白段落
        if current_narration is not None:
            merged_segments.append(current_narration)
        
        # 重新编号
        for i, segment in enumerate(merged_segments):
            segment['order'] = i + 1
        
        logger.debug(f"旁白合并: {len(segments)}→{len(merged_segments)}个段落")
        return merged_segments

    def _validate_completeness(self, original_text: str, segments: List[Dict]) -> bool:
        """校验分析结果的完整性"""
        try:
            # 统计原文字数（去除空格和换行）
            original_chars = len(original_text.replace(' ', '').replace('\n', '').replace('\r', ''))
            
            # 简化调试信息
            logger.debug(f"🔍 完整性校验 - segments数量: {len(segments)}")
            if len(segments) == 0:
                logger.error(f"❌ segments为空列表！")
            
            # 统计segments字数（去除空格和换行）
            segment_chars = sum(len(seg.get('text', '').replace(' ', '').replace('\n', '').replace('\r', '')) for seg in segments)
            
            # 简化统计信息
            if segment_chars == 0 and len(segments) > 0:
                logger.warning(f"异常：有{len(segments)}个segments但总字数为0")
            
            # 计算完整度比例
            completeness_ratio = segment_chars / original_chars if original_chars > 0 else 0
            
            logger.info(f"✅ 分析模块对话分析完整性: {completeness_ratio:.1%} ({segment_chars}/{original_chars}字符)")
            
            # 根据快速模式调整完整性阈值
            if self.settings.get("fastModeEnabled", True):
                min_ratio = 0.75  # 快速模式：75%以上认为可接受
            else:
                min_ratio = 0.85  # 标准模式：85%以上认为完整
            
            if completeness_ratio < min_ratio:
                logger.warning(f"内容完整性校验失败: 完整度仅{completeness_ratio:.2%}，阈值{min_ratio:.0%}")
                return False
            
            logger.info("内容完整性校验通过")
            return True
            
        except Exception as e:
            logger.error(f"完整性校验异常: {str(e)}")
            return False  # 校验异常时认为不完整，触发重试

    def _infer_gender_smart(self, name: str, ai_gender: str) -> str:
        """智能推断角色性别 - 完全依赖AI判断"""
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
