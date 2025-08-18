"""
环境音分析器
核心逻辑：从synthesis_plan提取旁白 → LLM分析 → 生成环境音轨道
"""

import logging
import re
from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

class NarrationEnvironmentAnalyzer:
    """环境音分析器 - 简化版，只保留核心逻辑"""
    
    def __init__(self, db: Optional[Session] = None):
        # LLM分析器
        from app.services.llm_scene_analyzer import OllamaLLMSceneAnalyzer
        self.scene_analyzer = OllamaLLMSceneAnalyzer()
        self.db = db
        
    async def extract_and_analyze_narration(self, synthesis_plan: List[Dict]) -> Dict:
        """主入口：分析环境音"""
        logger.info(f"[ENV_ANALYZER] 开始分析，共{len(synthesis_plan)}个段落")
        
        # 检查合成计划是否为空
        if not synthesis_plan:
            error_msg = "合成计划为空！请先完成书籍的智能准备，确保章节有完整的合成计划数据。"
            logger.error(f"[ENV_ANALYZER] {error_msg}")
            return {
                'environment_tracks': [],
                'analysis_summary': {
                    'total_duration': 0.0,
                    'narration_segments': 0,
                    'environment_tracks_detected': 0,
                    'analysis_timestamp': datetime.now().isoformat(),
                    'error': error_msg
                }
            }
        
        # 1. 提取旁白段落
        narration_segments = self._extract_narration_segments(synthesis_plan)
        if not narration_segments:
            error_msg = "未找到旁白段落！请检查合成计划中是否包含旁白内容，或重新进行智能准备。"
            logger.warning(f"[ENV_ANALYZER] {error_msg}")
            return {
                'environment_tracks': [],
                'analysis_summary': {
                    'total_duration': 0.0,
                    'narration_segments': 0,
                    'environment_tracks_detected': 0,
                    'analysis_timestamp': datetime.now().isoformat(),
                    'warning': error_msg
                }
            }
        
        # 2. 构建LLM提示词
        prompt = self._build_analysis_prompt(narration_segments)
        
        # 3. LLM分析 - 直接调用，避免批量分析检测
        try:
            # 直接调用LLM，不使用批量分析检测
            llm_result = await self._call_llm_directly(prompt)
            if not llm_result.analyzed_scenes:
                return self._empty_result()
        except Exception as e:
            logger.error(f"[ENV_ANALYZER] LLM分析失败: {e}")
            return self._empty_result()
        
        # 4. 生成环境音轨道
        environment_tracks = self._generate_tracks(llm_result, narration_segments)
        
        return {
            'environment_tracks': environment_tracks,
            'analysis_summary': {
                'total_duration': sum(seg['duration'] for seg in narration_segments),
                'narration_segments': len(narration_segments),
                'environment_tracks_detected': len(environment_tracks),
                'analysis_timestamp': datetime.now().isoformat()
            }
        }
    
    def _extract_narration_segments(self, synthesis_plan: List[Dict]) -> List[Dict]:
        """提取旁白段落"""
        narration_segments = []
        current_time = 0.0
        
        for segment in synthesis_plan:
            # 识别旁白
            if self._is_narration(segment):
                text = segment.get('text', '') or segment.get('content', '')
                duration = self._calculate_duration(text)
                
                narration_segments.append({
                    'segment_id': segment.get('segment_id', f'seg_{len(narration_segments) + 1}'),
                    'text': text,
                    'start_time': current_time,
                    'duration': duration
                })
            
            current_time += self._calculate_duration(segment.get('text', '') or segment.get('content', ''))
        
        return narration_segments
    
    def _is_narration(self, segment: Dict) -> bool:
        """判断是否为旁白段落"""
        narration_speakers = ['旁白', 'narrator', '叙述者', 'narration']
        speaker = segment.get('speaker') or segment.get('character', '')
        return speaker in narration_speakers
    
    def _calculate_duration(self, text: str) -> float:
        """计算文本时长"""
        if not text:
            return 1.0
        char_count = len(text.replace(' ', '').replace('\n', ''))
        return max(1.0, char_count / 5.0)  # 5字符/秒
    
    def _build_analysis_prompt(self, narration_segments: List[Dict]) -> str:
        """构建智能分析提示词 - 同时生成关键词和中文/英文提示词"""
        prompt_parts = [
            "请分析以下小说段落中的环境声音，并生成中文描述和英文合成提示词。",
            "",
            "🎯 分析要求：",
            "1. 提取环境声音关键词（中文）",
            "2. 生成详细的中文场景描述（用于前端展示）",
            "3. 生成详细的英文提示词（用于声音生成）",
            "4. 考虑场景、强度、音色等细节",
            "",
            "📝 输出格式（JSON）：",
            "段落1: {",
            '  "keywords": ["关键词1", "关键词2"],',
            '  "prompts": [',
            '    {',
            '      "keyword": "关键词1",',
            '      "chinese_description": "详细的中文场景描述，包含环境、氛围、声音特征",',
            '      "english_prompt": "详细的英文提示词，包含场景、强度、音色描述",',
            '      "duration_type": "instant|continuous"',
            '    }',
            '  ]',
            "}",
            "",
            "✅ 正确示例：",
            "段落: '空调发出轻微嗡鸣，营造出宁静的氛围'",
            "输出: {",
            '  "keywords": ["嗡鸣"],',
            '  "prompts": [',
            '    {',
            '      "keyword": "嗡鸣",',
            '      "chinese_description": "博物馆内空调系统发出的轻微嗡鸣声，营造出宁静祥和的氛围，背景机械声轻柔持续",',
            '      "english_prompt": "Air conditioning humming softly in a quiet museum, gentle mechanical background noise, subtle ambient sound creating peaceful atmosphere",',
            '      "duration_type": "continuous"',
            '    }',
            '  ]',
            "}",
            "",
            "段落: '叮 ——'",
            "输出: {",
            '  "keywords": ["叮"],',
            '  "prompts": [',
            '    {',
            '      "keyword": "叮",',
            '      "chinese_description": "清脆的铃声响起，可能是手机通知或系统提示音，声音短暂而清晰",',
            '      "english_prompt": "Light bell ringing sound, gentle notification tone, clear metallic chime",',
            '      "duration_type": "instant"',
            '    }',
            '  ]',
            "}",
            "",
            "⚠️ 严格规则：",
            "1. 只提取原文中明确的声音词汇",
            "2. 中文描述要详细、生动、易于理解",
            "3. 英文提示词要详细、准确、地道",
            "4. 包含场景背景、声音特征、强度描述",
            "5. 没有声音的段落返回空数组",
            "",
            "段落内容："
        ]
        
        for i, seg in enumerate(narration_segments):
            prompt_parts.append(f"段落{i+1}: {seg['text']}")
        
        prompt_parts.extend([
            "",
            "请按段落顺序返回JSON格式结果：",
            "段落1: {JSON对象}",
            "段落2: {JSON对象}",
            "...",
            "",
            "记住：中文关键词 + 英文提示词，确保准确性！"
        ])
        
        return "\n".join(prompt_parts)
    
    def _generate_tracks(self, llm_result, narration_segments: List[Dict]) -> List[Dict]:
        """生成环境音轨道（包含英文提示词）"""
        tracks = []

        for i, segment in enumerate(narration_segments):
            if i >= len(llm_result.analyzed_scenes):
                continue
                
            scene = llm_result.analyzed_scenes[i]
            keywords = self._clean_keywords(scene.keywords)
            
            # 为所有段落生成轨道，即使没有环境音
            if not keywords:
                # 没有环境音的段落，生成空轨道用于前端显示
                tracks.append({
                        'segment_id': segment['segment_id'],
                        'start_time': segment['start_time'],
                        'duration': segment['duration'],
                        'narration_text': segment['text'],
                    'environment_keywords': [],
                    'english_prompt': '',
                    'chinese_description': '',
                    'duration_type': 'none',
                        'confidence': scene.confidence,
                        'analysis_timestamp': datetime.now().isoformat(),
                    'has_environment': False
                })
                continue
                
            # 获取提示词信息
            prompts_data = getattr(scene, 'metadata', {}).get('prompts', [])
            
            # 规划该段落内每个关键词的时长与起止时间
            planned = self._plan_keyword_timing(
                keywords=keywords[:3],
                segment_start=segment['start_time'],
                segment_duration=segment['duration']
            )

            for plan in planned:
                # 查找对应的英文提示词
                english_prompt = None
                chinese_description = None
                duration_type = 'continuous'
                
                for prompt_info in prompts_data:
                    if prompt_info.get('keyword') == plan['keyword']:
                        english_prompt = prompt_info.get('english_prompt')
                        chinese_description = prompt_info.get('chinese_description')
                        duration_type = prompt_info.get('duration_type', 'continuous')
                        break
                
                # 如果没有找到英文提示词或中文描述，说明LLM分析有问题
                if not english_prompt or not chinese_description:
                    logger.error(f"[ENV_ANALYZER] LLM分析结果不完整: keyword={plan['keyword']}, english_prompt={english_prompt}, chinese_description={chinese_description}")
                    continue
                        
                tracks.append({
                    'segment_id': segment['segment_id'],
                    'start_time': plan['start_time'],
                    'duration': plan['duration'],
                    'narration_text': segment['text'],
                    'environment_keywords': [plan['keyword']],
                    'english_prompt': english_prompt,
                    'chinese_description': chinese_description,
                    'duration_type': duration_type,
                    'confidence': scene.confidence,
                        'analysis_timestamp': datetime.now().isoformat(),
                    'has_environment': True
                })

        return tracks
    

    
    def _clean_keywords(self, keywords: List[str]) -> List[str]:
        """清理关键词"""
        if not keywords:
            return []
        
        cleaned = []
        for kw in keywords:
            if not kw or not isinstance(kw, str):
                continue
            
            # 基本清理
            kw = kw.strip()
            kw = re.sub(r'\d+\.?\d*s', '', kw)  # 移除时间
            kw = re.sub(r'[高中低]强度', '', kw)  # 移除强度
            kw = kw.strip()
            
            # 检查是否为声音词汇
            if self._is_sound_keyword(kw) and 1 <= len(kw) <= 8:
                cleaned.append(kw)
        
        return list(set(cleaned))[:3]  # 去重，最多3个
    
    def _is_sound_keyword(self, keyword: str) -> bool:
        """判断是否为声音关键词"""
        sound_indicators = ['声', '音', '响', '鸣', '叫', '吼', '啸', '嗡', '叮', '咚', '啪', '砰']
        # 特殊处理一些常见的声音词汇
        special_sounds = ['叮', '震动', '玉佩发烫', '马蹄', '蜂鸣', '白光']
        
        # 检查是否包含声音指示符
        has_sound_indicator = any(indicator in keyword for indicator in sound_indicators)
        
        # 检查是否是特殊声音词汇
        is_special_sound = any(sound in keyword for sound in special_sounds)
        
        return has_sound_indicator or is_special_sound

    def _classify_sound(self, keyword: str) -> str:
        """将声音分类为瞬时或持续（尽量通用，少依赖硬编码）。"""
        k = keyword.strip()
        instant_indicators = ['叮', '砰', '啪', '咚', '响', '敲', '铃', '破碎', '爆炸', '蜂鸣']
        continuous_indicators = ['嗡', '空调', '雨', '风', '雷', '水', '流', '人群', '音乐', '脚步', '马蹄']

        is_instant = any(tok in k for tok in instant_indicators)
        is_cont = any(tok in k for tok in continuous_indicators) or ('声' in k and not is_instant)

        if is_instant and not is_cont:
            return 'instant'
        if is_cont and not is_instant:
            return 'continuous'
        # 模糊情况：优先将纯拟声词视为瞬间，否则视为持续
        if len(k) <= 2:
            return 'instant'
        return 'continuous'

    def _plan_keyword_timing(self, keywords: List[str], segment_start: float, segment_duration: float) -> List[Dict[str, Any]]:
        """为一个段落内的多个关键词规划时长与开始时间。

        规则：
        - 瞬时声：每个约0.8~1.5s，均匀分布在段落的30%~80%区间
        - 持续声：不铺满整段，默认占段落的60%（背景如空调可到80%）；多条持续声平均切分
        - 混合：先放持续声（覆盖段落前半/前中段），再穿插瞬时声
        """
        if segment_duration <= 0:
            return []

        plans: List[Dict[str, Any]] = []
        instant_kws: List[str] = []
        cont_kws: List[str] = []

        for kw in keywords:
            cls = self._classify_sound(kw)
            (instant_kws if cls == 'instant' else cont_kws).append(kw)

        # 限制数量，避免过多音轨
        instant_kws = instant_kws[:3]
        cont_kws = cont_kws[:2]

        # 持续声规划
        if cont_kws:
            # 背景类（含 嗡/空调/雨/风/水/人群/音乐）比例更高
            bg_tokens = ['嗡', '空调', '雨', '风', '水', '人群', '音乐']
            has_bg = any(any(tok in kw for tok in bg_tokens) for kw in cont_kws)
            cover_ratio = 0.8 if has_bg and not instant_kws else 0.6
            total_continuous = max(2.0, min(segment_duration * cover_ratio, max(3.0, segment_duration * 0.9)))

            slice_len = max(1.5, total_continuous / len(cont_kws))
            current = segment_start
            for idx, kw in enumerate(cont_kws):
                start = current
                dur = min(slice_len, segment_start + segment_duration - start)
                if dur > 0.2:
                    plans.append({'keyword': kw, 'start_time': round(start, 2), 'duration': round(dur, 2)})
                current = start + dur

        # 瞬时声规划（分布在30%~80%区间）
        if instant_kws:
            n = len(instant_kws)
            base = max(0.8, min(1.5, segment_duration * 0.25))
            for idx, kw in enumerate(instant_kws):
                pos_ratio = 0.3 + (0.5 * (idx + 1) / (n + 1))
                start = segment_start + segment_duration * pos_ratio
                end = segment_start + segment_duration
                dur = min(base, max(0.6, end - start))
                plans.append({'keyword': kw, 'start_time': round(start, 2), 'duration': round(dur, 2)})

        # 边界保护：不超过段落范围
        bounded = []
        seg_end = segment_start + segment_duration
        for p in plans:
            s = max(segment_start, min(p['start_time'], seg_end))
            e = max(s, min(s + p['duration'], seg_end))
            d = max(0.2, e - s)
            bounded.append({'keyword': p['keyword'], 'start_time': round(s, 2), 'duration': round(d, 2)})

        return bounded
    
    async def _call_llm_directly(self, prompt: str):
        """直接调用LLM，避免批量分析检测"""
        import aiohttp
        import time
        
        start_time = time.time()
        
        payload = {
            "model": self.scene_analyzer.model_name,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
            "options": {
                "temperature": 0.1,
                "top_p": 0.9,
                "num_predict": 2000,
            }
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.scene_analyzer.ollama_base_url}/api/chat",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=60)
            ) as response:
                
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"[ENV_ANALYZER] Ollama请求失败 {response.status}: {error_text}")
                    return self._create_empty_llm_result(f"HTTP错误: {response.status}")
                
                data = await response.json()
                analysis_time = time.time() - start_time
                
                if not data or 'message' not in data:
                    logger.error("[ENV_ANALYZER] LLM响应格式错误")
                    return self._create_empty_llm_result("响应格式错误")
                
                response_text = data['message']['content'].strip()
                logger.info(f"[ENV_ANALYZER] LLM分析完成，耗时: {analysis_time:.2f}s")
                logger.info(f"[ENV_ANALYZER] LLM响应: {response_text[:200]}...")
                
                # 解析响应
                scenes = self._parse_llm_response(response_text)
                confidence = 0.9 if scenes else 0.0
                
                from app.services.llm_scene_analyzer import SceneAnalysisResult
                return SceneAnalysisResult(
                    analyzed_scenes=scenes,
                    confidence_score=confidence,
                    processing_time=analysis_time,
                    raw_response=response_text
                )
    
    def _parse_llm_response(self, response_text: str):
        """解析智能LLM响应 - JSON格式"""
        import json
        import re
        
        scenes = []
        
        # 先尝试提取所有JSON对象
        json_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
        json_matches = re.finditer(json_pattern, response_text, re.DOTALL)
        
        segment_num = 1
        for json_match in json_matches:
            json_str = json_match.group(0)
            
            try:
                # 解析JSON对象
                data = json.loads(json_str)
                
                if isinstance(data, dict) and 'keywords' in data and 'prompts' in data:
                    keywords = data['keywords']
                    prompts = data['prompts']
                    
                    # 清理关键词
                    clean_keywords = [kw.strip() for kw in keywords if kw.strip()]
                    
                    # 为每个段落都创建场景，即使关键词为空
                    from app.services.llm_scene_analyzer import SceneAnalysis
                    scenes.append(SceneAnalysis(
                        location="detected_environment",
                        keywords=clean_keywords[:3],  # 最多3个
                        confidence=0.9 if clean_keywords else 0.8,
                        # 添加自定义字段存储提示词信息
                        metadata={
                            'prompts': prompts,
                            'segment_num': segment_num
                        }
                    ))
                    
                    if clean_keywords:
                        logger.info(f"[ENV_ANALYZER] 段落{segment_num}: {clean_keywords}")
                        logger.info(f"[ENV_ANALYZER] 段落{segment_num}提示词: {prompts}")
                    else:
                        logger.info(f"[ENV_ANALYZER] 段落{segment_num}: 无声音关键词")
                    
                    segment_num += 1
                else:
                    logger.warning(f"[ENV_ANALYZER] JSON格式错误: {json_str}")
                    
            except json.JSONDecodeError as e:
                logger.warning(f"[ENV_ANALYZER] JSON解析失败: {json_str}, 错误: {e}")
                continue
        
        return scenes
    
    def _create_empty_llm_result(self, error_msg: str):
        """创建空的LLM结果"""
        from app.services.llm_scene_analyzer import SceneAnalysisResult
        return SceneAnalysisResult(
            analyzed_scenes=[],
            confidence_score=0.0,
            processing_time=0.0,
            raw_response=error_msg
        )
    
    def _empty_result(self) -> Dict:
        """返回空结果"""
        return {
            'environment_tracks': [],
            'analysis_summary': {
                'total_duration': 0.0,
                'narration_segments': 0,
                'environment_tracks_detected': 0,
                'analysis_timestamp': datetime.now().isoformat()
            }
        }
    
    # 保持向后兼容的方法
    async def extract_and_analyze_narration_batch(self, synthesis_plan: List[Dict]) -> Dict:
        """批量分析版本（向后兼容）"""
        return await self.extract_and_analyze_narration(synthesis_plan)
    
    async def extract_and_analyze_narration_individual(self, synthesis_plan: List[Dict]) -> Dict:
        """逐一分析版本（向后兼容）"""
        return await self.extract_and_analyze_narration(synthesis_plan)
