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
        
        # 1. 提取旁白段落
        narration_segments = self._extract_narration_segments(synthesis_plan)
        if not narration_segments:
            return self._empty_result()
        
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
        """构建LLM分析提示词"""
        prompt_parts = [
            "请分析以下小说段落中的环境声音，严格按照以下规则：",
            "",
            "🎯 核心规则：只提取文本中明确包含声音词汇的内容",
            "",
            "✅ 正确示例：",
            "- 文本：'空调发出轻微嗡鸣' → 输出：['嗡鸣']",
            "- 文本：'叮 ——' → 输出：['叮']", 
            "- 文本：'耳畔响起尖锐的蜂鸣' → 输出：['蜂鸣']",
            "- 文本：'远处传来马蹄声' → 输出：['马蹄声']",
            "",
            "❌ 错误示例：",
            "- 文本：'快步穿过走廊' → 错误：['脚步声']（文本没有'脚步声'）",
            "- 文本：'何人在此？' → 错误：['说话声']（文本没有'说话声'）",
            "- 文本：'走路' → 错误：['脚步声']（文本没有'脚步声'）",
            "",
            "⚠️ 严格禁止：",
            "1. 禁止联想：看到动作不要联想声音",
            "2. 禁止推理：看到对话不要推理'说话声'",
            "3. 禁止扩展：只提取原文中的声音词汇",
            "4. 没有明确声音词汇的段落返回[]",
            "",
            "段落内容："
        ]
        
        for i, seg in enumerate(narration_segments):
            prompt_parts.append(f"段落{i+1}: {seg['text']}")
        
        prompt_parts.extend([
            "",
            "请按段落顺序返回结果，严格按照上述规则：",
            "段落1: [关键词1, 关键词2]",
            "段落2: []",
            "段落3: [关键词1]",
            "...",
            "",
            "记住：只提取原文中明确的声音词汇，不要联想！"
        ])
        
        return "\n".join(prompt_parts)
    
    def _generate_tracks(self, llm_result, narration_segments: List[Dict]) -> List[Dict]:
        """生成环境音轨道"""
        tracks = []
        
        # 简单的一对一映射
        for i, segment in enumerate(narration_segments):
            if i < len(llm_result.analyzed_scenes):
                scene = llm_result.analyzed_scenes[i]
                keywords = self._clean_keywords(scene.keywords)
                
                if keywords:
                    tracks.append({
                        'segment_id': segment['segment_id'],
                        'start_time': segment['start_time'],
                        'duration': segment['duration'],
                        'narration_text': segment['text'],
                        'environment_keywords': keywords,
                        'confidence': scene.confidence,
                        'analysis_timestamp': datetime.now().isoformat()
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
            if self._is_sound_keyword(kw) and 2 <= len(kw) <= 8:
                cleaned.append(kw)
        
        return list(set(cleaned))[:3]  # 去重，最多3个
    
    def _is_sound_keyword(self, keyword: str) -> bool:
        """判断是否为声音关键词"""
        sound_indicators = ['声', '音', '响', '鸣', '叫', '吼', '啸', '嗡', '叮', '咚', '啪', '砰']
        return any(indicator in keyword for indicator in sound_indicators)
    
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
        """解析LLM响应"""
        import json
        import re
        
        scenes = []
        lines = response_text.strip().split('\n')
        segment_pattern = r'段落(\d+):\s*(\[.*?\])'
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            match = re.search(segment_pattern, line)
            if match:
                segment_num = int(match.group(1))
                keywords_str = match.group(2)
                
                try:
                    # 解析JSON数组
                    keywords = json.loads(keywords_str)
                    if isinstance(keywords, list):
                        # 清理关键词
                        clean_keywords = [kw.strip() for kw in keywords if kw.strip()]
                        
                        from app.services.llm_scene_analyzer import SceneAnalysis
                        scenes.append(SceneAnalysis(
                            location="detected_environment",
                            keywords=clean_keywords[:3],  # 最多3个
                            confidence=0.9 if clean_keywords else 0.8
                        ))
                        logger.info(f"[ENV_ANALYZER] 段落{segment_num}: {clean_keywords}")
                    else:
                        logger.warning(f"[ENV_ANALYZER] 段落{segment_num}不是数组: {keywords_str}")
                except json.JSONDecodeError as e:
                    logger.warning(f"[ENV_ANALYZER] 段落{segment_num}JSON解析失败: {keywords_str}, 错误: {e}")
                    # 尝试手动解析
                    try:
                        # 移除可能的引号和方括号
                        clean_str = keywords_str.strip().strip('[]').strip("'").strip('"')
                        if clean_str:
                            keywords = [kw.strip().strip("'").strip('"') for kw in clean_str.split(',') if kw.strip()]
                            clean_keywords = [kw for kw in keywords if kw]
                            
                            from app.services.llm_scene_analyzer import SceneAnalysis
                            scenes.append(SceneAnalysis(
                                location="detected_environment",
                                keywords=clean_keywords[:3],  # 最多3个
                                confidence=0.9 if clean_keywords else 0.8
                            ))
                            logger.info(f"[ENV_ANALYZER] 段落{segment_num}手动解析成功: {clean_keywords}")
                    except Exception as e2:
                        logger.warning(f"[ENV_ANALYZER] 段落{segment_num}手动解析也失败: {e2}")
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
