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
    """基于Ollama的角色检测器"""
    
    def __init__(self, model_name: str = "qwen2.5:14b", ollama_url: str = None):
        self.model_name = model_name
        self.api_url = ollama_url or "http://localhost:11434/api/generate"
        self.logger = logging.getLogger(__name__)

    async def analyze_text(self, text: str, chapter_info: dict) -> dict:
        """使用Ollama分析文本中的角色 - 直接AI分析，简单高效"""
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
            
            # 1. 直接调用Ollama进行全文分析（包括角色识别和文本分段）
            await send_analysis_progress(session_id, 30, "正在调用AI模型进行角色识别...")
            
            # 🔥 修复：增加重试机制，最多重试3次
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
                            await send_analysis_progress(session_id, 30 + attempt * 10, f"重试中... ({attempt + 1}/{max_retries})")
                            time.sleep(2)  # 等待2秒后重试
                        
                except Exception as e:
                    logger.error(f"第{attempt + 1}次尝试异常: {str(e)}")
                    if attempt < max_retries - 1:
                        await send_analysis_progress(session_id, 30 + attempt * 10, f"重试中... ({attempt + 1}/{max_retries})")
                        time.sleep(2)  # 等待2秒后重试
                    else:
                        raise e
            
            processing_time = time.time() - start_time
            
            if response:
                await send_analysis_progress(session_id, 80, "正在解析AI分析结果...")
                
                # 解析Ollama返回的完整结果
                result = self._parse_comprehensive_response(response)
                
                # 🔥 修复：增加内容完整性校验
                completeness_valid = self._validate_completeness(text, result['segments'])
                if not completeness_valid:
                    logger.warning("内容完整性校验失败，尝试重新分析")
                    await send_analysis_progress(session_id, 85, "内容完整性校验失败，重新分析中...")
                    
                    # 如果完整性校验失败，尝试使用更详细的提示词重新分析
                    detailed_prompt = self._build_detailed_analysis_prompt(text)
                    retry_response = self._call_ollama(detailed_prompt)
                    
                    if retry_response:
                        retry_result = self._parse_comprehensive_response(retry_response)
                        retry_completeness = self._validate_completeness(text, retry_result['segments'])
                        
                        if retry_completeness:
                            result = retry_result
                            logger.info("重新分析成功，内容完整性校验通过")
                            await send_analysis_progress(session_id, 95, "重新分析成功")
                        else:
                            logger.warning("重新分析仍未通过完整性校验，使用原结果并记录警告")
                            await send_analysis_progress(session_id, 95, "分析完成，但存在内容完整性警告")
                
                await send_analysis_progress(session_id, 100, f"分析完成，识别到{len(result['characters'])}个角色")
                
                # 智能分析阶段：返回所有识别到的角色（不过滤已存在的）
                all_characters = result['characters']
                
                return {
                    "chapter_id": chapter_info['chapter_id'],
                    "chapter_title": chapter_info['chapter_title'],
                    "chapter_number": chapter_info['chapter_number'],
                    "detected_characters": all_characters,  # 返回所有角色
                    "segments": result['segments'],
                    "processing_stats": {
                        "total_segments": len(result['segments']),
                        "dialogue_segments": len([s for s in result['segments'] if s['text_type'] == 'dialogue']),
                        "narration_segments": len([s for s in result['segments'] if s['text_type'] == 'narration']),
                        "characters_found": len(result['characters']),
                        "new_characters_found": len(result['characters']),
                        "analysis_method": "ollama_ai_primary",
                        "processing_time": round(processing_time, 2),
                        "text_length": len(text),
                        "ai_model": self.model_name,
                        "completeness_validated": completeness_valid,  # 🔥 新增：完整性校验结果
                        "retry_count": max_retries - (3 if response else 0)  # 🔥 新增：重试次数记录
                    }
                }
            else:
                # Ollama调用失败，直接抛出错误
                logger.error("❌ Ollama API调用失败，没有返回有效响应")
                await send_analysis_progress(session_id, 0, "AI分析失败")
                raise Exception("Ollama API调用失败，没有返回有效响应")
                
        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"❌ Ollama角色分析异常失败: {str(e)}")
            await send_analysis_progress(session_id, 0, f"AI分析失败: {str(e)}")
            raise Exception(f"Ollama角色分析失败: {str(e)}")
    
    def _validate_completeness(self, original_text: str, segments: List[Dict]) -> bool:
        """🔥 新增：校验分析结果的完整性"""
        try:
            # 统计原文字数（去除空格和换行）
            original_chars = len(original_text.replace(' ', '').replace('\n', '').replace('\r', ''))
            
            # 统计segments字数（去除空格和换行）
            segment_chars = sum(len(seg.get('text', '').replace(' ', '').replace('\n', '').replace('\r', '')) for seg in segments)
            
            # 计算完整度比例
            completeness_ratio = segment_chars / original_chars if original_chars > 0 else 0
            
            logger.info(f"内容完整性校验: 原文{original_chars}字符，分析结果{segment_chars}字符，完整度{completeness_ratio:.2%}")
            
            # 如果差异超过15%，认为不完整
            if completeness_ratio < 0.85:
                logger.warning(f"内容完整性校验失败: 完整度仅{completeness_ratio:.2%}，可能有内容丢失")
                return False
            
            # 检查是否有明显的文本遗漏（通过关键词检查）
            original_keywords = self._extract_keywords(original_text)
            segment_text = ' '.join([seg.get('text', '') for seg in segments])
            segment_keywords = self._extract_keywords(segment_text)
            
            missing_keywords = original_keywords - segment_keywords
            if len(missing_keywords) > len(original_keywords) * 0.2:  # 如果超过20%的关键词丢失
                logger.warning(f"关键词完整性校验失败: 丢失关键词{missing_keywords}")
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
        """🆕 基于小说类型构建专门的分析提示词"""
        
        # 基础分析要求
        base_requirements = """
分析要求：
1. 识别所有说话的角色（包括旁白）
2. 将文本按句子分段，每段标记正确的说话者
3. **🚨 绝对强制要求**：必须严格分离所有混合文本

🚨 **强制分离规则（必须执行）**：
❗ 任何包含"角色名 + 动作 + 冒号 + 引号内容"的文本都必须分为两段：
- "项羽冷笑一声："你又是何人？"" → 必须分为：
  第一段："项羽冷笑一声：" → 说话者：旁白
  第二段："你又是何人？" → 说话者：项羽

❗ 任何包含"引号内容 + 角色动作描述"的文本都必须分为两段：
- ""何人在此？" 将领勒马，长枪直指他咽喉。" → 必须分为：
  第一段："何人在此？" → 说话者：将领
  第二段："将领勒马，长枪直指他咽喉。" → 说话者：旁白

❗ 任何通讯、消息、传话类文本都必须分离：
- "是导师发来的消息："新出土的未央宫残简，速来。"" → 必须分为：
  第一段："是导师发来的消息：" → 说话者：旁白
  第二段："新出土的未央宫残简，速来。" → 说话者：导师

🎯 **分离判断标准**：
- 描述性文字（动作、场景、来源说明）= 旁白
- 引号内的实际话语内容 = 对应角色发言
- 绝不允许将混合内容归为单一说话者！"""

        # 根据小说类型添加专门的规则
        type_specific_rules = ""
        
        if novel_type == 'ancient':
            type_specific_rules = """
**🏛️ 古代小说专门规则**：
- 间接引述：皇帝下旨、传旨、圣旨、诏书、密信等
  示例："皇帝下旨：'即刻班师回朝。'" → 分离为旁白描述 + 皇帝话语
- 古代称谓：陛下、皇上、公主、王爷、大人、臣等要准确识别
- 文言文对话：注意"曰"、"云"、"道"等古代对话动词
- 书信传话：信中写道、密报、传令等要分离动作和内容"""
            
        elif novel_type == 'modern':
            type_specific_rules = """
**🏙️ 现代小说专门规则**：
- 现代通讯分离（重点）：
  * "导师发来的消息：'内容'" → 两段：
    第一段："导师发来的消息：" → 旁白（描述收到消息）
    第二段："内容" → 导师（消息内容）
  * "他看了一眼屏幕，是导师发来的消息：'内容'" → 三段：
    第一段："他看了一眼屏幕，" → 旁白（动作描述）
    第二段："是导师发来的消息：" → 旁白（消息来源描述）
    第三段："内容" → 导师（消息内容）
  * "老板在电话里说：'开会了。'" → 两段：
    第一段："老板在电话里说：" → 旁白（通话描述）
    第二段："开会了。" → 老板（电话内容）

- 现代通讯关键词：手机、短信、电话、微信、QQ、邮件、消息、语音
- 职场称谓：老板、经理、同事、导师、老师、领导
- 必须严格分离描述性文字和实际通讯内容！"""
            
        elif novel_type == 'wuxia':
            type_specific_rules = """
**⚔️ 武侠小说专门规则**：
- 江湖称谓：掌门、师父、师兄、弟子、侠客等
- 传音入密：内力传音、神识传话等特殊对话方式
- 门派规则：师门规矩、江湖规矩相关的对话
- 武功招式：注意区分招式名称（旁白）和实际对话"""
            
        elif novel_type == 'fantasy':
            type_specific_rules = """
**🔮 玄幻小说专门规则**：
- 魔法通讯：法术传音、魔法通话、精神链接等
- 异世界称谓：法师、战士、魔导师、国王、贵族等
- 魔法元素：咒语吟唱、法术释放要区分于对话
- 种族对话：精灵、矮人、龙族等不同种族的对话特点

**🌟 现代穿越文特殊处理**：
如果文本包含现代元素（手机、博物馆、导师等），同时应用现代通讯分离规则：
- "导师发来的消息：'内容'" → 分离为旁白描述 + 导师话语
- "手机震动"、"收到短信"等现代通讯场景要正确分离
- 现代称谓（导师、老师、同事）要正确识别"""
            
        elif novel_type == 'scifi':
            type_specific_rules = """
**🚀 科幻小说专门规则**：
- 科技通讯：全息通话、量子通讯、脑波传输等
- 未来称谓：指挥官、舰长、博士、实验员等
- AI对话：人工智能、机器人的对话要正确识别
- 科技术语：区分科技描述（旁白）和实际对话"""
            
        elif novel_type == 'military':
            type_specific_rules = """
**🎖️ 军事小说专门规则**：
- 军事通讯：无线电、作战指令、军令传达等
- 军事称谓：将军、指挥官、士兵、参谋等
- 作战指令：命令下达、战报汇报要分离动作和内容
- 军事术语：区分战术描述（旁白）和实际对话"""
        else:
            type_specific_rules = """
**🔍 通用规则**：
- 间接引述：任何"某某[动作]：'内容'"格式都要分离
- 现代通讯：电话、短信、邮件等要分离描述和内容
- 传统对话：注意各种对话引导词的正确分离"""

        prompt = f"""你是一个专业的中文小说文本分析专家。当前分析的是**{novel_type}类型小说**，请针对性地分析以下文本。

文本：
{text[:4000] if len(text) > 4000 else text}

{base_requirements}

{type_specific_rules}

**🎵 声音描述特殊规则（通用）**：
- 所有描述声音、语调、音色的文字都是旁白，不是对话
- 关键词识别：凡是包含"声"、"音"、"响"、"传来"、"响起"等描述声音的词汇，都是旁白叙述

**🧠 心理描写特殊规则（通用）**：
- "他心里想"、"她暗自琢磨"后的引号内容是该角色的心理活动
- 心理描写关键词：心里想、心想、暗想、暗道、心道、琢磨、思考、想到等

**🎯 角色名称一致性要求（核心）**：
- 同一角色必须使用统一的名称，避免多种称呼
- 优先使用具体人名，避免泛指称呼

输出格式（严格JSON）：
{{
  "novel_type": "{novel_type}",
  "segments": [
    {{"order": 1, "text": "文本内容", "speaker": "说话者", "text_type": "dialogue/narration/inner_monologue", "confidence": 0.9}}
  ],
  "characters": [
    {{"name": "角色名", "frequency": 出现次数, "gender": "male/female/neutral", "personality": "calm/brave/gentle", "personality_description": "性格描述", "is_main_character": true/false, "confidence": 0.8}}
  ]
}}

只输出JSON，不要任何其他文字"""
        
        return prompt

    def _build_comprehensive_analysis_prompt(self, text: str) -> str:
        """构建综合分析提示词 - 现在支持类型感知"""
        # 🆕 第一步：检测小说类型
        novel_type = self._detect_novel_type(text)
        
        # 🆕 第二步：基于类型构建专门提示词
        return self._build_type_aware_analysis_prompt(text, novel_type)

    def _call_ollama(self, prompt: str) -> Optional[str]:
        """调用Ollama API"""
        try:
            payload = {
                "model": self.model_name,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.2,
                    "top_p": 0.8,
                    "max_tokens": 8000,    # 🔥 修复：增加到8000，避免输出截断
                    "num_ctx": 8192        # 🔥 修复：增加到8192，支持更长的上下文
                }
            }
            
            response = requests.post(
                self.api_url,
                json=payload,
                timeout=300  # 🔥 修复：增加超时时间到5分钟，避免长文本分析超时
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
                    speaker = seg_data.get('speaker', '').strip()
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
                
                return {
                    'segments': segments,
                    'characters': characters
                }
            
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