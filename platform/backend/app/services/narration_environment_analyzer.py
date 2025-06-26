"""
旁白环境分析器
从synthesis_plan提取旁白内容并分析环境关键词与时长
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class NarrationEnvironmentAnalyzer:
    """旁白环境分析器 - 从synthesis_plan提取旁白内容并分析环境"""
    
    def __init__(self):
        # 复用现有LLM分析器的分析能力
        from app.services.llm_scene_analyzer import OllamaLLMSceneAnalyzer
        self.scene_analyzer = OllamaLLMSceneAnalyzer()
        
        # 旁白语速配置 (每分钟字数)
        self.NARRATION_SPEED_CHARS_PER_MINUTE = 300
        
    async def extract_and_analyze_narration(self, synthesis_plan: List[Dict]) -> Dict:
        """主入口：使用批量分析模式，LLM不可用时直接报错"""
        logger.error("🚨🚨🚨 [NARRATION_ANALYZER] 这是新版本的代码！使用批量分析模式，LLM不可用时直接报错！🚨🚨🚨")
        return await self.extract_and_analyze_narration_batch(synthesis_plan)
    
    async def extract_and_analyze_narration_batch(self, synthesis_plan: List[Dict]) -> Dict:
        """批量分析版本：一次分析，智能映射"""
        logger.info(f"[BATCH_ANALYZER] 开始批量分析synthesis_plan，共{len(synthesis_plan)}个段落")
        
        # 1. 提取所有旁白段落，记录时间轴信息
        narration_segments = []
        cumulative_time = 0.0
        
        for segment in synthesis_plan:
            segment_duration = self._calculate_segment_duration(segment)
            
            # 支持多种旁白标识
            narration_speakers = ['旁白', 'narrator', '叙述者', 'narration']
            if segment.get('speaker') in narration_speakers or segment.get('character') in narration_speakers:
                narration_text = segment.get('text', '') or segment.get('content', '')
                segment_id = segment.get('segment_id') or segment.get('id', f'seg_{len(narration_segments) + 1}')
                
                narration_segments.append({
                    'segment_id': segment_id,
                    'text': narration_text,
                    'start_time': cumulative_time,
                    'duration': segment_duration,
                    'end_time': cumulative_time + segment_duration
                })
                
                logger.info(f"[BATCH_ANALYZER] 收集旁白段落 {segment_id}: "
                           f"{cumulative_time:.1f}-{cumulative_time + segment_duration:.1f}s")
            
            cumulative_time += segment_duration
        
        if not narration_segments:
            logger.info("[BATCH_ANALYZER] 未找到旁白段落")
            return {
                'environment_tracks': [],
                'analysis_summary': {
                    'total_duration': cumulative_time,
                    'narration_segments': 0,
                    'environment_tracks_detected': 0,
                    'analysis_timestamp': datetime.now().isoformat()
                }
            }
        
        logger.info(f"[BATCH_ANALYZER] 找到{len(narration_segments)}个旁白段落，总时长{cumulative_time:.1f}s")
        
        # 2. 构建批量分析的提示词
        batch_prompt = self._build_batch_analysis_prompt(narration_segments)
        logger.info(f"[BATCH_ANALYZER] 构建批量提示词，长度: {len(batch_prompt)}字符")
        
        # 3. 一次性LLM分析
        logger.info("[BATCH_ANALYZER] 开始一次性LLM分析")
        llm_result = await self.scene_analyzer.analyze_text_scenes_with_llm(batch_prompt)
        logger.info(f"[BATCH_ANALYZER] LLM分析完成，识别到{len(llm_result.analyzed_scenes)}个场景")
        
        # 检查LLM是否真的有效分析
        if len(llm_result.analyzed_scenes) == 0 and llm_result.confidence_score == 0.0:
            raise RuntimeError("LLM分析器无法工作：返回空结果，请检查Ollama服务是否运行正常")
        
        # 4. 智能映射场景到具体段落
        environment_tracks = self._map_scenes_to_segments(llm_result, narration_segments)

        
        logger.info(f"[BATCH_ANALYZER] 批量分析完成: 总时长{cumulative_time:.1f}s，"
                   f"旁白段落{len(narration_segments)}个，环境音轨道{len(environment_tracks)}个")
        
        return {
            'environment_tracks': environment_tracks,
            'analysis_summary': {
                'total_duration': cumulative_time,
                'narration_segments': len(narration_segments),
                'environment_tracks_detected': len(environment_tracks),
                'analysis_timestamp': datetime.now().isoformat(),
                'analysis_mode': 'batch'
            }
        }
    
    def _build_batch_analysis_prompt(self, narration_segments: List[Dict]) -> str:
        """构建批量分析的提示词"""
        prompt_parts = ["请分析以下章节的旁白内容，提取每个时间段的环境声音："]
        
        for i, seg in enumerate(narration_segments):
            time_range = f"{seg['start_time']:.1f}-{seg['end_time']:.1f}s"
            prompt_parts.append(f"段落{i+1}({time_range}): {seg['text']}")
        
        combined_text = "\n".join(prompt_parts)
        logger.info(f"[BATCH_ANALYZER] 批量提示词示例: {combined_text[:200]}...")
        return combined_text
    
    def _map_scenes_to_segments(self, llm_result, narration_segments: List[Dict]) -> List[Dict]:
        """将场景分析结果映射到具体段落"""
        environment_tracks = []
        
        logger.info(f"[MAPPING] 开始映射{len(llm_result.analyzed_scenes)}个场景到{len(narration_segments)}个段落")
        
        # 如果没有识别到场景，返回空
        if not llm_result.analyzed_scenes:
            logger.info("[MAPPING] 未识别到任何场景")
            return environment_tracks
        
        # 策略1: 如果场景数量与段落数量匹配，一对一映射
        if len(llm_result.analyzed_scenes) == len(narration_segments):
            logger.info("[MAPPING] 场景与段落数量匹配，使用一对一映射")
            for i, segment in enumerate(narration_segments):
                scene = llm_result.analyzed_scenes[i]
                if scene.keywords:
                    environment_tracks.append({
                        'segment_id': segment['segment_id'],
                        'start_time': segment['start_time'],
                        'duration': segment['duration'],
                        'narration_text': segment['text'],
                        'environment_keywords': scene.keywords,
                        'scene_description': scene.location if scene.location != "detected_environment" else "、".join(scene.keywords[:3]),
                        'confidence': scene.confidence,
                        'analysis_timestamp': datetime.now().isoformat(),
                        'mapping_strategy': 'one_to_one'
                    })
                    logger.info(f"[MAPPING] 段落{i+1}映射到场景: {scene.keywords}")
        
        # 策略2: 场景数量不匹配，使用智能位置映射
        else:
            logger.info(f"[MAPPING] 场景数量({len(llm_result.analyzed_scenes)})与段落数量({len(narration_segments)})不匹配，使用智能位置映射")
            
            # 智能映射：为每个场景找到最佳匹配的段落
            used_segments = set()
            
            for scene_idx, scene in enumerate(llm_result.analyzed_scenes):
                if not scene.keywords:
                    continue
                    
                best_segment = None
                best_score = 0.0
                
                # 为当前场景找到最佳匹配的段落
                for segment in narration_segments:
                    if segment['segment_id'] in used_segments:
                        continue
                        
                    # 计算匹配分数
                    score = self._calculate_scene_segment_match_score(scene, segment)
                    
                    if score > best_score:
                        best_score = score
                        best_segment = segment
                
                # 如果找到了合适的匹配
                if best_segment and best_score > 0.1:
                    used_segments.add(best_segment['segment_id'])
                    
                    environment_tracks.append({
                        'segment_id': best_segment['segment_id'],
                        'start_time': best_segment['start_time'],
                        'duration': best_segment['duration'],
                        'narration_text': best_segment['text'],
                        'environment_keywords': scene.keywords,
                        'scene_description': scene.location if scene.location != "detected_environment" else "、".join(scene.keywords[:3]),
                        'confidence': scene.confidence * (0.8 + 0.2 * best_score),  # 根据匹配度调整置信度
                        'analysis_timestamp': datetime.now().isoformat(),
                        'mapping_strategy': 'intelligent_position_mapping'
                    })
                    logger.info(f"[MAPPING] 场景{scene_idx+1}({scene.keywords}) 智能映射到段落 {best_segment['segment_id']} (分数: {best_score:.2f})")
                else:
                    logger.info(f"[MAPPING] 场景{scene_idx+1}({scene.keywords}) 未找到合适的段落匹配")
        
        logger.info(f"[MAPPING] 映射完成，生成{len(environment_tracks)}个环境音轨道")
        return environment_tracks
    
    def _find_best_matching_scene(self, text: str, scenes: List) -> Optional[Any]:
        """为文本找到最匹配的场景"""
        if not scenes:
            return None
        
        # 简单的关键词匹配策略
        text_lower = text.lower()
        best_scene = None
        best_score = 0.0
        
        for scene in scenes:
            score = 0.0
            
            # 检查关键词匹配
            for keyword in scene.keywords:
                if keyword.lower() in text_lower:
                    score += 1.0
            
            # 检查场景位置匹配
            if hasattr(scene, 'location') and scene.location and scene.location.lower() in text_lower:
                score += 0.5
            
            # 归一化分数
            if len(scene.keywords) > 0:
                score = score / len(scene.keywords)
            
            if score > best_score:
                best_score = score
                best_scene = scene
        
        # 只返回有一定匹配度的场景
        if best_score > 0.2:
            logger.info(f"[MATCHING] 文本片段匹配到场景，分数: {best_score:.2f}")
            return best_scene
        
        # 如果没有好的匹配，不要使用默认场景，直接返回None
        # 这样可以避免将不相关的关键词分配给无法匹配的段落
        logger.info("[MATCHING] 未找到合适的匹配场景，跳过该段落")
        return None

    def _calculate_scene_segment_match_score(self, scene, segment) -> float:
        """计算场景与段落的匹配分数"""
        text = segment['text'].lower()
        score = 0.0
        
        # 检查关键词匹配
        for keyword in scene.keywords:
            keyword_lower = keyword.lower()
            if keyword_lower in text:
                score += 1.0
            # 检查相关词汇匹配
            elif self._check_related_keywords(keyword_lower, text):
                score += 0.5
        
        # 根据关键词数量归一化
        if len(scene.keywords) > 0:
            score = score / len(scene.keywords)
        
        return min(score, 1.0)  # 最大分数为1.0
    
    def _check_related_keywords(self, keyword: str, text: str) -> bool:
        """检查相关关键词匹配"""
        # 定义相关词汇映射
        related_words = {
            '脚步声': ['走', '跑', '跳', '踏', '进', '出'],
            '翻书声': ['书', '翻', '看', '读', '页'],
            '雷声': ['雷', '打雷', '雷鸣', '闪电'],
            '雨声': ['雨', '下雨', '雨点', '雨水'],
            '风声': ['风', '吹', '微风', '大风'],
            '虫鸣': ['虫', '蝉', '蛐蛐', '昆虫'],
            '鸟叫': ['鸟', '鸟儿', '歌唱', '啁啾'],
            '水声': ['水', '流水', '溪水', '河水']
        }
        
        if keyword in related_words:
            for related_word in related_words[keyword]:
                if related_word in text:
                    return True
        
        return False

    async def extract_and_analyze_narration_individual(self, synthesis_plan: List[Dict]) -> Dict:
        """原有的逐一分析方法（作为备用）"""
        logger.info(f"[INDIVIDUAL_ANALYZER] 开始逐一分析synthesis_plan，共{len(synthesis_plan)}个段落")
        
        environment_tracks = []
        cumulative_time = 0.0
        narration_count = 0
        
        for segment in synthesis_plan:
            # 只处理旁白segments (旁白才会说环境内容)
            narration_speakers = ['旁白', 'narrator', '叙述者', 'narration']
            if segment.get('speaker') in narration_speakers or segment.get('character') in narration_speakers:
                narration_count += 1
                
                # 计算旁白时长 (旁白语速固定，内容已在JSON)
                narration_text = segment.get('text', '') or segment.get('content', '')
                estimated_duration = self._calculate_narration_duration(narration_text)
                
                segment_id = segment.get('segment_id') or segment.get('id', f'seg_{narration_count}')
                logger.info(f"[INDIVIDUAL_ANALYZER] 处理旁白段落 {segment_id}: "
                           f"时长{estimated_duration:.1f}s，内容: {narration_text[:50]}...")
                
                # 使用LLM提取声音关键词
                try:
                    logger.info("[INDIVIDUAL_ANALYZER] 使用LLM提取声音关键词")
                    llm_result = await self.scene_analyzer.analyze_text_scenes_with_llm(narration_text)
                    
                    # 转换为我们需要的格式
                    environment_analysis = {
                        'environment_detected': len(llm_result.analyzed_scenes) > 0,
                        'scene_keywords': [],
                        'scene_description': '',
                        'confidence': llm_result.confidence_score
                    }
                    
                    # 提取关键词和场景描述
                    if llm_result.analyzed_scenes:
                        for scene in llm_result.analyzed_scenes:
                            environment_analysis['scene_keywords'].extend(scene.keywords)
                            if scene.location and scene.location != "detected_environment":
                                environment_analysis['scene_description'] += f"{scene.location} "
                        
                        # 去重关键词
                        environment_analysis['scene_keywords'] = list(set(environment_analysis['scene_keywords']))
                        environment_analysis['scene_description'] = environment_analysis['scene_description'].strip()
                        
                        # 如果没有具体场景描述，用关键词组合
                        if not environment_analysis['scene_description']:
                            environment_analysis['scene_description'] = "、".join(environment_analysis['scene_keywords'][:3])
                    
                    # 检查LLM是否真的有效分析
                    if len(llm_result.analyzed_scenes) == 0 and llm_result.confidence_score == 0.0:
                        raise RuntimeError(f"LLM分析器无法工作：段落 {segment_id} 返回空结果，请检查Ollama服务是否运行正常")
                    
                    if environment_analysis.get('environment_detected'):
                        environment_tracks.append({
                            'segment_id': segment_id,
                            'start_time': cumulative_time,
                            'duration': estimated_duration,
                            'narration_text': narration_text,
                            'environment_keywords': environment_analysis.get('scene_keywords', []),
                            'scene_description': environment_analysis.get('scene_description', ''),
                            'confidence': environment_analysis.get('confidence', 0.0),
                            'analysis_timestamp': datetime.now().isoformat(),
                            'mapping_strategy': 'individual'
                        })
                        
                        logger.info(f"[INDIVIDUAL_ANALYZER] 检测到环境: {environment_analysis.get('scene_keywords', [])}")
                    else:
                        logger.info(f"[INDIVIDUAL_ANALYZER] LLM未检测到环境声音")
                        
                except Exception as e:
                    logger.error(f"[INDIVIDUAL_ANALYZER] LLM分析失败: {str(e)}")
                    raise RuntimeError(f"LLM分析器异常：段落 {segment_id} 分析失败 - {str(e)}")
                
                cumulative_time += estimated_duration
            else:
                # 非旁白段落，累加时长但不分析环境
                segment_duration = self._calculate_segment_duration(segment)
                cumulative_time += segment_duration
                
        logger.info(f"[INDIVIDUAL_ANALYZER] 分析完成: 总时长{cumulative_time:.1f}s，"
                   f"旁白段落{narration_count}个，环境音轨道{len(environment_tracks)}个")
                
        return {
            'environment_tracks': environment_tracks,
            'analysis_summary': {
                'total_duration': cumulative_time,
                'narration_segments': narration_count,
                'environment_tracks_detected': len(environment_tracks),
                'analysis_timestamp': datetime.now().isoformat(),
                'analysis_mode': 'individual'
            }
        }
        
    def _calculate_narration_duration(self, text: str) -> float:
        """计算旁白时长 (语速固定)"""
        if not text or not text.strip():
            return 0.0
            
        # 去除空白字符，计算有效字符数
        char_count = len(text.replace(' ', '').replace('\n', '').replace('\t', ''))
        
        # 根据固定语速计算时长
        duration_minutes = char_count / self.NARRATION_SPEED_CHARS_PER_MINUTE
        duration_seconds = duration_minutes * 60.0
        
        # 最少1秒，最多60秒
        return max(1.0, min(duration_seconds, 60.0))
        
    def _calculate_segment_duration(self, segment: Dict) -> float:
        """计算其他段落时长"""
        # 尝试从segment中获取预估时长
        if 'estimated_duration' in segment:
            return float(segment['estimated_duration'])
            
        # 如果没有预估时长，根据文本长度计算
        text = segment.get('text', '') or segment.get('content', '')
        if text:
            # 对话通常比旁白语速快一些
            char_count = len(text.replace(' ', '').replace('\n', ''))
            duration_minutes = char_count / 400  # 对话语速更快
            return max(0.5, duration_minutes * 60.0)
            
        return 1.0  # 默认1秒
        
    def get_analysis_stats(self, analysis_result: Dict) -> Dict:
        """获取分析统计信息"""
        environment_tracks = analysis_result.get('environment_tracks', [])
        
        if not environment_tracks:
            return {
                'total_tracks': 0,
                'total_duration': 0.0,
                'avg_duration': 0.0,
                'keyword_distribution': {},
                'confidence_distribution': {}
            }
            
        total_duration = sum(track['duration'] for track in environment_tracks)
        avg_duration = total_duration / len(environment_tracks)
        
        # 关键词分布统计
        keyword_count = {}
        for track in environment_tracks:
            for keyword in track.get('environment_keywords', []):
                keyword_count[keyword] = keyword_count.get(keyword, 0) + 1
                
        # 置信度分布统计
        confidence_ranges = {'高(>0.8)': 0, '中(0.5-0.8)': 0, '低(<0.5)': 0}
        for track in environment_tracks:
            confidence = track.get('confidence', 0.0)
            if confidence > 0.8:
                confidence_ranges['高(>0.8)'] += 1
            elif confidence > 0.5:
                confidence_ranges['中(0.5-0.8)'] += 1
            else:
                confidence_ranges['低(<0.5)'] += 1
                
        return {
            'total_tracks': len(environment_tracks),
            'total_duration': round(total_duration, 1),
            'avg_duration': round(avg_duration, 1),
            'keyword_distribution': dict(sorted(keyword_count.items(), key=lambda x: x[1], reverse=True)),
            'confidence_distribution': confidence_ranges
        }
