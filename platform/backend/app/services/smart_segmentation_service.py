import asyncio
import logging
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from app.services.storyboard_analysis.llm_client import LLMClient
from app.models.smart_segmentation import SmartSegmentation
from app.utils.llm_config_loader import llm_config_loader

logger = logging.getLogger(__name__)


class SmartSegmentationService:
    """智能分段服务 - 清理版本，专注于正确分段"""
    
    def __init__(self):
        # 从统一配置加载器读取LLM模型设置
        self.llm_config = llm_config_loader.get_config()
        self.llm = LLMClient(
            model=self.llm_config["model"], 
            base_url=self.llm_config["base_url"]
        )
        self.llm.timeout = self.llm_config["timeout"]
        
        # 最佳分段提示词（测试验证过）
        self.segmentation_prompt = """你是一个专业的文学编辑，专门负责小说文本的智能分段。

任务：将以下小说文本按照故事逻辑和阅读体验进行合理分段。

【通用分段原则】
1. 场景完整性：同一场景的内容应该在同一段落
2. 事件完整性：一个完整事件不应该被分割
3. 对话完整性：对话和说话者的描述应该在一起
4. 情感连贯性：情感发展应该保持连贯
5. 段落长度：每段控制在100-300字之间

【分段方法】
- 寻找自然转折点（时间、地点、人物、事件的变化）
- 确保每段都有明确的重点
- 避免在句子中间或对话中间切断
- 使用 "---" 作为段落分隔符

请分析以下文本并进行分段："""

    async def segment_content(self, content: str) -> List[str]:
        """智能分段主函数 - 简洁版本"""
        logger.info(f"开始智能分段，原文长度: {len(content)} 字符")
        
        # 调用LLM进行分段
        response = await self.llm.call(self.segmentation_prompt + "\n\n" + content)
        
        # 解析分段结果
        segments = self._parse_response(response)
        
        # 验证分段结果
        if not segments or len(segments) <= 1:
            raise ValueError(f"分段失败，LLM返回无效结果")
        
        logger.info(f"分段成功，共 {len(segments)} 段")
        return segments

    def _parse_response(self, response: str) -> List[str]:
        """解析LLM响应，智能提取分段内容"""
        if not response:
            return []
        
        # 1. 移除<think>标签及其内容
        cleaned_response = self._remove_thinking_process(response)
        
        # 2. 按"---"分割
        segments = [seg.strip() for seg in cleaned_response.split("---") if seg.strip()]
        
        # 3. 过滤掉空段落和纯思考内容
        valid_segments = []
        for seg in segments:
            clean_seg = self._clean_segment(seg)
            if clean_seg and len(clean_seg) > 10:  # 至少10个字符
                valid_segments.append(clean_seg)
        
        logger.info(f"解析到 {len(valid_segments)} 个有效分段")
        return valid_segments
    
    def _remove_thinking_process(self, response: str) -> str:
        """移除LLM的思考过程"""
        import re
        
        # 移除<think>标签及其内容
        response = re.sub(r'<think>.*?</think>', '', response, flags=re.DOTALL)
        
        # 移除"【分段结果】"、"【分段说明】"等标记
        response = re.sub(r'【.*?】', '', response)
        
        # 移除"第一段"、"第二段"等标记
        response = re.sub(r'第[一二三四五六七八九十]段.*?：', '', response)
        
        return response.strip()
    
    def _clean_segment(self, segment: str) -> str:
        """清理单个段落内容"""
        import re
        
        # 移除多余的空格和换行
        segment = re.sub(r'\s+', ' ', segment)
        
        # 移除纯数字和标点
        if re.match(r'^[\d\s\W]+$', segment):
            return ""
        
        # 移除过短的段落
        if len(segment.strip()) < 10:
            return ""
        
        return segment.strip()

    async def validate_segments(self, original_content: str, segments: List[str]) -> bool:
        """验证分段结果的基本完整性"""
        if not segments:
            return False
        
        # 合并所有分段
        combined = " ".join(segments)
        combined_length = len(combined.replace(" ", ""))
        original_length = len(original_content.replace(" ", ""))
        
        # 检查长度差异（允许小幅差异）
        length_diff = abs(combined_length - original_length) / original_length
        if length_diff > 0.1:  # 允许10%的差异
            logger.warning(f"分段后长度差异过大: {length_diff:.2%}")
            return False
        
        logger.info(f"分段验证通过，长度差异: {length_diff:.2%}")
        return True

    async def segment_and_save(self, content: str, project_id: int, chapter_id: int, db: Session, force_update: bool = False) -> Dict[str, Any]:
        """智能分段并持久化保存到数据库"""
        try:
            logger.debug(f"开始智能分段并持久化，分析项目ID: {project_id}，章节ID: {chapter_id}，强制覆盖: {force_update}")
            
            # 1. 执行智能分段
            segments = await self.segment_content(content)
            
            # 2. 验证分段结果
            is_valid = await self.validate_segments(content, segments)
            if not is_valid:
                raise ValueError("分段验证失败")
            
            # 3. 构建分段数据
            segmentation_data = {
                "project_id": project_id,
                "chapter_id": chapter_id,
                "original_content": content,
                "segments": segments,
                "segment_count": len(segments),
                "total_length": len(content),
                "segments_length": [len(seg) for seg in segments],
                "created_at": datetime.utcnow().isoformat(),
                "model_used": "qwen3:8b",
                "validation_passed": True,
                "force_update": force_update
            }
            
            # 4. 保存到数据库
            saved_result = await self._save_segmentation_result(segmentation_data, db, force_update)
            
            logger.debug(f"分段持久化成功，分析项目ID: {project_id}，章节ID: {chapter_id}，共 {len(segments)} 段")
            
            return {
                "success": True,
                "segments": segments,
                "segmentation_data": segmentation_data,
                "storage_info": saved_result
            }
            
        except Exception as e:
            logger.error(f"分段持久化失败，分析项目ID: {project_id}，章节ID: {chapter_id}，错误: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "segments": []
            }

    async def _save_segmentation_result(self, segmentation_data: Dict[str, Any], db: Session, force_update: bool = False) -> Dict[str, Any]:
        """保存分段结果到独立的智能分段表"""
        try:
            # 检查是否已有该分析项目和章节的分段结果
            existing_result = db.query(SmartSegmentation).filter(
                SmartSegmentation.project_id == segmentation_data["project_id"],
                SmartSegmentation.chapter_id == segmentation_data["chapter_id"]
            ).first()
            
            if existing_result:
                if force_update:
                    # 强制覆盖现有记录
                    logger.info(f"强制覆盖现有智能分段结果，分析项目ID: {segmentation_data['project_id']}，章节ID: {segmentation_data['chapter_id']}")
                    
                    existing_result.original_content = segmentation_data["original_content"]
                    existing_result.segments = segmentation_data["segments"]
                    existing_result.segment_count = segmentation_data["segment_count"]
                    existing_result.total_length = segmentation_data["total_length"]
                    existing_result.segments_length = segmentation_data["segments_length"]
                    existing_result.model_used = segmentation_data["model_used"]
                    existing_result.validation_passed = segmentation_data["validation_passed"]
                    existing_result.updated_at = datetime.utcnow()
                    
                    db.commit()
                    db.refresh(existing_result)
                    
                    return {
                        "success": True,
                        "action": "force_updated",
                        "segmentation_id": existing_result.id,
                        "message": f"智能分段结果已强制覆盖，分析项目ID: {segmentation_data['project_id']}，章节ID: {segmentation_data['chapter_id']}"
                    }
                else:
                    # 非强制覆盖，返回现有结果
                    logger.info(f"智能分段结果已存在，跳过更新，分析项目ID: {segmentation_data['project_id']}，章节ID: {segmentation_data['chapter_id']}")
                    
                    return {
                        "success": True,
                        "action": "skipped",
                        "segmentation_id": existing_result.id,
                        "message": f"智能分段结果已存在，未进行更新，分析项目ID: {segmentation_data['project_id']}，章节ID: {segmentation_data['chapter_id']}"
                    }
                
            else:
                # 创建新记录
                logger.info(f"创建新的智能分段记录，分析项目ID: {segmentation_data['project_id']}，章节ID: {segmentation_data['chapter_id']}")
                
                new_segmentation = SmartSegmentation(
                    project_id=segmentation_data["project_id"],
                    chapter_id=segmentation_data["chapter_id"],
                    original_content=segmentation_data["original_content"],
                    segments=segmentation_data["segments"],
                    segment_count=segmentation_data["segment_count"],
                    total_length=segmentation_data["total_length"],
                    segments_length=segmentation_data["segments_length"],
                    model_used=segmentation_data["model_used"],
                    validation_passed=segmentation_data["validation_passed"]
                )
                
                db.add(new_segmentation)
                db.commit()
                db.refresh(new_segmentation)
                
                return {
                    "success": True,
                    "action": "created",
                    "segmentation_id": new_segmentation.id,
                    "message": f"智能分段结果已创建，分析项目ID: {segmentation_data['project_id']}，章节ID: {segmentation_data['chapter_id']}"
                }
                
        except Exception as e:
            logger.error(f"保存智能分段结果失败: {str(e)}")
            db.rollback()
            raise

    async def get_cached_segments(self, project_id: int, chapter_id: int, db: Session) -> Optional[List[str]]:
        """从独立的智能分段表获取分段结果"""
        try:
            logger.info(f"开始查询分析项目 {project_id} 章节 {chapter_id} 的智能分段数据")

            # 查询智能分段表
            segmentation_result = db.query(SmartSegmentation).filter(
                SmartSegmentation.project_id == project_id,
                SmartSegmentation.chapter_id == chapter_id
            ).first()

            if segmentation_result:
                logger.info(f"找到智能分段记录: ID={segmentation_result.id}, 分段数量={segmentation_result.segment_count}")
                segments = segmentation_result.segments
                logger.info(f"从智能分段表获取分段结果，分析项目ID: {project_id}，章节ID: {chapter_id}，共 {len(segments)} 段")
                return segments
            else:
                logger.info(f"未找到分析项目 {project_id} 章节 {chapter_id} 的智能分段结果")
                return None

        except Exception as e:
            logger.error(f"获取智能分段结果失败: {str(e)}")
            return None
