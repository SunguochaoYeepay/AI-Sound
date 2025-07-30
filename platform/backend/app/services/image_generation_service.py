"""
图片生成服务
基于书籍智能准备结果生成配图
"""

import logging
import json
import re
import asyncio
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
import os

from app.models import (
    ImageGenerationTask, ImageGenerationPreset, BookChapter, 
    AnalysisResult, ImageGenerationTask
)
from app.clients.comfyui_client import ComfyUIClient
from app.utils.exceptions import ServiceException

logger = logging.getLogger(__name__)


class ImageGenerationService:
    """图片生成服务"""
    
    def __init__(self, db: Session):
        self.db = db
        self.comfyui_client = ComfyUIClient()
    
    async def create_image_generation_tasks_from_chapter(
        self, 
        chapter_id: int,
        analysis_result_id: Optional[int] = None,
        generation_config: Dict = None
    ) -> List[Dict]:
        """从章节智能准备结果创建图片生成任务"""
        
        try:
            # 1. 获取章节数据
            chapter = self.db.query(BookChapter).filter(BookChapter.id == chapter_id).first()
            if not chapter:
                raise ServiceException(f"章节 {chapter_id} 不存在")
            
            # 2. 获取分析结果
            if analysis_result_id:
                analysis_result = self.db.query(AnalysisResult).filter(
                    AnalysisResult.id == analysis_result_id
                ).first()
            else:
                # 获取最新的分析结果
                analysis_result = self.db.query(AnalysisResult).filter(
                    AnalysisResult.chapter_id == chapter_id
                ).order_by(AnalysisResult.created_at.desc()).first()
            
            if not analysis_result:
                raise ServiceException(f"章节 {chapter_id} 没有可用的分析结果")
            
            # 3. 解析分析结果
            analysis_data = analysis_result.get_analysis_data()
            segments = analysis_data.get('segments', [])
            
            # 4. 🔥 新增：获取角色一致性配置
            character_consistency = generation_config.get('character_consistency', {}) if generation_config else {}
            selected_character = None
            
            if character_consistency.get('enabled') and character_consistency.get('selectedCharacterId'):
                from app.models.character import Character
                selected_character = self.db.query(Character).filter(
                    Character.id == character_consistency['selectedCharacterId']
                ).first()
                
                logger.info(f"🎭 启用角色一致性: {selected_character.name if selected_character else '角色未找到'}")
            
            # 5. 筛选适合生成图片的段落
            image_worthy_segments = []
            for segment in segments:
                if self._is_segment_image_worthy(segment):
                    # 🔥 新增：为每个段落添加角色信息
                    if selected_character:
                        enhanced_segment = self._enhance_segment_with_character(segment, selected_character, character_consistency.get('weight', 0.6))
                        image_worthy_segments.append(enhanced_segment)
                    else:
                        image_worthy_segments.append(segment)
            
            logger.info(f"从 {len(segments)} 个段落中筛选出 {len(image_worthy_segments)} 个适合生成图片的段落")
            
            # 6. 创建图片生成任务
            created_tasks = []
            for i, segment in enumerate(image_worthy_segments):
                task_data = {
                    'chapter_id': chapter_id,
                    'analysis_result_id': analysis_result.id,
                    'segment_index': segment.get('order', i),
                    'segment_text': segment.get('text', ''),
                    'segment_type': segment.get('text_type', 'narration'),
                    'prompt': self._generate_image_prompt(segment, chapter, generation_config),
                    'negative_prompt': generation_config.get('negative_prompt', '') if generation_config else '',
                    'generation_config': generation_config or {},
                    'status': 'pending',
                    'character_consistency_enabled': character_consistency.get('enabled', False),
                    'character_id': selected_character.id if selected_character else None
                }
                
                # 创建任务记录
                task = ImageGenerationTask(
                    chapter_id=chapter_id,
                    analysis_result_id=analysis_result.id,
                    segment_index=task_data['segment_index'],
                    segment_text=task_data['segment_text'][:1000],  # 限制长度
                    segment_type=task_data['segment_type'],
                    prompt=task_data['prompt'][:2000],  # 限制长度
                    negative_prompt=task_data['negative_prompt'][:1000],
                    generation_config=task_data['generation_config'],
                    status='pending'
                )
                
                self.db.add(task)
                created_tasks.append(task_data)
            
            self.db.commit()
            logger.info(f"成功创建 {len(created_tasks)} 个图片生成任务")
            
            return created_tasks
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"创建图片生成任务失败: {str(e)}")
            raise ServiceException(f"创建图片生成任务失败: {str(e)}")
    
    def _filter_segments_for_image_generation(self, segments: List[Dict]) -> List[Tuple[int, Dict]]:
        """筛选适合生成图片的段落"""
        suitable_segments = []
        
        for index, segment in enumerate(segments):
            text = segment.get('text', '').strip()
            text_type = segment.get('text_type', 'dialogue')
            speaker = segment.get('speaker', '')
            
            # 跳过过短的文本 (降低长度要求)
            if len(text) < 10:
                continue
            
            # 优先选择叙述性段落和场景描述 (修复类型匹配问题)
            if text_type in ['narrative', 'description', 'scene', 'narration']:
                suitable_segments.append((index, segment))
                continue
            
            # 检查是否包含场景描述关键词 (扩展关键词列表)
            scene_keywords = [
                # 原有关键词
                '只见', '此时', '突然', '眼前', '四周', '远处', '天空', '大地', '山峰', '森林',
                '城堡', '宫殿', '房间', '街道', '广场', '花园', '湖泊', '河流', '海边',
                '夜晚', '黎明', '黄昏', '月光', '阳光', '星空', '雪花', '雨滴', '雾气',
                # 新增关键词 - 建筑和场所
                '教室', '图书馆', '学校', '办公室', '客厅', '卧室', '厨房', '餐厅', '商店', '超市',
                '医院', '银行', '公园', '车站', '机场', '酒店', '咖啡馆', '餐厅', '商场', '电影院',
                # 新增关键词 - 时间和天气
                '早上', '中午', '下午', '傍晚', '晚上', '深夜', '春天', '夏天', '秋天', '冬天',
                '晴天', '阴天', '雨天', '雪天', '风', '雷', '闪电',
                # 新增关键词 - 位置描述
                '里面', '外面', '上面', '下面', '前面', '后面', '左边', '右边', '旁边', '中间',
                '角落', '窗边', '门口', '楼上', '楼下', '地上', '桌上', '床上'
            ]
            
            if any(keyword in text for keyword in scene_keywords):
                suitable_segments.append((index, segment))
                continue
            
            # 检查是否包含动作描述（可能形成画面）(扩展动作关键词)
            action_keywords = [
                # 原有关键词
                '走向', '奔跑', '飞翔', '站在', '坐在', '躺在', '望着', '眺望', 
                '举起', '挥动', '伸出', '指向', '拥抱', '亲吻', '战斗', '追逐',
                # 新增动作关键词 - 基本动作
                '走', '跑', '跳', '爬', '坐', '站', '躺', '蹲', '弯腰', '转身', '回头',
                '抬头', '低头', '点头', '摇头', '摆手', '招手', '挥手', '握手',
                # 新增动作关键词 - 表情动作
                '笑', '哭', '笑容', '微笑', '大笑', '皱眉', '瞪眼', '眨眼', '闭眼', '张嘴',
                # 新增动作关键词 - 日常动作
                '吃', '喝', '看', '听', '说', '读', '写', '画', '唱', '跳舞', '打字',
                '开门', '关门', '开窗', '关窗', '打开', '关闭', '拿起', '放下', '递给',
                # 新增动作关键词 - 移动
                '进入', '走出', '离开', '到达', '经过', '穿过', '越过', '跨过', '爬上', '走下'
            ]
            
            if any(keyword in text for keyword in action_keywords):
                suitable_segments.append((index, segment))
                continue
            
            # 检查是否包含人物描述或情绪表达
            character_keywords = [
                '表情', '神情', '脸色', '眼神', '目光', '笑容', '泪水', '汗水',
                '高兴', '开心', '快乐', '兴奋', '惊喜', '满意', '愉快',
                '伤心', '难过', '痛苦', '悲伤', '失望', '沮丧', '绝望',
                '愤怒', '生气', '恼火', '不满', '抱怨', '愤恨',
                '害怕', '恐惧', '紧张', '担心', '焦虑', '不安', '慌张',
                '惊讶', '吃惊', '震惊', '意外', '困惑', '疑惑', '奇怪'
            ]
            
            if any(keyword in text for keyword in character_keywords):
                suitable_segments.append((index, segment))
                continue
            
            # 对于对话，如果长度足够且包含一定的描述性内容，也可以考虑
            if text_type == 'dialogue' and len(text) >= 15:
                # 检查对话中是否包含描述性内容
                description_indicators = [
                    '从前', '曾经', '那时', '当时', '后来', '接着', '然后', '于是',
                    '记得', '想起', '回忆', '描述', '形容', '像', '似乎', '仿佛',
                    '山', '水', '树', '花', '草', '动物', '建筑', '景色', '风景'
                ]
                
                if any(indicator in text for indicator in description_indicators):
                    suitable_segments.append((index, segment))
                    continue
        
        return suitable_segments
    
    async def _create_single_image_generation_task(
        self,
        chapter_id: int,
        analysis_result_id: int,
        segment_index: int,
        segment: Dict,
        generation_config: Dict = None
    ) -> Dict:
        """创建单个图片生成任务"""
        
        # 1. 解析段落信息
        segment_text = segment.get('text', '')
        segment_type = segment.get('text_type', 'narrative')
        speaker = segment.get('speaker', '')
        emotion = segment.get('emotion', '')
        
        # 2. 生成场景描述和提示词
        scene_analysis = await self._analyze_segment_for_image(segment_text, segment_type)
        
        # 3. 获取默认配置
        default_config = generation_config or {}
        preset_id = default_config.get('preset_id')
        preset = None
        if preset_id:
            preset = self.db.query(ImageGenerationPreset).filter(
                ImageGenerationPreset.id == preset_id
            ).first()
        
        # 4. 创建任务记录
        task = ImageGenerationTask(
            chapter_id=chapter_id,
            analysis_result_id=analysis_result_id,
            segment_index=segment_index,
            segment_text=segment_text,
            segment_type=segment_type,
            scene_description=scene_analysis['scene_description'],
            character_info=scene_analysis['character_info'],
            emotional_tone=scene_analysis['emotional_tone'],
            style_keywords=scene_analysis['style_keywords'],
            generated_prompt=scene_analysis['generated_prompt'],
            negative_prompt=scene_analysis['negative_prompt'],
            comfyui_workflow=preset.default_workflow if preset else None,
            generation_params=preset.default_params if preset else default_config.get('params', {}),
            image_width=default_config.get('width', 1024),
            image_height=default_config.get('height', 1024),
            generation_model=default_config.get('model', 'SD1.5'),
            status='pending'
        )
        
        self.db.add(task)
        self.db.flush()  # 获取ID
        
        return {
            'id': task.id,
            'chapter_id': chapter_id,
            'segment_index': segment_index,
            'segment_text': segment_text[:100] + '...' if len(segment_text) > 100 else segment_text,
            'scene_description': scene_analysis['scene_description'],
            'generated_prompt': scene_analysis['generated_prompt'],
            'status': 'pending'
        }
    
    async def _analyze_segment_for_image(self, text: str, segment_type: str) -> Dict[str, Any]:
        """分析段落内容，生成图片描述和提示词"""
        
        try:
            # 使用AI导演系统生成专业提示词
            from app.services.ai_director_service import AIDirectorService
            ai_director = AIDirectorService()
            
            logger.info(f"使用AI导演分析段落: {text[:50]}...")
            result = await ai_director.generate_visual_prompt(text, segment_type, 'cinematic')
            
            if result.get('success', False):
                logger.info(f"AI导演分析成功，生成提示词: {result['generated_prompt'][:100]}...")
                return {
                    'scene_description': result.get('scene_description', ''),
                    'character_info': result.get('character_info', {}),
                    'emotional_tone': result.get('emotional_tone', ''),
                    'style_keywords': result.get('style_keywords', []),
                    'generated_prompt': result.get('generated_prompt', ''),
                    'negative_prompt': result.get('negative_prompt', 'blurry, low quality, distorted, nsfw')
                }
            else:
                logger.warning(f"AI导演分析失败，使用降级方法: {result.get('error', 'Unknown error')}")
                # 如果AI导演失败，使用降级的提示词
                return {
                    'scene_description': result.get('scene_description', ''),
                    'character_info': result.get('character_info', {}),
                    'emotional_tone': result.get('emotional_tone', ''),
                    'style_keywords': result.get('style_keywords', []),
                    'generated_prompt': result.get('generated_prompt', ''),
                    'negative_prompt': result.get('negative_prompt', 'blurry, low quality, distorted, nsfw')
                }
            
        except Exception as e:
            logger.error(f"AI导演服务调用失败: {str(e)}，使用传统方法")
            
            # 降级到原有的简单方法
            analysis = {
                'scene_description': '',
                'character_info': {},
                'emotional_tone': '',
                'style_keywords': [],
                'generated_prompt': '',
                'negative_prompt': 'blurry, low quality, distorted, nsfw'
            }
            
            # 1. 提取场景描述
            scene_description = self._extract_scene_description(text)
            analysis['scene_description'] = scene_description
            
            # 2. 提取角色信息
            character_info = self._extract_character_info(text)
            analysis['character_info'] = character_info
            
            # 3. 分析情感色调
            emotional_tone = self._analyze_emotional_tone(text)
            analysis['emotional_tone'] = emotional_tone
            
            # 4. 提取风格关键词
            style_keywords = self._extract_style_keywords(text, segment_type)
            analysis['style_keywords'] = style_keywords
            
            # 5. 生成简单提示词（比之前稍微改进）
            prompt_parts = []
            
            # 优化的提示词构建
            if '林渊' in text:
                prompt_parts.append('young Chinese man in ancient clothing')
            
            if '胸甲' in text or '汉' in text:
                prompt_parts.append('ancient Chinese armor with Han dynasty insignia')
            
            if '穿越' in text or '突然意识到' in text:
                prompt_parts.append('dramatic moment of realization, shocked expression')
            
            if scene_description:
                prompt_parts.append(scene_description)
            
            if character_info:
                for char_name, char_desc in character_info.items():
                    if char_desc:
                        prompt_parts.append(f"{char_desc}")
            
            if emotional_tone:
                prompt_parts.append(f"mood: {emotional_tone}")
            
            if style_keywords:
                prompt_parts.extend(style_keywords)
            
            # 添加默认的质量标签
            quality_tags = [
                "cinematic lighting", "dramatic scene", "historical accuracy",
                "detailed costume", "professional photography", "high quality", 
                "masterpiece", "best quality", "detailed"
            ]
            prompt_parts.extend(quality_tags)
            
            analysis['generated_prompt'] = ", ".join(prompt_parts)
            
            return analysis
    
    def _extract_scene_description(self, text: str) -> str:
        """从文本中提取场景描述"""
        # 场景关键词映射
        scene_mapping = {
            # 室内场景
            '房间': 'room interior',
            '大厅': 'hall, grand interior',
            '客厅': 'living room',
            '卧室': 'bedroom',
            '书房': 'study room, library',
            '厨房': 'kitchen',
            '庭院': 'courtyard, garden',
            
            # 室外场景  
            '山': 'mountain landscape',
            '湖': 'lake scenery',
            '河': 'river view',
            '森林': 'forest scene',
            '草原': 'grassland, prairie',
            '沙漠': 'desert landscape',
            '海边': 'seaside, coastal',
            '城市': 'urban scene, cityscape',
            '村庄': 'village scene',
            '街道': 'street view',
            
            # 建筑
            '宫殿': 'palace, imperial architecture',
            '寺庙': 'temple, traditional architecture',
            '城楼': 'city tower, fortress',
            '桥': 'bridge architecture',
            
            # 时间和天气
            '黎明': 'dawn, early morning light',
            '日出': 'sunrise, golden hour',
            '正午': 'midday, bright sunlight',
            '黄昏': 'sunset, dusk lighting',
            '夜晚': 'night scene, dark atmosphere',
            '月夜': 'moonlit night',
            '雨': 'rainy weather, wet atmosphere',
            '雪': 'snowy scene, winter atmosphere',
            '雾': 'misty, foggy atmosphere'
        }
        
        # 提取匹配的场景元素
        scene_elements = []
        for keyword, description in scene_mapping.items():
            if keyword in text:
                scene_elements.append(description)
        
        # 如果没有明确的场景关键词，尝试从整体文本推断
        if not scene_elements:
            if any(word in text for word in ['站', '坐', '躺', '走', '跑']):
                scene_elements.append('character scene')
            elif any(word in text for word in ['美丽', '壮观', '华丽']):
                scene_elements.append('beautiful scenery')
            elif any(word in text for word in ['黑暗', '恐怖', '可怕']):
                scene_elements.append('dark atmosphere, dramatic')
        
        return ', '.join(scene_elements) if scene_elements else 'general scene'
    
    def _extract_character_info(self, text: str) -> Dict[str, str]:
        """提取角色信息"""
        # 匹配角色描述的模式
        character_patterns = [
            r'([一-龯]{2,4})[^，。]*?[说道]',  # 角色说话
            r'([一-龯]{2,4})[^，。]*?[走来去站坐]',  # 角色动作
        ]
        
        characters = {}
        for pattern in character_patterns:
            matches = re.findall(pattern, text)
            for char_name in matches:
                if char_name not in characters:
                    characters[char_name] = self._get_character_description(char_name, text)
        
        return characters
    
    def _get_character_description(self, char_name: str, context: str) -> str:
        """根据上下文生成角色描述"""
        # 这里可以从数据库中查询角色的预设描述
        # 暂时返回基础描述
        if '女' in char_name or char_name in ['嫦娥', '西施', '貂蝉']:
            return "beautiful woman, traditional chinese clothing"
        elif '男' in char_name or '君' in char_name:
            return "handsome man, traditional chinese clothing"
        else:
            return "person, traditional chinese clothing"
    
    def _analyze_emotional_tone(self, text: str) -> str:
        """分析情感色调"""
        emotion_keywords = {
            'angry': ['愤怒', '怒', '恼', '气'],
            'sad': ['悲伤', '哭', '泣', '痛苦', '忧'],
            'happy': ['高兴', '开心', '喜悦', '笑', '乐'],
            'peaceful': ['平静', '安静', '宁静', '祥和'],
            'mysterious': ['神秘', '诡异', '奇怪', '诡谲'],
            'romantic': ['浪漫', '温柔', '甜蜜', '情'],
            'epic': ['壮观', '宏伟', '磅礴', '雄伟'],
            'dark': ['黑暗', '阴森', '恐怖', '血腥']
        }
        
        for emotion, keywords in emotion_keywords.items():
            if any(keyword in text for keyword in keywords):
                return emotion
        
        return 'neutral'
    
    def _extract_style_keywords(self, text: str, segment_type: str) -> List[str]:
        """提取风格关键词"""
        style_keywords = []
        
        # 基于时代背景
        if any(word in text for word in ['古代', '朝廷', '皇宫', '江湖']):
            style_keywords.extend(['ancient china', 'traditional architecture'])
        
        # 基于场景类型
        if any(word in text for word in ['山', '峰', '岭']):
            style_keywords.extend(['mountain landscape', 'nature'])
        elif any(word in text for word in ['城', '街', '市']):
            style_keywords.extend(['urban scene', 'architecture'])
        elif any(word in text for word in ['宫', '殿', '楼']):
            style_keywords.extend(['palace', 'grand architecture'])
        
        # 基于时间
        if any(word in text for word in ['夜', '月', '星']):
            style_keywords.extend(['night scene', 'moonlight'])
        elif any(word in text for word in ['日', '阳', '光']):
            style_keywords.extend(['daylight', 'bright'])
        
        # 基于天气
        if any(word in text for word in ['雨', '雪', '雾']):
            style_keywords.append('atmospheric weather')
        
        return style_keywords
    
    async def generate_single_image(self, task_id: int) -> Dict[str, Any]:
        """生成单张图片"""
        
        try:
            # 1. 获取任务信息
            task = self.db.query(ImageGenerationTask).filter(
                ImageGenerationTask.id == task_id
            ).first()
            
            if not task:
                raise ServiceException(f"图片生成任务 {task_id} 不存在")
            
            if task.status not in ['pending', 'failed']:
                raise ServiceException(f"任务 {task_id} 状态为 {task.status}，无法重新生成")
            
            # 2. 更新任务状态
            task.status = 'processing'
            task.started_at = datetime.utcnow()
            self.db.commit()
            
            # 3. 准备生成参数
            comfyui_client = ComfyUIClient()
            
            # 智能选择参考图像（如果启用角色一致性且有可用图像）
            reference_image = None
            generation_params_data = task.generation_params or {}
            
            # 检查是否启用角色一致性
            if generation_params_data.get('enableCharacterConsistency', False):
                # 检查是否有上传的参考图像
                uploaded_reference = generation_params_data.get('referenceImage')
                if uploaded_reference:
                    reference_image = uploaded_reference
                    logger.info(f"任务 {task_id} 启用角色一致性，使用上传的参考图像")
                else:
                    # 未来可以从之前生成的图片中选择作为参考
                    logger.info(f"任务 {task_id} 启用角色一致性，但无可用参考图像，使用纯文本模式")
            
            # FluxKontext参数
            generation_params = {
                'prompt': task.generated_prompt,
                'negative_prompt': task.negative_prompt or "",
                'width': task.image_width or 1024,
                'height': task.image_height or 1024,
                'steps': 20,  # Flux推荐步数
                'cfg': 1.0,   # Flux推荐CFG
                'filename_prefix': f"chapter_{task.chapter_id}_segment_{task.segment_index}",
                'reference_image': reference_image
            }
            
            logger.info(f"开始生成图片，任务ID: {task_id}, 提示词: {generation_params['prompt'][:100]}...")
            
            # 4. 调用FluxKontext生成
            try:
                image_path = await comfyui_client.generate_image(**generation_params)
                
                # 5. 更新任务结果
                task.status = 'completed'
                task.completed_at = datetime.utcnow()
                task.generated_image_url = f"/api/v1/image-generation/files/image_generation/{os.path.basename(image_path)}"
                task.generated_image_path = image_path
                task.generation_progress = 100
                task.error_message = None  # 清空之前的错误信息
                task.generation_model = 'FluxKontext'  # 更新生成模型名称
                
                # 计算生成时间
                if task.started_at:
                    generation_time = (task.completed_at - task.started_at).total_seconds()
                    # 更新生成参数，添加运行时信息
                    current_params = task.generation_params or {}
                    current_params.update({
                        'generation_time': generation_time,
                        'model': 'FluxKontext',
                        'steps': generation_params['steps'],
                        'cfg': generation_params['cfg']
                    })
                    task.generation_params = current_params
                
                self.db.commit()
                
                logger.info(f"图片生成成功，任务ID: {task_id}, 路径: {image_path}")
                
                return {
                    'success': True,
                    'task_id': task_id,
                    'status': 'completed',
                    'image_url': task.generated_image_url,
                    'image_path': image_path,
                    'generation_time': generation_time if task.started_at else 0
                }
                
            except Exception as e:
                # 6. 处理生成失败
                task.status = 'failed'
                task.completed_at = datetime.utcnow()
                task.error_message = str(e)
                task.generation_progress = 0
                self.db.commit()
                
                logger.error(f"图片生成失败，任务ID: {task_id}, 错误: {str(e)}")
                
                return {
                    'success': False,
                    'task_id': task_id,
                    'status': 'failed',
                    'error': str(e),
                    'image_url': None,
                    'image_path': None
                }
                
        except Exception as e:
            logger.error(f"图片生成服务错误，任务ID: {task_id}, 错误: {str(e)}")
            raise ServiceException(f"图片生成失败: {str(e)}")
    
    async def batch_generate_images(self, chapter_id: int, task_ids: List[int] = None) -> Dict:
        """批量生成图片"""
        
        try:
            # 1. 获取要处理的任务
            query = self.db.query(ImageGenerationTask).filter(
                ImageGenerationTask.chapter_id == chapter_id,
                ImageGenerationTask.status == 'pending'
            )
            
            if task_ids:
                query = query.filter(ImageGenerationTask.id.in_(task_ids))
            
            tasks = query.all()
            
            if not tasks:
                return {
                    'total': 0,
                    'completed': 0,
                    'failed': 0,
                    'results': []
                }
            
            logger.info(f"开始批量生成图片，章节ID: {chapter_id}, 任务数: {len(tasks)}")
            
            # 2. 并发生成图片（限制并发数）
            results = []
            completed = 0
            failed = 0
            
            # 分批处理，避免过度并发
            batch_size = 3
            for i in range(0, len(tasks), batch_size):
                batch_tasks = tasks[i:i + batch_size]
                batch_results = await asyncio.gather(
                    *[self.generate_single_image(task.id) for task in batch_tasks],
                    return_exceptions=True
                )
                
                for task, result in zip(batch_tasks, batch_results):
                    if isinstance(result, Exception):
                        failed += 1
                        results.append({
                            'task_id': task.id,
                            'status': 'failed',
                            'error': str(result)
                        })
                    else:
                        completed += 1
                        results.append(result)
            
            logger.info(f"批量生成完成，章节ID: {chapter_id}, 成功: {completed}, 失败: {failed}")
            
            return {
                'total': len(tasks),
                'completed': completed,
                'failed': failed,
                'results': results
            }
            
        except Exception as e:
            logger.error(f"批量生成图片失败，章节ID: {chapter_id}, 错误: {str(e)}")
            raise ServiceException(f"批量生成图片失败: {str(e)}")
    
    def get_chapter_image_generation_status(self, chapter_id: int) -> Dict:
        """获取章节图片生成状态"""
        
        tasks = self.db.query(ImageGenerationTask).filter(
            ImageGenerationTask.chapter_id == chapter_id
        ).all()
        
        status_count = {}
        for task in tasks:
            status = task.status
            status_count[status] = status_count.get(status, 0) + 1
        
        return {
            'chapter_id': chapter_id,
            'total_tasks': len(tasks),
            'status_breakdown': status_count,
            'tasks': [
                {
                    'id': task.id,
                    'chapter_id': task.chapter_id,
                    'segment_index': task.segment_index,
                    'segment_text': task.segment_text,
                    'segment_type': task.segment_type,
                    'scene_description': task.scene_description,
                    'character_info': task.character_info,
                    'emotional_tone': task.emotional_tone,
                    'style_keywords': task.style_keywords,
                    'generated_prompt': task.generated_prompt,
                    'negative_prompt': task.negative_prompt,
                    'status': task.status,
                    'progress': task.progress,
                    'error_message': task.error_message,
                    'generated_image_url': task.generated_image_url,
                    'generated_image_path': task.generated_image_path,
                    'generation_seed': task.generation_seed,
                    'generation_time': task.generation_time,
                    'quality_score': task.quality_score,
                    'user_rating': task.user_rating,
                    'is_approved': task.is_approved,
                    'image_width': task.image_width,
                    'image_height': task.image_height,
                    'generation_model': task.generation_model,
                    'created_at': task.created_at.isoformat() if task.created_at else None,
                    'started_at': task.started_at.isoformat() if task.started_at else None,
                    'completed_at': task.completed_at.isoformat() if task.completed_at else None
                }
                for task in tasks
            ]
        }