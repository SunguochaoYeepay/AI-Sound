"""
旁白环境分析器
从synthesis_plan提取旁白内容并分析环境关键词与时长
集成智能时间轴修正器，确保环境音与旁白描述同步
"""

import logging
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
        
        # 5. 🕐 应用智能时间轴修正器
        if environment_tracks:
            logger.info("[BATCH_ANALYZER] 开始应用智能时间轴修正")
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
        """构建批量分析的提示词"""
        
        # 构建更详细的提示词，包含具体的环境音类型指导
        prompt_parts = [
            "请仔细分析以下小说章节的旁白内容，识别每个时间段中描述的环境声音。",
            "",
            "需要识别的环境音类型包括但不限于：",
            "• 自然环境：雨声、雷声、风声、鸟鸣、虫鸣、海浪声、流水声、叶子摩擦声",
            "• 人为活动：脚步声、开门声、关门声、翻书声、写字声、敲击声、机械声",
            "• 室内环境：时钟滴答声、空调声、火焰燃烧声、电器运转声、厨房声音",
            "• 交通环境：汽车声、火车声、飞机声、轮船声、马蹄声",
            "• 社交场景：人群喧哗、掌声、音乐声、乐器声、歌声",
            "",
            "分析要求：",
            "1. 只分析明确描述或暗示有具体声音的内容",
            "2. 优先识别直接描述的声音（如'雨声''脚步声'）",
            "3. 从环境描述中推断可能的环境音（如'雨夜'→雨声，'走过走廊'→脚步声）",
            "4. 考虑场景的时间、地点、天气对环境音的影响",
            "5. 忽略纯粹的对话、心理描述和情感表达",
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
            "请为每个段落提供分析结果，格式如下：",
            "段落X：[识别到的环境音关键词列表，用逗号分隔]",
            "如果某段落没有明确的环境音，请标注：段落X：无环境音"
        ])
        
        combined_text = "\n".join(prompt_parts)
        logger.info(f"[BATCH_ANALYZER] 优化后的批量提示词长度: {len(combined_text)}字符")
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
        # 扩展的相关词汇映射 - 更全面的环境音识别
        related_words = {
            # 自然环境音
            '脚步声': ['走', '跑', '跳', '踏', '进', '出', '踱步', '奔跑', '疾走', '缓步', '迈步', '跨步', '踏入', '走向', '朝着', '步入', '赶路'],
            '翻书声': ['书', '翻', '看', '读', '页', '书页', '翻阅', '阅读', '查看', '翻动', '书本', '典籍', '册子'],
            '雷声': ['雷', '打雷', '雷鸣', '闪电', '雷电', '霹雳', '轰隆', '雷声隆隆', '电闪雷鸣', '雷雨', '雷暴'],
            '雨声': ['雨', '下雨', '雨点', '雨水', '降雨', '细雨', '大雨', '暴雨', '雨滴', '雨夜', '雨声', '雨打', '雨淋'],
            '风声': ['风', '吹', '微风', '大风', '清风', '狂风', '劲风', '风起', '风声', '呼啸', '吹拂', '风吹', '刮风'],
            '虫鸣': ['虫', '蝉', '蛐蛐', '昆虫', '虫子', '蝉鸣', '蟋蟀', '鸣虫', '夏虫', '秋虫', '虫唱', '虫声'],
            '鸟叫': ['鸟', '鸟儿', '歌唱', '啁啾', '鸟鸣', '鸟声', '飞鸟', '百鸟', '鸟啼', '雀鸟', '鸣禽', '鸟语'],
            '水声': ['水', '流水', '溪水', '河水', '湖水', '泉水', '水流', '潺潺', '涓涓', '汩汩', '溪流', '江河', '喷泉'],
            
            # 室内环境音
            '开门声': ['开门', '推门', '拉门', '门开', '开启', '房门', '大门', '木门', '推开', '拉开'],
            '关门声': ['关门', '关上', '门关', '合门', '掩门', '闭门', '砰', '门响'],
            '敲门声': ['敲门', '敲击', '叩门', '拍门', '门响', '敲打', '扣门'],
            '时钟声': ['时钟', '钟表', '滴答', '钟声', '表声', '计时', '钟摆', '秒针'],
            '火焰声': ['火', '火焰', '燃烧', '篝火', '炉火', '火苗', '烛火', '劈啪', '噼啪'],
            
            # 人为活动音
            '写字声': ['写', '书写', '记录', '笔', '纸', '写字', '执笔', '落笔', '书写'],
            '翻页声': ['翻页', '翻动', '纸张', '书页', '页面', '翻看'],
            '咳嗽声': ['咳嗽', '咳', '清咳', '轻咳'],
            '呼吸声': ['呼吸', '喘息', '呼气', '吸气', '喘气', '气息'],
            '心跳声': ['心跳', '心脏', '心律', '脉搏', '跳动'],
            
            # 交通环境音
            '汽车声': ['汽车', '车辆', '轿车', '货车', '卡车', '车子', '车声', '引擎', '发动机', '马达'],
            '马蹄声': ['马', '马匹', '战马', '骏马', '马蹄', '奔马', '骑马'],
            '火车声': ['火车', '列车', '车厢', '铁路', '轨道', '汽笛'],
            
            # 社交场景音
            '人群声': ['人群', '众人', '人们', '人声', '嘈杂', '喧哗', '嘈嘈', '议论', '交谈'],
            '掌声': ['掌声', '鼓掌', '喝彩', '叫好', '欢呼'],
            '音乐声': ['音乐', '乐声', '旋律', '乐曲', '演奏', '弹奏'],
            '歌声': ['歌声', '歌唱', '吟唱', '唱歌', '歌谣', '吟诵'],
            
            # 厨房环境音
            '切菜声': ['切菜', '切', '刀', '菜板', '料理', '烹饪'],
            '炒菜声': ['炒菜', '炒', '烹饪', '下锅', '爆炒'],
            '煮水声': ['煮水', '烧水', '开水', '水开', '沸腾'],
            
            # 战斗/武器音
            '刀剑声': ['刀', '剑', '兵器', '刀剑', '兵刃', '利刃', '宝剑', '长刀'],
            '撞击声': ['撞击', '碰撞', '撞', '击', '碰', '撞击'],
            '破碎声': ['破碎', '碎裂', '破', '碎', '粉碎', '打碎'],
            
            # 天气相关
            '雪声': ['雪', '下雪', '雪花', '飘雪', '雪夜', '风雪'],
            '冰声': ['冰', '结冰', '冰块', '冰霜', '冰冷'],
            
            # 动物声音
            '猫声': ['猫', '猫咪', '小猫', '喵', '猫叫'],
            '狗声': ['狗', '犬', '小狗', '汪', '狗叫', '犬吠'],
            '马声': ['马', '马匹', '马嘶', '嘶鸣'],
            '鸡声': ['鸡', '公鸡', '鸡鸣', '鸡叫', '啼鸣']
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
        
        # 🕐 应用智能时间轴修正器
        if environment_tracks:
            logger.info("[INDIVIDUAL_ANALYZER] 开始应用智能时间轴修正")
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
