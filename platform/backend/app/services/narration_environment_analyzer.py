"""
旁白环境分析器
从synthesis_plan提取旁白内容并分析环境关键词与时长
集成智能时间轴修正器，确保环境音与旁白描述同步
"""

import logging
import re
from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

class NarrationEnvironmentAnalyzer:
    """旁白环境分析器 - 从synthesis_plan提取旁白内容并分析环境"""
    
    def __init__(self, db: Optional[Session] = None):
        # 复用现有LLM分析器的分析能力
        from app.services.llm_scene_analyzer import OllamaLLMSceneAnalyzer
        self.scene_analyzer = OllamaLLMSceneAnalyzer()
        
        # 智能时间轴修正器
        from app.services.intelligent_timeline_corrector import IntelligentTimelineCorrector
        self.timeline_corrector = IntelligentTimelineCorrector()
        
        # 数据库会话（用于获取实际音频时长）
        self.db = db
        
        # 旁白语速配置 (每分钟字数) - 仅作为后备方案
        self.NARRATION_SPEED_CHARS_PER_MINUTE = 300
        
    async def extract_and_analyze_narration(self, synthesis_plan: List[Dict]) -> Dict:
        """主入口：使用批量分析模式，LLM不可用时直接报错"""
        logger.error("🚨🚨🚨 [NARRATION_ANALYZER] 这是新版本的代码！使用批量分析模式，LLM不可用时直接报错！🚨🚨🚨")
        return await self.extract_and_analyze_narration_batch(synthesis_plan)
    
    async def extract_and_analyze_narration_batch(self, synthesis_plan: List[Dict]) -> Dict:
        """批量分析版本：一次分析，智能映射"""
        logger.info(f"[BATCH_ANALYZER] 开始批量分析synthesis_plan，共{len(synthesis_plan)}个段落")
        logger.info(f"[BATCH_ANALYZER] 第一个段落内容: {synthesis_plan[0] if synthesis_plan else 'No segments'}")
        
        # 1. 提取所有旁白段落，记录时间轴信息
        narration_segments = []
        cumulative_time = 0.0
        
        for segment in synthesis_plan:
            # 支持多种旁白标识
            narration_speakers = ['旁白', 'narrator', '叙述者', 'narration']
            if segment.get('speaker') in narration_speakers or segment.get('character') in narration_speakers:
                narration_text = segment.get('text', '') or segment.get('content', '')
                # 旁白段落使用专门的时长计算方法
                segment_duration = self._calculate_narration_duration(narration_text)
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
            else:
                # 非旁白段落使用通用时长计算方法
                segment_duration = self._calculate_segment_duration(segment)
            
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
        
        # 5. 🕐 简化时间轴修正 - 只在必要时进行修正
        if environment_tracks:
            logger.info("[BATCH_ANALYZER] 检查是否需要时间轴修正")
            
            # 检查是否有明显的时间轴问题
            needs_correction = False
            for track in environment_tracks:
                if track['start_time'] < 0 or track['duration'] <= 0:
                    needs_correction = True
                    break
            
            if needs_correction:
                logger.info("[BATCH_ANALYZER] 检测到时间轴问题，应用修正")
                original_tracks = [track.copy() for track in environment_tracks]  # 保存原始数据
                corrected_tracks = self.timeline_corrector.correct_environment_tracks_timeline(
                    environment_tracks, narration_segments
                )
                
                # 获取修正统计
                correction_summary = self.timeline_corrector.get_correction_summary(
                    original_tracks, corrected_tracks
                )
                
                logger.info(f"[BATCH_ANALYZER] 时间轴修正完成: {correction_summary['summary']}")
                environment_tracks = corrected_tracks
            else:
                logger.info("[BATCH_ANALYZER] 时间轴正常，跳过修正")
        
        logger.info(f"[BATCH_ANALYZER] 批量分析完成: 总时长{cumulative_time:.1f}s，"
                   f"旁白段落{len(narration_segments)}个，环境音轨道{len(environment_tracks)}个")
        
        return {
            'environment_tracks': environment_tracks,
            'analysis_summary': {
                'total_duration': cumulative_time,
                'narration_segments': len(narration_segments),
                'environment_tracks_detected': len(environment_tracks),
                'analysis_timestamp': datetime.now().isoformat(),
                'analysis_mode': 'batch',
                'timeline_correction_applied': True if environment_tracks else False
            }
        }
    
    def _build_batch_analysis_prompt(self, narration_segments: List[Dict]) -> str:
        """构建批量分析的提示词 - 增强时序分析能力"""
        
        # 构建更详细的提示词，包含时序分析指导
        prompt_parts = [
            "请仔细分析以下小说章节的旁白内容，识别每个时间段中描述的环境声音及其时序特征。",
            "",
            "⚠️ 重要原则：只识别文本中明确描述或暗示的实际发生的动作声音，不要基于场景进行联想！",
            "",
            "需要识别的环境音类型包括但不限于：",
            "• 自然环境：雨声、雷声、风声、鸟鸣、虫鸣、海浪声、流水声、叶子摩擦声",
            "• 人为活动：脚步声、开门声、关门声、翻书声、写字声、敲击声、机械声",
            "• 室内环境：时钟滴答声、空调声、火焰燃烧声、电器运转声、厨房声音",
            "• 交通环境：汽车声、火车声、飞机声、轮船声、马蹄声",
            "• 社交场景：人群喧哗、掌声、音乐声、乐器声、歌声",
            "",
            "⚠️ 识别规则：",
            "1. 只识别文本中明确提到的动作声音（如'脚步声'、'叮声'、'马蹄声'）",
            "2. 不要因为场景是'御书房'就联想'翻书声'、'写字声'",
            "3. 不要因为场景是'厨房'就联想'炒菜声'、'切菜声'",
            "4. 如果文本中没有明确描述声音，标记为'无声段'",
            "5. 区分动作描述和声音描述：'走路'≠'脚步声'，'说话'≠'说话声'",
            "",
            "时序分析要求：",
            "1. 分析声音的持续时间：瞬间声音（如'叮'、'砰'）通常1-2秒，持续声音（如'雨声'、'空调声'）持续整个段落",
            "2. 分析声音的强度变化：高强度（如'雷声'、'爆炸声'）、中强度（如'脚步声'、'说话声'）、低强度（如'呼吸声'、'时钟声'）",
            "3. 分析声音的时序关系：哪些声音同时发生，哪些声音先后发生",
            "4. 识别无声段落：纯对话、心理描述、无声动作等",
            "5. 考虑声音的因果关系：如'手机震动'→'叮'声，'看消息'→无声",
            "",
            "以下是需要分析的旁白内容：",
            ""
        ]
        
        for i, seg in enumerate(narration_segments):
            time_range = f"{seg['start_time']:.1f}-{seg['end_time']:.1f}s"
            # 清理文本，移除多余的空格和换行
            clean_text = ' '.join(seg['text'].split())
            prompt_parts.append(f"【段落{i+1}】时间轴：{time_range}")
            prompt_parts.append(f"内容：{clean_text}")
            prompt_parts.append("")
        
        prompt_parts.extend([
            "请为每个段落提供详细的时序分析结果，格式如下：",
            "段落X：",
            "- 声音事件1：[声音类型] [开始时间] [持续时间] [强度] [描述]",
            "- 声音事件2：[声音类型] [开始时间] [持续时间] [强度] [描述]",
            "- 无声段：[开始时间] [持续时间] [描述]",
            "",
            "示例：",
            "段落1：",
            "- 声音事件1：空调声 0.0s 14.4s 低强度 持续的背景嗡鸣（文本明确提到'空调发出轻微嗡鸣'）",
            "段落2：",
            "- 声音事件1：手机震动声 0.0s 1.5s 高强度 叮的一声（文本明确提到'手机震动'和'叮'）",
            "- 无声段：1.5s 6.5s 查看消息内容（文本没有描述其他声音）",
            "",
            "错误示例：",
            "❌ 不要因为'御书房'就联想'翻书声'、'写字声'",
            "❌ 不要因为'厨房'就联想'炒菜声'、'切菜声'",
            "❌ 不要因为'走路'就联想'脚步声'（除非文本明确提到）"
        ])
        
        combined_text = "\n".join(prompt_parts)
        logger.info(f"[BATCH_ANALYZER] 增强时序分析提示词长度: {len(combined_text)}字符")
        logger.info(f"[BATCH_ANALYZER] 提示词前200字符: {combined_text[:200]}...")
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
                     # 清理和过滤关键词
                     filtered_keywords = self._clean_environment_keywords(scene.keywords)
                     
                     # 智能时长分配
                     duration, start_time = self._calculate_smart_duration(
                         filtered_keywords, segment['duration'], segment['start_time']
                     )
                     
                     environment_tracks.append({
                         'segment_id': segment['segment_id'],
                         'start_time': start_time,
                         'duration': duration,
                         'narration_text': segment['text'],
                         'environment_keywords': filtered_keywords,
                         'scene_description': scene.location if scene.location != "detected_environment" else "、".join(filtered_keywords[:3]),
                         'confidence': scene.confidence,
                         'analysis_timestamp': datetime.now().isoformat(),
                         'mapping_strategy': 'one_to_one'
                     })
                     logger.info(f"[MAPPING] 段落{i+1}映射到场景: {filtered_keywords}")
        
        # 策略2: 场景数量不匹配，使用智能位置映射
        else:
            logger.info(f"[MAPPING] 场景数量({len(llm_result.analyzed_scenes)})与段落数量({len(narration_segments)})不匹配，使用智能位置映射")
            
            # 改进的智能映射：为每个段落找到最匹配的场景，或者创建新场景
            used_segments = set()
            used_scenes = set()
            
            # 第一轮：为每个场景找到最佳匹配的段落
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
                    # 清理和过滤关键词
                    filtered_keywords = self._clean_environment_keywords(scene.keywords)
                    
                    # 智能时长分配
                    duration, start_time = self._calculate_smart_duration(
                        filtered_keywords, best_segment['duration'], best_segment['start_time']
                    )
                    
                    used_segments.add(best_segment['segment_id'])
                    used_scenes.add(scene_idx)
                    
                    environment_tracks.append({
                        'segment_id': best_segment['segment_id'],
                        'start_time': start_time,
                        'duration': duration,
                        'narration_text': best_segment['text'],
                        'environment_keywords': filtered_keywords,
                        'scene_description': scene.location if scene.location != "detected_environment" else "、".join(filtered_keywords[:3]),
                        'confidence': scene.confidence * (0.8 + 0.2 * best_score),  # 根据匹配度调整置信度
                        'analysis_timestamp': datetime.now().isoformat(),
                        'mapping_strategy': 'intelligent_position_mapping'
                    })
                    logger.info(f"[MAPPING] 场景{scene_idx+1}({filtered_keywords}) 智能映射到段落 {best_segment['segment_id']} (分数: {best_score:.2f})")
                else:
                    logger.info(f"[MAPPING] 场景{scene_idx+1}({scene.keywords}) 未找到合适的段落匹配")
            
            # 第二轮：为未匹配的段落尝试创建环境音轨道
            for segment in narration_segments:
                if segment['segment_id'] in used_segments:
                    continue
                
                # 尝试从文本中直接提取环境音关键词 - 使用智能提取，避免硬编码
                text = segment['text']
                detected_sounds = self._extract_sounds_from_text(text)
                
                if detected_sounds:
                    # 智能时长分配
                    duration, start_time = self._calculate_smart_duration(
                        detected_sounds, segment['duration'], segment['start_time']
                    )
                    
                    environment_tracks.append({
                        'segment_id': segment['segment_id'],
                        'start_time': start_time,
                        'duration': duration,
                        'narration_text': segment['text'],
                        'environment_keywords': detected_sounds,
                        'scene_description': "、".join(detected_sounds[:3]),
                        'confidence': 0.6,  # 直接提取的置信度较低
                        'analysis_timestamp': datetime.now().isoformat(),
                        'mapping_strategy': 'direct_text_extraction'
                    })
                    logger.info(f"[MAPPING] 段落 {segment['segment_id']} 直接提取到环境音: {detected_sounds}")
                else:
                    logger.info(f"[MAPPING] 段落 {segment['segment_id']} 未检测到环境音，跳过")
             
            # 第二轮：为未匹配的段落创建空环境音轨道（完全依赖LLM）
            for segment in narration_segments:
                 if segment['segment_id'] in used_segments:
                     continue
                 
                 # 如果LLM没有识别到声音，就不创建环境音轨道
                 logger.info(f"[MAPPING] 段落 {segment['segment_id']} LLM未识别到声音，跳过")
        
        logger.info(f"[MAPPING] 映射完成，生成{len(environment_tracks)}个环境音轨道")
        return environment_tracks
    
    def _clean_environment_keywords(self, keywords: List[str]) -> List[str]:
        """清理环境音关键词，移除无关信息"""
        if not keywords:
            return []
        
        cleaned_keywords = []
        for keyword in keywords:
            if not isinstance(keyword, str):
                continue
                
            # 移除包含描述性文本的关键词
            if any(desc in keyword for desc in ['**段落', '无声段', '声音事件', '强度', '文本明确提到']):
                continue
                
            # 移除包含时间信息的关键词（时间信息已单独处理）
            if re.search(r'\d+\.?\d*s', keyword):
                continue
                
            # 移除过长的关键词（通常是描述性文本）
            if len(keyword) > 20:
                continue
                
            # 清理关键词
            clean_keyword = keyword.strip()
            if clean_keyword and clean_keyword not in cleaned_keywords:
                cleaned_keywords.append(clean_keyword)
        
        # 限制关键词数量
        return cleaned_keywords[:3]
    
    def _extract_sounds_from_text(self, text: str) -> List[str]:
         """智能从文本中提取声音关键词，不依赖硬编码列表"""
         if not text:
             return []
         
         detected_sounds = []
         
         # 使用正则表达式匹配常见的声音描述模式
         import re
         
         # 匹配 "XXX声" 模式
         sound_patterns = [
             r'([^，。！？\s]+声)',  # 匹配 "脚步声"、"钟声" 等
             r'([^，。！？\s]+响)',  # 匹配 "轻响"、"巨响" 等
             r'([^，。！？\s]+鸣)',  # 匹配 "鸟鸣"、"虫鸣" 等
             r'([^，。！？\s]+叫)',  # 匹配 "狗叫"、"猫叫" 等
             r'([^，。！？\s]+音)',  # 匹配 "音乐声"、"说话声" 等
         ]
         
         for pattern in sound_patterns:
             matches = re.findall(pattern, text)
             for match in matches:
                 if len(match) >= 2 and len(match) <= 6:  # 合理的长度范围
                     detected_sounds.append(match)
         
         # 匹配动作产生的声音
         action_sound_patterns = [
             r'([^，。！？\s]+步)',  # 匹配 "脚步"、"跑步" 等
             r'([^，。！？\s]+敲)',  # 匹配 "敲门"、"敲击" 等
             r'([^，。！？\s]+打)',  # 匹配 "打雷"、"打击" 等
             r'([^，。！？\s]+摩擦)',  # 匹配 "摩擦声" 等
         ]
         
         for pattern in action_sound_patterns:
             matches = re.findall(pattern, text)
             for match in matches:
                 if len(match) >= 2 and len(match) <= 6:
                     detected_sounds.append(match + "声")
         
         # 去重并限制数量
         unique_sounds = list(set(detected_sounds))
         return unique_sounds[:3]  # 最多返回3个
     
    def _calculate_smart_duration(self, keywords: List[str], segment_duration: float, segment_start: float) -> tuple:
         """智能计算环境音时长 - 基于关键词特征，减少硬编码"""
         if not keywords:
             return segment_duration, segment_start
         
         # 基于关键词特征判断声音类型，而不是硬编码列表
         def is_instant_sound(keyword: str) -> bool:
             """判断是否为瞬间声音"""
             # 瞬间声音通常包含这些特征
             instant_indicators = ['叮', '砰', '啪', '咚', '响', '震动', '吱呀', '敲门', '铃声', '爆炸', '破碎']
             return any(indicator in keyword for indicator in instant_indicators)
         
         def is_continuous_sound(keyword: str) -> bool:
             """判断是否为持续声音"""
             # 持续声音通常包含这些特征
             continuous_indicators = ['声', '音', '鸣', '叫', '吼', '啸', '嗡', '雨', '风', '雷', '水', '音乐', '歌', '说话', '人群']
             return any(indicator in keyword for indicator in continuous_indicators)
         
         # 检查关键词类型
         has_instant = any(is_instant_sound(kw) for kw in keywords)
         has_continuous = any(is_continuous_sound(kw) for kw in keywords)
         
         # 智能时长分配
         if has_instant and not has_continuous:
             # 纯瞬间声音：1-2秒
             duration = 1.5
             start_time = segment_start + segment_duration * 0.3  # 在段落30%位置开始
         elif has_continuous and not has_instant:
             # 纯持续声音：使用段落时长
             duration = segment_duration
             start_time = segment_start
         elif has_instant and has_continuous:
             # 混合声音：瞬间声音1.5秒，持续声音使用段落时长
             duration = segment_duration
             start_time = segment_start
         else:
             # 未知类型：使用段落时长
             duration = segment_duration
             start_time = segment_start
         
         logger.info(f"[SMART_DURATION] 关键词: {keywords}, 类型: {'瞬间' if has_instant else '持续'}, 时长: {duration:.1f}s")
         
         return duration, start_time
    
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
    
    def _filter_invalid_keywords(self, keywords: List[str], text: str) -> List[str]:
        """过滤无效的关键词，避免场景联想错误"""
        filtered_keywords = []
        text_lower = text.lower()
        
        # 强制过滤错误的关键词
        invalid_keywords = ['翻书声', '写字声', '水声']
        
        for keyword in keywords:
            keyword_lower = keyword.lower()
            is_valid = True
            
            # 强制过滤这些错误的关键词
            for invalid_keyword in invalid_keywords:
                if invalid_keyword in keyword_lower:
                    logger.info(f"[FILTER] 强制过滤错误关键词: {keyword}")
                    is_valid = False
                    break
            
            if is_valid:
                filtered_keywords.append(keyword)
        
        logger.info(f"[FILTER] 过滤前: {keywords}")
        logger.info(f"[FILTER] 过滤后: {filtered_keywords}")
        return filtered_keywords

    def _check_related_keywords(self, keyword: str, text: str) -> bool:
        """检查相关关键词匹配 - 已移除，完全依赖LLM"""
        # 不再使用硬编码逻辑，完全依赖LLM的智能分析
        return False

    def _extract_default_environment_keywords(self, text: str) -> List[str]:
        """从文本中提取默认环境音关键词 - 已移除，完全依赖LLM"""
        # 不再使用硬编码逻辑，完全依赖LLM的智能分析
        return []

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
        
        # 🕐 简化时间轴修正 - 只在必要时进行修正
        if environment_tracks:
            logger.info("[INDIVIDUAL_ANALYZER] 检查是否需要时间轴修正")
            
            # 检查是否有明显的时间轴问题
            needs_correction = False
            for track in environment_tracks:
                if track['start_time'] < 0 or track['duration'] <= 0:
                    needs_correction = True
                    break
            
            if needs_correction:
                logger.info("[INDIVIDUAL_ANALYZER] 检测到时间轴问题，应用修正")
                # 构建段落信息供修正器使用
                narration_segments = []
                current_time = 0.0
                for segment in synthesis_plan:
                    segment_duration = self._calculate_segment_duration(segment)
                    narration_speakers = ['旁白', 'narrator', '叙述者', 'narration']
                    if segment.get('speaker') in narration_speakers or segment.get('character') in narration_speakers:
                        narration_segments.append({
                            'segment_id': segment.get('segment_id') or segment.get('id'),
                            'text': segment.get('text', '') or segment.get('content', ''),
                            'start_time': current_time,
                            'duration': segment_duration
                        })
                    current_time += segment_duration
                
                original_tracks = [track.copy() for track in environment_tracks]
                corrected_tracks = self.timeline_corrector.correct_environment_tracks_timeline(
                    environment_tracks, narration_segments
                )
                
                correction_summary = self.timeline_corrector.get_correction_summary(
                    original_tracks, corrected_tracks
                )
                
                logger.info(f"[INDIVIDUAL_ANALYZER] 时间轴修正完成: {correction_summary['summary']}")
                environment_tracks = corrected_tracks
            else:
                logger.info("[INDIVIDUAL_ANALYZER] 时间轴正常，跳过修正")
                
        logger.info(f"[INDIVIDUAL_ANALYZER] 分析完成: 总时长{cumulative_time:.1f}s，"
                   f"旁白段落{narration_count}个，环境音轨道{len(environment_tracks)}个")
                
        return {
            'environment_tracks': environment_tracks,
            'analysis_summary': {
                'total_duration': cumulative_time,
                'narration_segments': narration_count,
                'environment_tracks_detected': len(environment_tracks),
                'analysis_timestamp': datetime.now().isoformat(),
                'analysis_mode': 'individual',
                'timeline_correction_applied': True if environment_tracks else False
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
        """计算段落时长 - 优先使用实际音频时长"""
        
        # 1. 优先从segment中获取预估时长
        if 'estimated_duration' in segment:
            return float(segment['estimated_duration'])
        
        # 2. 尝试从数据库获取实际音频时长
        if self.db and 'segment_id' in segment:
            try:
                from app.models.audio import AudioFile
                
                # 根据segment_id查找对应的音频文件
                audio_file = self.db.query(AudioFile).filter(
                    AudioFile.segment_id == segment['segment_id'],
                    AudioFile.audio_type == 'segment',
                    AudioFile.status == 'active'
                ).first()
                
                if audio_file and audio_file.duration:
                    logger.info(f"[DURATION] 段落{segment['segment_id']}使用实际音频时长: {audio_file.duration:.1f}s")
                    return float(audio_file.duration)
                else:
                    logger.debug(f"[DURATION] 段落{segment['segment_id']}未找到实际音频文件，使用估算时长")
                    
            except Exception as e:
                logger.warning(f"[DURATION] 获取实际音频时长失败: {str(e)}")
        
        # 3. 如果没有数据库连接或未找到音频文件，根据文本长度计算
        text = segment.get('text', '') or segment.get('content', '')
        if text:
            # 对话通常比旁白语速快一些
            char_count = len(text.replace(' ', '').replace('\n', ''))
            duration_minutes = char_count / 400  # 对话语速更快
            estimated_duration = max(0.5, duration_minutes * 60.0)
            logger.debug(f"[DURATION] 段落估算时长: {estimated_duration:.1f}s (字符数: {char_count})")
            return estimated_duration
            
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
