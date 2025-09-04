import asyncio
import logging
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from app.services.storyboard_analysis.llm_client import LLMClient
from app.models.analysis_result import AnalysisResult

logger = logging.getLogger(__name__)


class SmartSegmentationService:
    """智能分段服务 - 清理版本，专注于正确分段"""
    
    def __init__(self):
        # 使用qwen3:8b模型，分段效果最好
        self.llm = LLMClient(model="qwen3:8b", base_url="http://localhost:11434")
        self.llm.timeout = 300  # 增加超时时间到5分钟
        
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

    async def segment_and_save(self, content: str, chapter_id: int, db: Session) -> Dict[str, Any]:
        """智能分段并持久化保存到数据库"""
        try:
            logger.info(f"开始智能分段并持久化，章节ID: {chapter_id}")
            
            # 1. 执行智能分段
            segments = await self.segment_content(content)
            
            # 2. 验证分段结果
            is_valid = await self.validate_segments(content, segments)
            if not is_valid:
                raise ValueError("分段验证失败")
            
            # 3. 构建分段数据
            segmentation_data = {
                "chapter_id": chapter_id,
                "original_content": content,
                "segments": segments,
                "segment_count": len(segments),
                "total_length": len(content),
                "segments_length": [len(seg) for seg in segments],
                "created_at": datetime.utcnow().isoformat(),
                "model_used": "qwen3:8b",
                "validation_passed": True
            }
            
            # 4. 保存到数据库
            saved_result = await self._save_segmentation_result(segmentation_data, db)
            
            logger.info(f"分段持久化成功，章节ID: {chapter_id}，共 {len(segments)} 段")
            
            return {
                "success": True,
                "segments": segments,
                "segmentation_data": segmentation_data,
                "storage_info": saved_result
            }
            
        except Exception as e:
            logger.error(f"分段持久化失败，章节ID: {chapter_id}，错误: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "segments": []
            }

    async def _save_segmentation_result(self, segmentation_data: Dict[str, Any], db: Session) -> Dict[str, Any]:
        """保存分段结果到数据库"""
        try:
            # 检查是否已有该章节的分段结果
            existing_result = db.query(AnalysisResult).filter(
                AnalysisResult.chapter_id == segmentation_data["chapter_id"],
                AnalysisResult.status == 'completed'
            ).first()
            
            if existing_result:
                # 更新现有记录，保留已有的6卡分析数据
                logger.info(f"更新现有分段结果，章节ID: {segmentation_data['chapter_id']}")
                
                # 获取现有的original_analysis，保留所有已有数据
                current_analysis = existing_result.original_analysis or {}
                
                # 合并数据，保留6卡分析结果，添加智能分段数据
                updated_analysis = {
                    **current_analysis,  # 保留现有数据（包括6卡分析）
                    "segmentation": segmentation_data,
                    "segments": segmentation_data["segments"],  # 新格式
                    "smart_segmentation_saved_at": datetime.utcnow().isoformat()
                }
                
                existing_result.original_analysis = updated_analysis
                existing_result.updated_at = datetime.utcnow()
                
            else:
                # 创建新记录
                logger.info(f"创建新分段结果记录，章节ID: {segmentation_data['chapter_id']}")
                
                new_result = AnalysisResult(
                    chapter_id=segmentation_data["chapter_id"],
                    original_analysis={
                        "segmentation": segmentation_data,
                        "segments": segmentation_data["segments"],  # 新格式
                        "smart_segmentation_saved_at": datetime.utcnow().isoformat()
                    },
                    status='completed',
                    processing_time=0,
                    confidence_score=95,  # 分段质量评分
                    created_at=datetime.utcnow(),
                    completed_at=datetime.utcnow()
                )
                
                db.add(new_result)
            
            db.commit()
            
            return {
                "storage_method": "analysis_result",
                "chapter_id": segmentation_data["chapter_id"],
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"保存分段结果失败: {str(e)}")
            db.rollback()
            raise

    async def get_cached_segments(self, chapter_id: int, db: Session) -> Optional[List[str]]:
        """从数据库获取缓存的分段结果"""
        try:
            logger.info(f"开始查询章节 {chapter_id} 的分段数据")

            # 查询所有AnalysisResult记录，检查是否有该章节的数据
            all_results = db.query(AnalysisResult).filter(
                AnalysisResult.chapter_id == chapter_id
            ).all()

            logger.info(f"找到 {len(all_results)} 条AnalysisResult记录，章节ID: {chapter_id}")

            for result in all_results:
                logger.info(f"记录详情 - ID: {result.id}, 状态: {result.status}, 有original_analysis: {result.original_analysis is not None}")

            existing_result = db.query(AnalysisResult).filter(
                AnalysisResult.chapter_id == chapter_id,
                AnalysisResult.status == 'completed'
            ).first()

            if existing_result:
                logger.info(f"找到completed状态的记录: ID={existing_result.id}")
                logger.info(f"original_analysis存在: {existing_result.original_analysis is not None}")

                if existing_result.original_analysis:
                    logger.info(f"original_analysis内容: {existing_result.original_analysis}")
                    original_data = existing_result.original_analysis

                    # 直接检查original_analysis中是否有segments字段（新格式）
                    if "segments" in original_data:
                        segments = original_data["segments"]
                        logger.info(f"从缓存获取分段结果（新格式），章节ID: {chapter_id}，共 {len(segments)} 段")
                        return segments

                    # 检查是否有segmentation子字段（旧格式）
                    segmentation_data = original_data.get("segmentation")
                    if segmentation_data:
                        logger.info(f"找到segmentation数据: {segmentation_data}")
                        if "segments" in segmentation_data:
                            segments = segmentation_data["segments"]
                            logger.info(f"从缓存获取分段结果（旧格式），章节ID: {chapter_id}，共 {len(segments)} 段")
                            return segments
                        else:
                            logger.warning(f"segmentation数据中没有segments字段: {segmentation_data}")
                    else:
                        logger.warning(f"original_analysis中既没有segments字段也没有segmentation字段: {original_data}")
                else:
                    logger.warning(f"记录ID={existing_result.id}的original_analysis为空")
            else:
                logger.info(f"未找到章节 {chapter_id} 的completed状态分段结果")

            logger.info(f"未找到缓存的分段结果，章节ID: {chapter_id}")
            return None

        except Exception as e:
            logger.error(f"获取缓存分段结果失败: {str(e)}")
            import traceback
            logger.error(f"完整错误堆栈: {traceback.format_exc()}")
            return None
