"""
小说文本处理模块
提供小说解析、分段和处理功能
"""

import os
import re
import json
import time
import logging
import numpy as np
from typing import Dict, List, Any, Tuple, Optional, Callable

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("processor.novel")

# 导入依赖，处理相对路径问题
try:
    from ..tts.engine import MegaTTSEngine
    from ..utils.audio import save_audio, merge_audio_files
    from ..utils.audio_field import SoundField
    from ..tts.character_voice import CharacterVoiceMapper
except ImportError:
    # 如果是作为主模块运行，相对导入会失败
    import sys
    from pathlib import Path
    sys.path.append(str(Path(__file__).parent.parent))
    from tts.engine import MegaTTSEngine
    from utils.audio import save_audio, merge_audio_files
    from utils.audio_field import SoundField
    from tts.character_voice import CharacterVoiceMapper

try:
    import jieba
except ImportError:
    logger.warning("jieba模块未安装，将影响中文分词功能")
    
    class DummyJieba:
        @staticmethod
        def initialize():
            pass
        
        @staticmethod
        def lcut(text):
            return list(text)
    
    jieba = DummyJieba()

class NovelSegmenter:
    """小说分段器，提供章节和段落分割功能"""
    
    def __init__(
        self, 
        config: Optional[Dict[str, Any]] = None
    ):
        """
        初始化分段器
        
        Args:
            config: 配置参数
                chapter_pattern: 章节匹配模式
                paragraph_min_chars: 段落最小字符数
                max_segment_length: 单段最大处理字符数
        """
        default_config = {
            "chapter_pattern": r"^第[\d一二三四五六七八九十百千]+[章节回]",
            "paragraph_min_chars": 100,
            "max_segment_length": 2000
        }
        
        self.config = default_config
        if config:
            self.config.update(config)
        
        self.chapter_pattern = re.compile(self.config["chapter_pattern"])
        
        # 加载jieba分词
        jieba.initialize()
        logger.info("小说分段器初始化完成")
    
    def load_novel(self, file_path: str) -> str:
        """
        加载小说文件
        
        Args:
            file_path: 小说文件路径
            
        Returns:
            str: 小说内容
        """
        if not os.path.exists(file_path):
            logger.error(f"小说文件不存在: {file_path}")
            raise FileNotFoundError(f"小说文件不存在: {file_path}")
        
        try:
            # 尝试不同编码读取文件
            encodings = ['utf-8', 'gbk', 'gb2312', 'utf-16']
            for encoding in encodings:
                try:
                    with open(file_path, 'r', encoding=encoding) as f:
                        content = f.read()
                    logger.info(f"使用编码 {encoding} 成功读取文件: {file_path}")
                    return content
                except UnicodeDecodeError:
                    continue
                
            # 如果所有编码都失败，使用二进制读取
            logger.warning(f"无法确定文件编码，尝试二进制读取: {file_path}")
            with open(file_path, 'rb') as f:
                content = f.read().decode('utf-8', errors='replace')
            
            return content
            
        except Exception as e:
            logger.error(f"读取小说文件失败: {str(e)}")
            raise
    
    def segment_chapters(self, content: str) -> List[Dict[str, Any]]:
        """
        分割小说章节
        
        Args:
            content: 小说内容
            
        Returns:
            List[Dict[str, Any]]: 章节列表，每个章节为一个字典
                {
                    "title": "章节标题",
                    "content": "章节内容",
                    "paragraphs": ["段落1", "段落2", ...] 
                }
        """
        logger.info("开始分割章节")
        
        # 按行分割
        lines = content.split("\n")
        
        chapters = []
        current_chapter = {"title": "开始", "content": "", "paragraphs": []}
        current_lines = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # 检查是否是新章节
            if self.chapter_pattern.match(line):
                # 保存当前章节
                if current_lines:
                    current_chapter["content"] = "\n".join(current_lines)
                    current_chapter["paragraphs"] = self.segment_paragraphs(current_chapter["content"])
                    chapters.append(current_chapter)
                
                # 创建新章节
                current_chapter = {"title": line, "content": "", "paragraphs": []}
                current_lines = []
                logger.debug(f"发现新章节: {line}")
            else:
                current_lines.append(line)
        
        # 处理最后一个章节
        if current_lines:
            current_chapter["content"] = "\n".join(current_lines)
            current_chapter["paragraphs"] = self.segment_paragraphs(current_chapter["content"]) 
            chapters.append(current_chapter)
        
        logger.info(f"章节分割完成，共 {len(chapters)} 个章节")
        return chapters
    
    def segment_paragraphs(self, content: str) -> List[str]:
        """
        分割章节内容为段落
        
        Args:
            content: 章节内容
            
        Returns:
            List[str]: 段落列表
        """
        # 按照换行符分割段落
        raw_paragraphs = [p.strip() for p in content.split("\n") if p.strip()]
        
        paragraphs = []
        current_paragraph = ""
        min_chars = self.config["paragraph_min_chars"]
        max_chars = self.config["max_segment_length"]
        
        for p in raw_paragraphs:
            # 如果段落很短，合并处理
            if len(current_paragraph) + len(p) < min_chars:
                if current_paragraph:
                    current_paragraph += "\n" + p
                else:
                    current_paragraph = p
                continue
                
            # 如果当前段落已经累积一定长度，就添加到段落列表
            if current_paragraph:
                paragraphs.append(current_paragraph)
                current_paragraph = p
            else:
                current_paragraph = p
                
            # 检查是否需要进一步分段
            if len(current_paragraph) > max_chars:
                # 按句子分割
                segments = self._split_long_paragraph(current_paragraph, max_chars)
                paragraphs.extend(segments)
                current_paragraph = ""
        
        # 处理最后一个段落
        if current_paragraph:
            if len(current_paragraph) > max_chars:
                segments = self._split_long_paragraph(current_paragraph, max_chars)
                paragraphs.extend(segments)
            else:
                paragraphs.append(current_paragraph)
        
        return paragraphs
     
    def _split_long_paragraph(self, text: str, max_length: int) -> List[str]:
        """
        将长段落拆分为短段落
        
        Args:
            text: 长段落文本
            max_length: 最大段落长度
            
        Returns:
            List[str]: 拆分后的段落列表
        """
        # 使用句号、问号、感叹号等作为分割点
        sentence_ends = ['。', '！', '？', '.', '!', '?']
        
        # 先尝试按句子分割
        segments = []
        current_segment = ""
        
        # 按字符遍历
        for char in text:
            current_segment += char
            
            # 如果遇到句子结束符且当前段长度已超过最小值，就结束当前段
            if char in sentence_ends and len(current_segment) >= max_length / 2:
                segments.append(current_segment)
                current_segment = ""
                
            # 如果当前段落超过最大长度，强制断句
            if len(current_segment) >= max_length:
                # 使用jieba分词尝试找到更合适的断句点
                try:
                    words = jieba.lcut(current_segment)
                    # 从后向前找到合适的断句点
                    cut_index = len(current_segment)
                    word_end = 0
                    
                    for word in words:
                        word_end += len(word)
                        if word_end >= max_length * 0.8:  # 找到接近80%长度的位置
                            cut_index = word_end
                            break
                    
                    segments.append(current_segment[:cut_index])
                    current_segment = current_segment[cut_index:]
                except Exception:
                    # 如果分词失败，直接按长度切分
                    segments.append(current_segment[:max_length])
                    current_segment = current_segment[max_length:]
        
        # 处理最后一个段落
        if current_segment:
            segments.append(current_segment)
            
        return segments

    def segment_novel(self, novel_path: str) -> List[Dict[str, Any]]:
        """
        分割整本小说

        Args:
            novel_path: 小说文件路径
            
        Returns:
            List[Dict[str, Any]]: 章节列表
        """
        try:
            # 加载小说内容
            content = self.load_novel(novel_path)
            
            # 分割章节
            chapters = self.segment_chapters(content)
            
            # 每个章节增加索引
            for i, chapter in enumerate(chapters):
                chapter["index"] = i
            
            # 进一步处理章节（提取角色等）
            processed_chapters = self._process_chapters(chapters)
            
            return processed_chapters
            
        except Exception as e:
            logger.error(f"分割小说失败: {str(e)}")
            raise

    def _process_chapters(self, chapters: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        进一步处理章节，提取角色等信息
        
        Args:
            chapters: 章节列表
            
        Returns:
            List[Dict[str, Any]]: 处理后的章节列表
        """
        processed_chapters = []
        
        for chapter in chapters:
            # 提取章节中的角色
            characters = set()
            
            for para in chapter["paragraphs"]:
                chars = self._extract_characters(para)
                characters.update(chars)
            
            # 扩展章节信息
            processed_chapter = {
                **chapter,
                "characters": list(characters)
            }
            
            processed_chapters.append(processed_chapter)
        
        return processed_chapters

    def _extract_characters(self, text: str) -> List[str]:
        """
        从文本中提取可能的角色名
        
        Args:
            text: 文本内容
            
        Returns:
            List[str]: 可能的角色名列表
        """
        # 简单方法：提取引号内的人名（中文引号）
        characters = []
        
        # 匹配"XXX说/道/问/..."的模式
        patterns = [
            r'"([^"]+)"(?:说|道|问|喊|叫|笑道|冷笑道|回答|回应|询问)',
            r'"([^"]+)"(?:说|道|问|喊|叫|笑道|冷笑道|回答|回应|询问)',
            r'「([^」]+)」(?:说|道|问|喊|叫|笑道|冷笑道|回答|回应|询问)',
            r'\'([^\']+)\'(?:说|道|问|喊|叫|笑道|冷笑道|回答|回应|询问)',
            r'"([^"]+)"(?:说|道|问|喊|叫|笑道|冷笑道|回答|回应|询问)'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                # 如果匹配到人名，尝试提取
                if len(match) <= 10:  # 避免提取过长的内容
                    characters.append(match)
        
        return characters


class NovelAudioGenerator:
    """小说语音生成器，将小说转换为有声书"""
    
    def __init__(
        self, 
        config: Optional[Dict[str, Any]] = None,
        tts_engine: Optional[MegaTTSEngine] = None,
        voice_mapping: Optional[Dict[str, str]] = None,
        character_mapper: Optional[CharacterVoiceMapper] = None
    ):
        """
        初始化语音生成器
        
        Args:
            config: 配置参数
            tts_engine: TTS引擎实例
            voice_mapping: 角色音色映射
            character_mapper: 角色声音映射器
        """
        default_config = {
            "output_format": "wav",
            "sample_rate": 24000,
            "with_emotion": True,
            "with_sound_field": False
        }
        
        self.config = default_config
        if config:
            self.config.update(config)
        
        # 初始化TTS引擎
        self.tts_engine = tts_engine
        if self.tts_engine is None:
            logger.info("初始化默认TTS引擎")
            self.tts_engine = MegaTTSEngine()
        
        # 初始化分段器
        self.segmenter = NovelSegmenter()
        
        # 语音映射
        self.voice_mapping = {
            "narrator": "female_mature",  # 旁白
            "character_default": "male_young"  # 默认角色
        }
        if voice_mapping:
            self.voice_mapping.update(voice_mapping)
            
        # 角色声音映射器
        self.character_mapper = character_mapper
        if self.character_mapper is None:
            logger.info("初始化默认角色声音映射器")
            self.character_mapper = CharacterVoiceMapper()
        
        # 声场处理器
        self.sound_field = None
        if self.config.get("with_sound_field"):
            logger.info("初始化声场处理器")
            self.sound_field = SoundField()
            self.with_sound_field = True
        else:
            self.with_sound_field = False
        
        # 进度回调函数
        self.progress_callback = None
        
        logger.info("小说语音生成器初始化完成")
    
    def _get_voice_for_character(self, character: str) -> str:
        """
        获取角色的音色ID
        
        Args:
            character: 角色名
            
        Returns:
            str: 音色ID
        """
        # 空角色使用旁白音色
        if not character:
            return self.voice_mapping.get("narrator", "female_mature")
        
        # 首先使用CharacterVoiceMapper查找
        if self.character_mapper:
            character_voice = self.character_mapper.get_character_voice(character)
            if character_voice:
                logger.debug(f"通过角色映射器找到角色 '{character}' 的声音: {character_voice['voice']['id']}")
                return character_voice["voice"]["id"]
        
        # 回退到直接映射
        if character in self.voice_mapping:
            return self.voice_mapping[character]
            
        # 包含匹配，如"张三说"可以匹配"张三"
        for name in self.voice_mapping:
            if name in character:
                return self.voice_mapping[name]
        
        # 尝试使用CharacterVoiceMapper进行角色推荐
        if self.character_mapper:
            # 为角色创建声音映射建议
            suggestions = self.character_mapper.suggest_character_mapping(character)
            if character in suggestions and suggestions[character]:
                # 使用第一个建议的声音
                suggested_voice = suggestions[character][0]
                logger.info(f"为角色 '{character}' 自动建议声音: {suggested_voice}")
                
                # 保存此映射以便后续使用
                try:
                    self.character_mapper.map_character(
                        character, 
                        suggested_voice,
                        {"auto_suggested": True}
                    )
                except Exception as e:
                    logger.warning(f"保存角色声音映射失败: {e}")
                    
                return suggested_voice
        
        # 返回默认角色音色
        return self.voice_mapping.get(
            "character_default", 
            "male_young"
        )
    
    def _process_paragraph(
        self, 
        text: str, 
        output_path: str,
        voice_id: str = None,
        emotion_type: str = "neutral",
        use_feature: bool = True
    ) -> bool:
        """
        处理单个段落，生成语音
        
        Args:
            text: 段落文本
            output_path: 输出文件路径
            voice_id: 音色ID，默认使用旁白音色
            emotion_type: 情感类型
            use_feature: 是否使用声纹特征
            
        Returns:
            bool: 是否成功处理
        """
        if not text.strip():
            return False
            
        try:
            # 使用默认旁白音色
            if voice_id is None:
                voice_id = self.voice_mapping.get("narrator", "female_mature")
            
            # 获取声纹特征
            voice_feature = None
            if use_feature and self.character_mapper:
                try:
                    from ..tts.voice_feature import VoiceFeatureExtractor
                    extractor = VoiceFeatureExtractor()
                    voice_feature = extractor.get_voice_feature(voice_id)
                    if voice_feature is not None:
                        logger.debug(f"使用声纹特征生成语音: {voice_id}")
                except Exception as e:
                    logger.warning(f"获取声纹特征失败: {str(e)}")
                    voice_feature = None
            
            # 生成语音
            if voice_feature is not None:
                # 使用声纹特征合成
                audio = self.tts_engine.synthesize_with_feature(
                    text=text,
                    voice_feature=voice_feature,
                    emotion_type=emotion_type
                )
            else:
                # 使用普通音色合成
                audio = self.tts_engine.synthesize(
                    text=text,
                    voice_id=voice_id,
                    emotion_type=emotion_type
                )
            
            # 保存音频
            os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
            save_audio(output_path, audio)
            
            return True
            
        except Exception as e:
            logger.error(f"处理段落失败: {str(e)}")
            return False
    
    def _detect_speaker(self, text: str) -> Optional[str]:
        """
        检测段落中的说话人
        
        Args:
            text: 段落文本
            
        Returns:
            Optional[str]: 说话人，如果没有检测到则返回None
        """
        # 匹配"XXX说"的模式
        patterns = [
            r'"([^"]+)"(?:说|道|问|喊|叫|笑道|冷笑道|回答|回应|询问)',
            r'"([^"]+)"(?:说|道|问|喊|叫|笑道|冷笑道|回答|回应|询问)',
            r'「([^」]+)」(?:说|道|问|喊|叫|笑道|冷笑道|回答|回应|询问)',
            r'\'([^\']+)\'(?:说|道|问|喊|叫|笑道|冷笑道|回答|回应|询问)',
            r'"([^"]+)"(?:说|道|问|喊|叫|笑道|冷笑道|回答|回应|询问)'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text)
            if matches:
                return matches[0]
                
        return None
    
    def process_novel(self, novel_path: str, output_dir: str, progress_callback: Optional[Callable] = None, resume_from: int = 0, auto_character_mapping: bool = True) -> Dict[str, Any]:
        """
        处理整本小说，转换为有声书
        
        Args:
            novel_path: 小说文件路径
            output_dir: 输出目录
            progress_callback: 进度回调函数
            resume_from: 从哪一章开始处理（用于恢复处理）
            auto_character_mapping: 是否自动分析并映射角色
            
        Returns:
            Dict[str, Any]: 处理结果信息
        """
        self.progress_callback = progress_callback
        
        # 创建输出目录
        os.makedirs(output_dir, exist_ok=True)
        
        try:
            # 分割小说
            logger.info(f"开始分割小说: {novel_path}")
            chapters = self.segmenter.segment_novel(novel_path)
            
            # 获取小说名称（去除扩展名）
            novel_name = os.path.splitext(os.path.basename(novel_path))[0]
            
            # 自动角色分析
            if auto_character_mapping and self.character_mapper:
                logger.info("开始自动分析小说角色...")
                # 读取小说内容
                novel_text = self.segmenter.load_novel(novel_path)
                # 分析角色
                characters = self.character_mapper.analyze_novel_characters(novel_text)
                # 生成建议
                suggestions = self.character_mapper.suggest_character_mapping(novel_text)
                
                # 输出角色分析结果
                logger.info(f"发现 {len(characters)} 个角色")
                for character, count in sorted(characters.items(), key=lambda x: x[1], reverse=True)[:10]:
                    suggested = suggestions.get(character, [])
                    logger.info(f"角色: {character} (出现 {count} 次), 建议音色: {suggested}")
                    
                # 保存角色分析结果
                character_analysis = {
                    "total": len(characters),
                    "characters": [
                        {"name": name, "count": count, "suggested_voices": suggestions.get(name, [])}
                        for name, count in sorted(characters.items(), key=lambda x: x[1], reverse=True)
                    ]
                }
                
                with open(os.path.join(output_dir, "character_analysis.json"), "w", encoding="utf-8") as f:
                    json.dump(character_analysis, f, ensure_ascii=False, indent=2)
                
                logger.info(f"角色分析结果已保存到 {os.path.join(output_dir, 'character_analysis.json')}")
            
            # 初始化处理状态
            state = {
                "novel_path": novel_path,
                "novel_name": novel_name,
                "output_dir": output_dir,
                "total_chapters": len(chapters),
                "completed_chapters": 0,
                "failed_chapters": 0,
                "total_paragraphs": sum(len(chapter["paragraphs"]) for chapter in chapters),
                "completed_paragraphs": 0,
                "failed_paragraphs": 0,
                "start_time": time.time(),
                "last_update_time": time.time()
            }
            
            # 保存处理状态
            state_file = os.path.join(output_dir, "processing_state.json")
            with open(state_file, "w", encoding="utf-8") as f:
                json.dump(state, f, ensure_ascii=False, indent=2)
            
            # 处理章节
            for i, chapter in enumerate(chapters):
                # 如果设置了恢复点，跳过已处理的章节
                if i < resume_from:
                    logger.info(f"跳过已处理章节 {i}: {chapter['title']}")
                    continue
                
                # 创建章节目录
                chapter_dir = os.path.join(output_dir, f"chapter_{i:03d}")
                os.makedirs(chapter_dir, exist_ok=True)
                
                # 处理章节
                logger.info(f"处理章节 {i}/{len(chapters)}: {chapter['title']}")
                
                # 处理章节内容
                result = self._process_chapter(chapter, chapter_dir)
                
                # 更新处理状态
                state["completed_chapters"] += 1
                state["completed_paragraphs"] += result["completed_paragraphs"]
                state["failed_paragraphs"] += result["failed_paragraphs"]
                state["last_update_time"] = time.time()
                
                # 保存处理状态
                with open(state_file, "w", encoding="utf-8") as f:
                    json.dump(state, f, ensure_ascii=False, indent=2)
                
                # 回调进度
                if progress_callback:
                    progress = i / len(chapters)
                    progress_callback(progress, i, len(chapters))
            
            # 完成处理
            state["end_time"] = time.time()
            state["status"] = "completed"
            
            # 保存最终处理状态
            with open(state_file, "w", encoding="utf-8") as f:
                json.dump(state, f, ensure_ascii=False, indent=2)
                
            logger.info(f"小说处理完成: {novel_path}")
            return state
            
        except Exception as e:
            logger.error(f"处理小说失败: {str(e)}")
            return {
                "status": "failed",
                "error": str(e)
            }
    
    def _process_chapter(
        self, 
        chapter: Dict[str, Any], 
        chapter_dir: str
    ) -> Dict[str, Any]:
        """
        处理单个章节
        
        Args:
            chapter: 章节数据
            chapter_dir: 章节输出目录
            
        Returns:
            Dict[str, Any]: 处理结果
        """
        logger.info(f"处理章节: {chapter['title']}")
        
        # 处理结果统计
        result = {
            "chapter_index": chapter["index"],
            "chapter_title": chapter["title"],
            "total_paragraphs": len(chapter["paragraphs"]),
            "completed_paragraphs": 0,
            "failed_paragraphs": 0
        }
        
        # 处理标题
        title_path = f"{chapter_dir}/title.wav"
        title_processed = self._process_paragraph(
            chapter["title"],
            title_path,
            voice_id=self.config.get("voice_mapping", {}).get("narrator", "female_mature")
        )
        
        if title_processed:
            result["completed_paragraphs"] += 1
        else:
            result["failed_paragraphs"] += 1
        
        # 处理段落
        paragraph_paths = []
        if title_processed:
            paragraph_paths.append(title_path)
        
        for i, para in enumerate(chapter["paragraphs"]):
            para_path = f"{chapter_dir}/para_{i:04d}.wav"
            
            # 检测对话和角色
            speaker = self._detect_speaker(para)
            voice_id = self._get_voice_for_character(speaker) if speaker else None
            
            # 处理段落
            para_processed = self._process_paragraph(para, para_path, voice_id)
            
            if para_processed:
                result["completed_paragraphs"] += 1
                paragraph_paths.append(para_path)
            else:
                result["failed_paragraphs"] += 1
        
        # 合并章节音频
        if paragraph_paths:
            try:
                merge_audio_files(
                    paragraph_paths,
                    f"{chapter_dir}.mp3"
                )
                logger.info(f"章节音频合并完成: {chapter_dir}.mp3")
            except Exception as e:
                logger.error(f"合并章节音频失败: {str(e)}")
        
        return result