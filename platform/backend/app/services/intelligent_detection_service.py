from typing import List, Dict, Any, Optional
import re
from dataclasses import dataclass
from app.models.book_chapter import BookChapter
from app.models.analysis_result import AnalysisResult
from app.database import get_db
from sqlalchemy.orm import Session
import logging

logger = logging.getLogger(__name__)

@dataclass
class DetectionIssue:
    """检测到的问题"""
    issue_type: str  # 问题类型
    severity: str    # 严重程度: 'low', 'medium', 'high'
    segment_index: int  # 片段索引
    description: str    # 问题描述
    suggestion: str     # 修复建议
    context: Optional[str] = None  # 上下文信息
    fixable: bool = True  # 是否可自动修复
    fix_data: Optional[Dict[str, Any]] = None  # 修复数据

@dataclass
class DetectionResult:
    """检测结果"""
    chapter_id: int
    total_issues: int
    issues_by_severity: Dict[str, int]
    fixable_issues: int
    issues: List[DetectionIssue]
    detection_time: str
    
class IntelligentDetectionService:
    """智能检测服务"""
    
    def __init__(self):
        self.issue_patterns = {
            'character_mismatch': {
                'description': '角色名称与语音配置不匹配',
                'severity': 'high',
                'fixable': True
            },
            'empty_content': {
                'description': '片段内容为空',
                'severity': 'medium',
                'fixable': False
            },
            'long_segment': {
                'description': '片段内容过长，可能影响合成质量',
                'severity': 'low',
                'fixable': True
            },
            'special_characters': {
                'description': '包含特殊字符或符号',
                'severity': 'medium',
                'fixable': True
            },
            'quoted_content_as_narration': {
                'description': '引号对话内容被标记为旁白',
                'severity': 'medium',
                'fixable': True
            },
            'narration_as_dialogue': {
                'description': '旁白内容被标记为对话',
                'severity': 'medium',
                'fixable': True
            }
            # 🔥 已移除：'inconsistent_voice_type' - 语音类型检测不重要
        }
    
    async def detect_chapter_issues(self, chapter_id: int, enable_ai_detection: bool = True) -> DetectionResult:
        """检测章节问题"""
        db = next(get_db())
        try:
            # 获取章节和合成计划
            chapter = db.query(BookChapter).filter(BookChapter.id == chapter_id).first()
            if not chapter:
                raise ValueError(f"Chapter {chapter_id} not found")
            
            analysis_result = db.query(AnalysisResult).filter(
                AnalysisResult.chapter_id == chapter_id
            ).order_by(AnalysisResult.created_at.desc()).first()
            
            if not analysis_result:
                return DetectionResult(
                    chapter_id=chapter_id,
                    total_issues=0,
                    issues_by_severity={'low': 0, 'medium': 0, 'high': 0},
                    fixable_issues=0,
                    issues=[],
                    detection_time=self._get_current_time()
                )
            
            # 🔥 修复：优先读取用户编辑后的数据
            segments = []
            
            # 首先尝试从final_config读取最新的用户编辑数据
            if analysis_result.final_config:
                try:
                    import json
                    final_config_data = json.loads(analysis_result.final_config)
                    if 'synthesis_json' in final_config_data and 'synthesis_plan' in final_config_data['synthesis_json']:
                        segments = final_config_data['synthesis_json']['synthesis_plan']
                        logger.info(f"[智能检测] 使用用户编辑后的数据进行检测，段落数: {len(segments)}")
                except Exception as e:
                    logger.warning(f"[智能检测] 解析final_config失败: {str(e)}")
            
            # 如果没有用户编辑数据，使用原始synthesis_plan
            if not segments and analysis_result.synthesis_plan and 'synthesis_plan' in analysis_result.synthesis_plan:
                segments = analysis_result.synthesis_plan['synthesis_plan']
                logger.info(f"[智能检测] 使用原始synthesis_plan数据进行检测，段落数: {len(segments)}")
            
            # 如果仍然没有数据，返回空结果
            if not segments:
                logger.warning(f"[智能检测] 章节 {chapter_id} 没有可用的合成计划数据")
                return DetectionResult(
                    chapter_id=chapter_id,
                    total_issues=0,
                    issues_by_severity={'low': 0, 'medium': 0, 'high': 0},
                    fixable_issues=0,
                    issues=[],
                    detection_time=self._get_current_time()
                )
            
            issues = []
            
            # 🔍 调试：显示段落数据详情
            logger.info(f"[智能检测] 准备检测章节 {chapter_id}，段落数: {len(segments)}")
            if segments:
                # 显示前3个段落的示例数据
                for i, segment in enumerate(segments[:3]):
                    logger.info(f"[智能检测] 段落{i+1}示例: text='{segment.get('text', '')[:50]}...', "
                               f"speaker='{segment.get('speaker', '')}', "
                               f"text_type='{segment.get('text_type', '')}'")
            
            # 基础检测
            basic_issues = self._detect_basic_issues(segments)
            issues.extend(basic_issues)
            logger.info(f"[智能检测] 基础检测完成，发现 {len(basic_issues)} 个问题")
            
            # AI增强检测（如果启用）
            if enable_ai_detection:
                logger.info(f"[智能检测] 开始AI增强检测...")
                ai_issues = await self._detect_ai_issues(segments)
                issues.extend(ai_issues)
                logger.info(f"[智能检测] AI增强检测完成，发现 {len(ai_issues)} 个问题")
            else:
                logger.info(f"[智能检测] AI增强检测已禁用")
            
            # 统计结果
            issues_by_severity = {'low': 0, 'medium': 0, 'high': 0}
            fixable_issues = 0
            
            for issue in issues:
                issues_by_severity[issue.severity] += 1
                if issue.fixable:
                    fixable_issues += 1
            
            logger.info(f"[智能检测] 章节 {chapter_id} 检测完成，总计发现 {len(issues)} 个问题")
            
            return DetectionResult(
                chapter_id=chapter_id,
                total_issues=len(issues),
                issues_by_severity=issues_by_severity,
                fixable_issues=fixable_issues,
                issues=issues,
                detection_time=self._get_current_time()
            )
            
        finally:
            db.close()
    
    def _detect_basic_issues(self, segments: List[Dict[str, Any]]) -> List[DetectionIssue]:
        """基础问题检测"""
        issues = []
        
        for index, segment in enumerate(segments):
            text = segment.get('text', '').strip()
            # 🔥 修复：使用正确的字段名
            character = segment.get('speaker', '') or segment.get('character', '')  # 优先使用speaker，fallback到character
            voice_type = segment.get('voice_type', '')
            text_type = segment.get('text_type', 'dialogue')
            
            # 检测空内容
            if not text:
                issues.append(DetectionIssue(
                    issue_type='empty_content',
                    severity='medium',
                    segment_index=index,
                    description='片段内容为空',
                    suggestion='请添加文本内容或删除此片段',
                    context=f'片段 {index + 1}',
                    fixable=False
                ))
                continue
            
            # 检测过长片段
            if len(text) > 500:
                issues.append(DetectionIssue(
                    issue_type='long_segment',
                    severity='low',
                    segment_index=index,
                    description=f'片段内容过长（{len(text)}字符）',
                    suggestion='建议将长片段分割为多个较短的片段',
                    context=text[:50] + '...',
                    fixable=True,
                    fix_data={'action': 'split_segment', 'max_length': 200}
                ))
            
            # 检测特殊字符
            special_chars = re.findall(r'[#@$%^&*()_+=\[\]{}|;:,.<>?/~`]', text)
            if special_chars:
                issues.append(DetectionIssue(
                    issue_type='special_characters',
                    severity='medium',
                    segment_index=index,
                    description=f'包含特殊字符: {", ".join(set(special_chars))}',
                    suggestion='建议移除或替换特殊字符',
                    context=text[:100],
                    fixable=True,
                    fix_data={'action': 'clean_special_chars', 'chars': special_chars}
                ))
            
            # 检测角色配置问题
            if text_type == 'dialogue' and not character:
                issues.append(DetectionIssue(
                    issue_type='character_mismatch',
                    severity='high',
                    segment_index=index,
                    description='对话片段未指定角色',
                    suggestion='请为对话片段指定说话角色',
                    context=text[:50],
                    fixable=True,
                    fix_data={'action': 'assign_character'}
                ))
            
            # 🔥 已移除语音类型检测：voice_type不影响TTS合成
            # 用户反馈：语音类型检测不重要，已完全移除
        
        return issues
    
    async def _detect_ai_issues(self, segments: List[Dict[str, Any]]) -> List[DetectionIssue]:
        """AI增强检测"""
        issues = []
        
        # 🔥 优化：使用编程规则进行初步筛选，只对可疑段落使用大模型
        logger.info(f"[AI增强检测] 开始智能检测 {len(segments)} 个段落")
        
        # 初始化编程规则检测器（用于快速预筛选）
        try:
            from app.detectors.character_detectors import ProgrammaticCharacterDetector
            rule_detector = ProgrammaticCharacterDetector()
            logger.info(f"[AI增强检测] 编程规则检测器初始化成功")
        except Exception as e:
            logger.warning(f"[AI增强检测] 编程规则检测器初始化失败: {str(e)}")
            rule_detector = None
        
        # 大模型检测器（仅在需要时初始化）
        mixed_text_detector = None
        suspicious_segments = []
        
        for index, segment in enumerate(segments):
            text = segment.get('text', '').strip()
            text_type = segment.get('text_type', 'dialogue')
            
            if not text:
                continue
            
            # �� 第一步：使用编程规则快速筛选可疑段落  
            if rule_detector and len(text) > 15:  # 只检测足够长的文本
                # 🔥 降低门槛：只要有一定特征就交给大模型判断
                
                # 1. 有角色动作描述（扩展匹配范围）
                has_speaker_action = re.search(r'([一-龯]{2,6})[^，。！？]*?[说道讲叫喊问答回复表示抬举点头摇头看着轻声道声道问道][:：]', text)
                
                # 2. 包含引号对话
                has_quotes = '"' in text or '"' in text or '"' in text
                
                # 3. 包含动作或场景描述
                has_narration_content = any(word in text for word in ['只见', '此时', '突然', '然后', '他们', '抬起', '看着', '等着', '意识到', '一起', '向', '扑', '都', '血红', '眼睛', '尸体', '放脱', '点头', '摇头', '走向', '愉快', '聊着'])
                
                # 4. 文本足够长可能包含多种内容（提高阈值）
                is_potentially_mixed = len(text) > 40
                
                # 🔍 调试信息
                logger.info(f"[AI增强检测] 段落{index+1}特征: 长度={len(text)}, "
                           f"角色动作={bool(has_speaker_action)}, 引号={has_quotes}, "
                           f"场景描述={has_narration_content}, 潜在混合={is_potentially_mixed}, "
                           f"文本='{text[:50]}...'")
                
                # 🎯 严格准入逻辑：只检测明显的混合文本，大幅减少LLM调用
                should_check = False
                reason = ""
                
                # 🚫 快速排除：明显不需要检测的情况
                if len(text) < 20:
                    should_check = False
                    reason = "文本过短"
                
                # 🔥 核心策略：同时包含对话标记和叙述内容的混合文本
                elif has_quotes and has_speaker_action and len(text) > 30:
                    # 必须同时有：引号 + 说话动作 + 足够长度
                    should_check = True
                    reason = "引号+说话动作+较长文本"
                
                # 🔥 明确的混合标志：包含完整的对话格式
                elif (re.search(r'[说道喊叫问答回复表示轻声道声道问道][:：]', text)) and has_narration_content:
                    # 必须同时有：对话标记 + 叙述词汇
                    should_check = True
                    reason = "对话标记+叙述内容"
                
                # 🔥 长文本且包含多种内容标志
                elif len(text) > 80 and has_quotes and has_narration_content:
                    # 必须同时有：较长 + 引号 + 叙述内容
                    should_check = True
                    reason = "长文本+引号+叙述内容"
                
                # 🔥 复杂混合：多个动作+引号+足够长度
                elif (len([word for word in ['抬起', '看着', '走向', '聊着', '点头', '摇头', '推开', '闯出', '扑过'] if word in text]) >= 2 
                      and has_quotes and len(text) > 35):
                    should_check = True
                    reason = "多个动作+引号+长文本"
                
                # 🔥 新增：包含引号且有叙述内容的中等长度文本
                elif has_quotes and has_narration_content and len(text) > 30:
                    should_check = True
                    reason = "引号+叙述内容+中等长度"
                
                # 🔥 新增：包含对话动作的较长文本
                elif has_speaker_action and len(text) > 40:
                    should_check = True
                    reason = "对话动作+较长文本"
                
                # 🔥 新增：包含对话标记的文本（降低门槛）
                elif re.search(r'[说道喊叫问答回复表示轻声道声道问道][:：]', text) and len(text) > 15:
                    should_check = True
                    reason = "对话标记+基本长度"
                
                if should_check:
                    suspicious_segments.append((index, text))
                    logger.info(f"[AI增强检测] ✅ 段落{index+1}标记为可疑 ({reason}): '{text[:50]}...'")
                else:
                    logger.info(f"[AI增强检测] ❌ 段落{index+1}未标记为可疑: 不符合任何检测策略")
        
        # 🔥 第二步：只对可疑段落使用大模型深度分析
        if suspicious_segments:
            logger.info(f"[AI增强检测] 发现 {len(suspicious_segments)} 个可疑段落，启用大模型深度分析 (共{len(segments)}个段落，筛选率：{len(suspicious_segments)/len(segments)*100:.1f}%)")
            
            try:
                from app.detectors.ollama_character_detector import OllamaCharacterDetector
                mixed_text_detector = OllamaCharacterDetector()
                logger.info(f"[AI增强检测] 大模型检测器初始化成功")
            except Exception as e:
                logger.warning(f"[AI增强检测] 大模型检测器初始化失败，跳过深度分析: {str(e)}")
            
            if mixed_text_detector:
                import time
                start_time = time.time()
                processed_count = 0
                
                for index, text in suspicious_segments:
                    try:
                        # 使用大模型分析这个可疑段落
                        analysis_result = await mixed_text_detector._analyze_single_text(text)
                        detected_segments = analysis_result.get('segments', [])
                        processed_count += 1
                        
                        # 如果检测出多个段落，说明这是混合文本
                        if len(detected_segments) > 1:
                            issues.append(DetectionIssue(
                                issue_type='segment_split_needed',
                                severity='medium',
                                segment_index=index,
                                description=f'检测到混合文本，建议拆分为 {len(detected_segments)} 个段落',
                                suggestion='点击查看拆分建议',
                                context=text[:100] + ('...' if len(text) > 100 else ''),
                                fixable=True,
                                fix_data={
                                    'action': 'split_segment', 
                                    'suggested_segments': detected_segments
                                }
                            ))
                            logger.info(f"[AI增强检测] 发现混合文本 (段落{index+1}): {len(detected_segments)}个子段落")
                        
                    except Exception as e:
                        logger.warning(f"[AI增强检测] 段落{index+1}深度分析失败: {str(e)}")
                
                # 性能统计
                end_time = time.time()
                total_time = end_time - start_time
                avg_time = total_time / processed_count if processed_count > 0 else 0
                logger.info(f"[AI增强检测] 大模型分析完成，处理{processed_count}个段落，耗时{total_time:.2f}秒，平均{avg_time:.2f}秒/段落")
        
        # 原有的基础AI检测逻辑
        for index, segment in enumerate(segments):
            text = segment.get('text', '').strip()
            text_type = segment.get('text_type', 'dialogue')
            
            if not text:
                continue
                
            # 检测引号内容但标记为旁白
            if text_type == 'narration' and ('"' in text or '"' in text or '"' in text):
                quote_content = re.search(r'["""]([^"""]*?)["""]', text)
                if quote_content and len(quote_content.group(1).strip()) > 5:
                    issues.append(DetectionIssue(
                        issue_type='quoted_content_as_narration',
                        severity='medium',
                        segment_index=index,
                        description='包含引号对话内容但被标记为旁白',
                        suggestion='建议将引号内容分离为独立的对话片段',
                        context=quote_content.group(1)[:50],
                        fixable=True,
                        fix_data={
                            'action': 'split_quoted_content',
                            'quoted_text': quote_content.group(1)
                        }
                    ))
            
            # 检测旁白内容但标记为对话
            if text_type == 'dialogue' and not any(char in text for char in ['"', '"', '"', '说', '道', '问', '答']):
                # 简单的旁白特征检测
                narration_indicators = ['只见', '突然', '此时', '然后', '接着', '于是', '这时']
                if any(indicator in text for indicator in narration_indicators):
                    issues.append(DetectionIssue(
                        issue_type='narration_as_dialogue',
                        severity='medium',
                        segment_index=index,
                        description='疑似旁白内容被标记为对话',
                        suggestion='建议将此片段标记为旁白',
                        context=text[:50],
                        fixable=True,
                        fix_data={'action': 'change_to_narration'}
                    ))
        
        logger.info(f"[AI增强检测] 智能检测完成，发现 {len([i for i in issues if i.issue_type == 'segment_split_needed'])} 个混合文本问题")
        return issues
    
    async def detect_single_segment_issues(self, segment_text: str, segment_index: int = 0) -> List[DetectionIssue]:
        """🔥 单段落智能检测 - 专门用于拆分混合文本"""
        issues = []
        
        try:
            # 🔥 修复：优先使用大模型进行单段落检测
            try:
                from app.detectors.ollama_character_detector import OllamaCharacterDetector
                character_detector = OllamaCharacterDetector()
                logger.info(f"[单段落检测] 使用Ollama AI进行智能检测")
                
                # 使用大模型分析单段落
                analysis_result = await character_detector._analyze_single_text(segment_text)
                detected_segments = analysis_result.get('segments', [])
                
            except Exception as e:
                logger.warning(f"[单段落检测] 大模型检测失败，回退到编程规则: {str(e)}")
                # 回退到编程规则检测器
                from app.detectors.character_detectors import ProgrammaticCharacterDetector
                character_detector = ProgrammaticCharacterDetector()
                analysis_result = character_detector.analyze_text_segments(segment_text)
                detected_segments = analysis_result.get('segments', [])
            
            # 如果检测出多个段落，说明需要拆分
            if len(detected_segments) > 1:
                issues.append(DetectionIssue(
                    issue_type='segment_split_needed',
                    severity='medium',
                    segment_index=segment_index,
                    description=f'检测到混合文本，建议拆分为 {len(detected_segments)} 个段落',
                    suggestion='点击查看拆分建议',
                    context=segment_text[:100] + ('...' if len(segment_text) > 100 else ''),
                    fixable=True,
                    fix_data={
                        'action': 'split_segment',
                        'suggested_segments': detected_segments
                    }
                ))
            
            logger.info(f"[单段落检测] 检测段落长度: {len(segment_text)}, 检测到段落数: {len(detected_segments)}, {'需要拆分' if len(detected_segments) > 1 else '无需拆分'}")
            
        except Exception as e:
            logger.error(f"[单段落检测] 检测失败: {str(e)}")
        
        return issues
    
    async def apply_fixes(self, chapter_id: int, issue_indices: Optional[List[int]] = None) -> Dict[str, Any]:
        """应用修复"""
        db = next(get_db())
        try:
            # 获取检测结果
            detection_result = await self.detect_chapter_issues(chapter_id, enable_ai_detection=True)
            
            if not detection_result.issues:
                return {'success': True, 'message': '没有发现需要修复的问题', 'fixed_count': 0}
            
            # 获取合成计划
            analysis_result = db.query(AnalysisResult).filter(
                AnalysisResult.chapter_id == chapter_id
            ).first()
            
            if not analysis_result or not analysis_result.synthesis_plan or 'synthesis_plan' not in analysis_result.synthesis_plan:
                return {'success': False, 'message': '未找到合成计划'}
            
            segments = analysis_result.synthesis_plan['synthesis_plan'].copy()
            fixed_count = 0
            
            # 确定要修复的问题
            issues_to_fix = detection_result.issues
            if issue_indices is not None:
                issues_to_fix = [issue for i, issue in enumerate(detection_result.issues) if i in issue_indices]
            
            # 按片段索引排序，从后往前处理（避免索引变化）
            issues_to_fix.sort(key=lambda x: x.segment_index, reverse=True)
            
            for issue in issues_to_fix:
                if not issue.fixable or not issue.fix_data:
                    continue
                
                success = self._apply_single_fix(segments, issue)
                if success:
                    fixed_count += 1
            
            # 更新合成计划
            analysis_result.synthesis_plan['synthesis_plan'] = segments
            db.commit()
            
            return {
                'success': True,
                'message': f'成功修复 {fixed_count} 个问题',
                'fixed_count': fixed_count
            }
            
        except Exception as e:
            db.rollback()
            return {'success': False, 'message': f'修复失败: {str(e)}'}
        finally:
            db.close()
    
    def _apply_single_fix(self, segments: List[Dict[str, Any]], issue: DetectionIssue) -> bool:
        """应用单个修复"""
        try:
            segment_index = issue.segment_index
            if segment_index >= len(segments):
                return False
            
            fix_data = issue.fix_data
            action = fix_data.get('action')
            
            if action == 'clean_special_chars':
                # 清理特殊字符
                text = segments[segment_index]['text']
                for char in fix_data.get('chars', []):
                    text = text.replace(char, '')
                segments[segment_index]['text'] = text.strip()
                return True
            
            elif action == 'split_segment':
                # 分割长片段
                text = segments[segment_index]['text']
                max_length = fix_data.get('max_length', 200)
                
                if len(text) > max_length:
                    # 简单按句号分割
                    sentences = re.split(r'[。！？]', text)
                    new_segments = []
                    current_text = ''
                    
                    for sentence in sentences:
                        if len(current_text + sentence) > max_length and current_text:
                            # 创建新片段
                            new_segment = segments[segment_index].copy()
                            new_segment['text'] = current_text.strip()
                            new_segments.append(new_segment)
                            current_text = sentence
                        else:
                            current_text += sentence + '。' if sentence else ''
                    
                    if current_text.strip():
                        new_segment = segments[segment_index].copy()
                        new_segment['text'] = current_text.strip()
                        new_segments.append(new_segment)
                    
                    # 替换原片段
                    if new_segments:
                        segments[segment_index:segment_index+1] = new_segments
                        return True
            
            elif action == 'change_to_narration':
                # 改为旁白
                segments[segment_index]['text_type'] = 'narration'
                segments[segment_index]['character'] = ''
                segments[segment_index]['voice_type'] = ''
                return True
            
            elif action == 'split_quoted_content':
                # 分离引号内容
                text = segments[segment_index]['text']
                quoted_text = fix_data.get('quoted_text', '')
                
                if quoted_text in text:
                    # 分离为两个片段
                    before_quote = text.split(quoted_text)[0].strip()
                    
                    new_segments = []
                    
                    # 旁白部分
                    if before_quote:
                        narration_segment = segments[segment_index].copy()
                        narration_segment['text'] = before_quote
                        narration_segment['text_type'] = 'narration'
                        narration_segment['character'] = ''
                        narration_segment['voice_type'] = ''
                        new_segments.append(narration_segment)
                    
                    # 对话部分
                    dialogue_segment = segments[segment_index].copy()
                    dialogue_segment['text'] = quoted_text
                    dialogue_segment['text_type'] = 'dialogue'
                    new_segments.append(dialogue_segment)
                    
                    # 替换原片段
                    segments[segment_index:segment_index+1] = new_segments
                    return True
            
            return False
            
        except Exception as e:
            print(f"Fix application error: {e}")
            return False
    
    def _get_current_time(self) -> str:
        """获取当前时间字符串"""
        from datetime import datetime
        return datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    def get_issue_statistics(self, issues: List[DetectionIssue]) -> Dict[str, Any]:
        """获取问题统计信息"""
        stats = {
            'total': len(issues),
            'by_severity': {'low': 0, 'medium': 0, 'high': 0},
            'by_type': {},
            'fixable': 0
        }
        
        for issue in issues:
            stats['by_severity'][issue.severity] += 1
            stats['by_type'][issue.issue_type] = stats['by_type'].get(issue.issue_type, 0) + 1
            if issue.fixable:
                stats['fixable'] += 1
        
        return stats
    
    def _get_current_time(self) -> str:
        """获取当前时间字符串"""
        from datetime import datetime
        return datetime.utcnow().isoformat()
        
    def detect_issues(self, chapter: BookChapter, use_ai: bool = True) -> Dict[str, Any]:
        """检测章节问题
        
        Args:
            chapter: 章节对象
            use_ai: 是否使用AI增强检测
            
        Returns:
            Dict[str, Any]: 检测结果字典
        """
        try:
            # 获取分析结果
            synthesis_plan = self._get_synthesis_plan(chapter)
            if not synthesis_plan:
                return {
                    "success": False,
                    "error": "章节未完成分析或合成计划不存在"
                }
                
            segments = synthesis_plan.get('synthesis_plan', [])
            if not segments:
                return {
                    "success": False,
                    "error": "合成计划为空"
                }
            
            # 执行基础检测
            basic_issues = self._detect_basic_issues(segments)
            
            # 执行AI增强检测
            ai_issues = []
            if use_ai:
                ai_issues = self._detect_ai_issues(segments)
            
            # 合并问题列表
            all_issues = basic_issues + ai_issues
            
            # 统计问题
            stats = self.get_issue_statistics(all_issues)
            
            # 转换为字典格式返回
            issues_dict = [{
                "issue_type": issue.issue_type,
                "severity": issue.severity,
                "segment_index": issue.segment_index,
                "description": issue.description,
                "suggestion": issue.suggestion,
                "auto_fixable": hasattr(issue, 'auto_fixable') and issue.auto_fixable
            } for issue in all_issues]
            
            return {
                "success": True,
                "issues": issues_dict,
                "stats": stats
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
            
    def _get_synthesis_plan(self, chapter: BookChapter) -> Optional[Dict[str, Any]]:
        """获取章节的合成计划"""
        db = next(get_db())
        try:
            analysis_result = db.query(AnalysisResult).filter(
                AnalysisResult.chapter_id == chapter.id
            ).first()
            
            if analysis_result and analysis_result.synthesis_plan:
                return analysis_result.synthesis_plan
            return None
        finally:
            db.close()
            
    def auto_fix_issues(self, segments: List[Dict[str, Any]], issues: List[DetectionIssue]) -> tuple:
        """自动修复检测到的问题
        
        Args:
            segments: 合成计划片段
            issues: 检测到的问题列表
            
        Returns:
            tuple: (修复后的片段, 修复日志)
        """
        fixed_segments = segments.copy()
        fix_logs = []
        
        # 按片段索引排序，从后往前处理（避免索引变化）
        fixable_issues = [issue for issue in issues if hasattr(issue, 'auto_fixable') and issue.auto_fixable]
        fixable_issues.sort(key=lambda x: x.segment_index, reverse=True)
        
        for issue in fixable_issues:
            try:
                segment_index = issue.segment_index
                if segment_index >= len(fixed_segments):
                    continue
                
                # 根据问题类型应用不同的修复
                if issue.issue_type == 'special_characters':
                    # 清理特殊字符
                    text = fixed_segments[segment_index]['text']
                    special_chars = re.findall(r'[#@$%^&*()_+=\[\]{}|;:,.<>?/~`]', text)
                    for char in special_chars:
                        text = text.replace(char, '')
                    fixed_segments[segment_index]['text'] = text.strip()
                    fix_logs.append(f"已清理片段 {segment_index + 1} 中的特殊字符")
                
                elif issue.issue_type == 'long_segment':
                    # 分割长片段
                    text = fixed_segments[segment_index]['text']
                    max_length = 200
                    
                    if len(text) > max_length:
                        # 简单按句号分割
                        sentences = re.split(r'[。！？]', text)
                        new_segments = []
                        current_text = ''
                        
                        for sentence in sentences:
                            if len(current_text + sentence) > max_length and current_text:
                                # 创建新片段
                                new_segment = fixed_segments[segment_index].copy()
                                new_segment['text'] = current_text.strip()
                                new_segments.append(new_segment)
                                current_text = sentence
                            else:
                                current_text += sentence + '。' if sentence else ''
                        
                        if current_text.strip():
                            new_segment = fixed_segments[segment_index].copy()
                            new_segment['text'] = current_text.strip()
                            new_segments.append(new_segment)
                        
                        # 替换原片段
                        if new_segments:
                            fixed_segments[segment_index:segment_index+1] = new_segments
                            fix_logs.append(f"已将片段 {segment_index + 1} 分割为 {len(new_segments)} 个片段")
                
                elif issue.issue_type == 'narration_as_dialogue':
                    # 将对话改为旁白
                    fixed_segments[segment_index]['text_type'] = 'narration'
                    fixed_segments[segment_index]['character'] = ''
                    fixed_segments[segment_index]['voice_type'] = ''
                    fix_logs.append(f"已将片段 {segment_index + 1} 从对话改为旁白")
                
            except Exception as e:
                fix_logs.append(f"修复片段 {segment_index + 1} 时出错: {str(e)}")
        
        return fixed_segments, fix_logs
    
    def _get_current_time(self) -> str:
        """获取当前时间字符串"""
        from datetime import datetime
        return datetime.now().isoformat()