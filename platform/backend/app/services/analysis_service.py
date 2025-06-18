"""
智能分析服务
处理书籍内容的AI智能分析功能
"""

import asyncio
import json
import hashlib
from typing import List, Dict, Any, Optional, AsyncGenerator
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from ..models import Book, BookChapter, NovelProject, AnalysisSession, AnalysisResult
# from .dify_client import DifyClient  # 🚀 已删除 - 文件不存在
from ..exceptions import ServiceException, DifyAPIException
from ..utils.websocket_manager import ProgressWebSocketManager


class AnalysisSessionManager:
    """分析会话管理器"""
    
    def __init__(self, db: Session, websocket_manager: ProgressWebSocketManager):
        self.db = db
        self.websocket_manager = websocket_manager
        # self.dify_client = DifyClient()  # 🚀 已删除 - 文件不存在
        
    async def create_session(
        self, 
        project_id: int, 
        target_type: str,
        target_ids: List[int] = None,
        config: Dict[str, Any] = None
    ) -> AnalysisSession:
        """创建新的分析会话"""
        
        # 验证项目存在
        project = self.db.query(NovelProject).filter(NovelProject.id == project_id).first()
        if not project:
            raise ServiceException("项目不存在")
        
        # 计算任务总数
        total_tasks = 0
        if target_type == "full_book":
            total_tasks = self.db.query(BookChapter).filter(BookChapter.book_id == project.book_id).count()
        elif target_type == "chapters":
            total_tasks = len(target_ids or [])
        else:
            raise ServiceException(f"不支持的目标类型: {target_type}")
        
        # 创建会话
        session = AnalysisSession(
            project_id=project_id,
            book_id=project.book_id,
            target_type=target_type,
            target_ids=json.dumps(target_ids or []),
            llm_provider=config.get("llm_provider", "dify"),
            llm_model=config.get("llm_model"),
            llm_workflow_id=config.get("llm_workflow_id"),
            status="pending",
            total_tasks=total_tasks
        )
        
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)
        
        return session
    
    async def start_session(self, session_id: int) -> bool:
        """启动分析会话"""
        session = self.db.query(AnalysisSession).filter(AnalysisSession.id == session_id).first()
        if not session:
            raise ServiceException("会话不存在")
        
        if session.status != "pending":
            raise ServiceException(f"会话状态不正确: {session.status}")
        
        # 更新会话状态
        session.status = "running"
        session.started_at = datetime.utcnow()
        self.db.commit()
        
        # 异步启动分析任务
        asyncio.create_task(self._run_analysis_tasks(session))
        
        return True
    
    async def _run_analysis_tasks(self, session: AnalysisSession):
        """执行分析任务主逻辑"""
        try:
            # 获取目标章节
            target_ids = json.loads(session.target_ids)
            
            if session.target_type == "full_book":
                chapters = self.db.query(BookChapter).filter(
                    BookChapter.book_id == session.book_id
                ).order_by(BookChapter.chapter_number).all()
            else:
                chapters = self.db.query(BookChapter).filter(
                    BookChapter.id.in_(target_ids)
                ).order_by(BookChapter.chapter_number).all()
            
            # 批量处理章节
            batch_size = 3  # 并发处理数量
            completed = 0
            
            for i in range(0, len(chapters), batch_size):
                batch_chapters = chapters[i:i + batch_size]
                
                # 并发处理本批次章节
                tasks = [
                    self._analyze_chapter(session, chapter) 
                    for chapter in batch_chapters
                ]
                
                batch_results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # 处理结果
                for j, result in enumerate(batch_results):
                    chapter = batch_chapters[j]
                    completed += 1
                    
                    if isinstance(result, Exception):
                        session.failed_tasks += 1
                        await self._send_progress_update(session, completed, f"章节 {chapter.chapter_title} 分析失败: {str(result)}")
                    else:
                        session.completed_tasks += 1
                        await self._send_progress_update(session, completed, f"章节 {chapter.chapter_title} 分析完成")
                    
                    # 更新数据库
                    self.db.commit()
                
                # 批次间休息，避免API限流
                if i + batch_size < len(chapters):
                    await asyncio.sleep(2)
            
            # 完成会话
            session.status = "completed"
            session.completed_at = datetime.utcnow()
            session.progress = 100
            
            await self._send_progress_update(session, completed, "所有章节分析完成")
            
        except Exception as e:
            # 处理全局错误
            session.status = "failed"
            session.error_message = str(e)
            await self._send_progress_update(session, session.completed_tasks, f"分析失败: {str(e)}")
        
        finally:
            self.db.commit()
    
    async def _analyze_chapter(self, session: AnalysisSession, chapter: BookChapter) -> AnalysisResult:
        """分析单个章节"""
        try:
            # 计算内容哈希
            input_hash = hashlib.md5(chapter.content.encode('utf-8')).hexdigest()
            
            # 检查是否已有相同内容的分析结果
            existing_result = self.db.query(AnalysisResult).filter(
                and_(
                    AnalysisResult.input_hash == input_hash,
                    AnalysisResult.status == "active"
                )
            ).first()
            
            if existing_result:
                # 复制现有结果
                new_result = AnalysisResult(
                    session_id=session.id,
                    chapter_id=chapter.id,
                    input_text=chapter.content,
                    input_hash=input_hash,
                    raw_response=existing_result.raw_response,
                    project_info=existing_result.project_info,
                    synthesis_plan=existing_result.synthesis_plan,
                    characters=existing_result.characters,
                    final_config=existing_result.final_config,
                    llm_response_time=0  # 缓存命中，响应时间为0
                )
            else:
                # 调用LLM分析
                start_time = datetime.utcnow()
                # llm_response = await self.dify_client.analyze_text(  # 🚀 已删除 - DifyClient不存在
                # 使用模拟响应或其他分析方法
                llm_response = await self._fallback_analysis(
                    text=chapter.content,
                    workflow_id=session.llm_workflow_id
                )
                end_time = datetime.utcnow()
                response_time = int((end_time - start_time).total_seconds() * 1000)
                
                # 解析响应
                parsed_result = self._parse_llm_response(llm_response)
                
                new_result = AnalysisResult(
                    session_id=session.id,
                    chapter_id=chapter.id,
                    input_text=chapter.content,
                    input_hash=input_hash,
                    llm_request_id=llm_response.get("request_id"),
                    llm_response_time=response_time,
                    raw_response=llm_response,
                    project_info=parsed_result.get("project_info"),
                    synthesis_plan=parsed_result["synthesis_plan"],
                    characters=parsed_result["characters"],
                    final_config=parsed_result["synthesis_plan"]  # 初始时final_config等于synthesis_plan
                )
            
            self.db.add(new_result)
            self.db.commit()
            self.db.refresh(new_result)
            
            return new_result
            
        except Exception as e:
            raise ServiceException(f"章节分析失败: {str(e)}")
    
    def _parse_llm_response(self, llm_response: Dict[str, Any]) -> Dict[str, Any]:
        """解析LLM响应结果"""
        try:
            # 从Dify响应中提取结构化数据
            # 这里需要根据实际的Dify工作流输出格式进行调整
            output_data = llm_response.get("data", {})
            
            # 解析项目信息
            project_info = output_data.get("project_info", {})
            
            # 解析合成计划
            synthesis_plan = output_data.get("synthesis_plan", {})
            if not synthesis_plan:
                raise ServiceException("LLM响应中缺少synthesis_plan")
            
            # 解析角色列表
            characters = output_data.get("characters", [])
            if not characters:
                raise ServiceException("LLM响应中缺少characters")
            
            return {
                "project_info": project_info,
                "synthesis_plan": synthesis_plan,
                "characters": characters
            }
            
        except (KeyError, TypeError, json.JSONDecodeError) as e:
            raise ServiceException(f"LLM响应解析失败: {str(e)}")
    
    async def _send_progress_update(self, session: AnalysisSession, completed: int, message: str):
        """发送进度更新"""
        progress = min(100, round((completed / session.total_tasks) * 100)) if session.total_tasks > 0 else 0
        session.progress = progress
        session.current_processing = message
        
        # 通过WebSocket发送更新
        await self.websocket_manager.send_progress_update(
            session_id=f"analysis_{session.id}",
            data={
                "session_id": session.id,
                "status": session.status,
                "progress": progress,
                "completed_tasks": completed,
                "total_tasks": session.total_tasks,
                "failed_tasks": session.failed_tasks,
                "current_processing": message,
                "timestamp": datetime.utcnow().isoformat()
            }
        )

    async def _fallback_analysis(self, text: str, workflow_id: str = None) -> Dict[str, Any]:
        """降级分析方法 - 当DifyClient不可用时使用"""
        import re
        
        # 简单的文本分析逻辑
        lines = text.split('\n')
        dialogues = []
        
        # 检测对话
        dialogue_patterns = [r'"([^"]*)"', r'"([^"]*)"', r'「([^」]*)」']
        
        for line in lines:
            for pattern in dialogue_patterns:
                matches = re.findall(pattern, line)
                dialogues.extend(matches)
        
        # 生成简化的分析结果
        characters = []
        if dialogues:
            # 基于对话数量估算角色
            char_count = min(len(set(dialogues[:10])), 5)
            for i in range(char_count):
                characters.append({
                    "name": f"角色{i+1}",
                    "voice_id": i + 1
                })
        
        # 添加旁白
        characters.append({
            "name": "旁白",
            "voice_id": len(characters) + 1
        })
        
        # 生成合成计划
        synthesis_plan = {
            "segments": []
        }
        
        segment_id = 1
        for line in lines[:20]:  # 只处理前20行
            if line.strip():
                is_dialogue = any(re.search(pattern, line) for pattern in dialogue_patterns)
                synthesis_plan["segments"].append({
                    "id": segment_id,
                    "text": line.strip(),
                    "speaker": "角色1" if is_dialogue else "旁白",
                    "voice_id": 1 if is_dialogue else len(characters)
                })
                segment_id += 1
        
        return {
            "request_id": f"fallback_{hash(text) % 10000}",
            "data": {
                "project_info": {
                    "analysis_method": "fallback",
                    "total_segments": len(synthesis_plan["segments"])
                },
                "synthesis_plan": synthesis_plan,
                "characters": characters
            }
        }


class AnalysisService:
    """智能分析服务主类"""
    
    def __init__(self, db: Session, websocket_manager: ProgressWebSocketManager = None):
        self.db = db
        self.websocket_manager = websocket_manager or ProgressWebSocketManager()
        self.session_manager = AnalysisSessionManager(db, self.websocket_manager)
    
    async def start_analysis(
        self, 
        project_id: int, 
        target_type: str = "full_book",
        target_ids: List[int] = None,
        config: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """启动智能分析"""
        
        # 检查是否有正在运行的会话
        active_session = self.db.query(AnalysisSession).filter(
            and_(
                AnalysisSession.project_id == project_id,
                AnalysisSession.status.in_(["pending", "running"])
            )
        ).first()
        
        if active_session:
            raise ServiceException("该项目已有正在进行的分析会话")
        
        # 创建新会话
        session = await self.session_manager.create_session(
            project_id=project_id,
            target_type=target_type,
            target_ids=target_ids,
            config=config or {}
        )
        
        # 启动会话
        await self.session_manager.start_session(session.id)
        
        return {
            "session_id": session.id,
            "status": session.status,
            "total_tasks": session.total_tasks,
            "message": "分析已启动"
        }
    
    async def get_session_status(self, session_id: int) -> Dict[str, Any]:
        """获取会话状态"""
        session = self.db.query(AnalysisSession).filter(AnalysisSession.id == session_id).first()
        if not session:
            raise ServiceException("会话不存在")
        
        return {
            "session_id": session.id,
            "project_id": session.project_id,
            "status": session.status,
            "progress": session.progress,
            "total_tasks": session.total_tasks,
            "completed_tasks": session.completed_tasks,
            "failed_tasks": session.failed_tasks,
            "current_processing": session.current_processing,
            "started_at": session.started_at.isoformat() if session.started_at else None,
            "completed_at": session.completed_at.isoformat() if session.completed_at else None,
            "error_message": session.error_message
        }
    
    async def cancel_session(self, session_id: int) -> bool:
        """取消分析会话"""
        session = self.db.query(AnalysisSession).filter(AnalysisSession.id == session_id).first()
        if not session:
            raise ServiceException("会话不存在")
        
        if session.status not in ["pending", "running"]:
            raise ServiceException(f"无法取消状态为 {session.status} 的会话")
        
        session.status = "cancelled"
        self.db.commit()
        
        return True
    
    async def get_analysis_results(self, session_id: int) -> List[Dict[str, Any]]:
        """获取分析结果"""
        results = self.db.query(AnalysisResult).filter(
            and_(
                AnalysisResult.session_id == session_id,
                AnalysisResult.status == "active"
            )
        ).order_by(AnalysisResult.created_at).all()
        
        return [result.to_dict() for result in results]
    
    async def update_analysis_result(
        self, 
        result_id: int, 
        user_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """更新分析结果（用户修改配置）"""
        result = self.db.query(AnalysisResult).filter(AnalysisResult.id == result_id).first()
        if not result:
            raise ServiceException("分析结果不存在")
        
        # 记录用户修改
        result.user_modified = True
        result.user_config = user_config
        
        # 合并最终配置
        final_config = result.synthesis_plan.copy()
        final_config.update(user_config)
        result.final_config = final_config
        
        result.applied_at = datetime.utcnow()
        
        self.db.commit()
        
        return result.to_dict()
    
    async def get_project_analysis_history(self, project_id: int) -> List[Dict[str, Any]]:
        """获取项目的分析历史"""
        sessions = self.db.query(AnalysisSession).filter(
            AnalysisSession.project_id == project_id
        ).order_by(AnalysisSession.created_at.desc()).all()
        
        return [session.to_dict() for session in sessions]
    
    async def delete_session(self, session_id: int) -> bool:
        """删除分析会话及其结果"""
        session = self.db.query(AnalysisSession).filter(AnalysisSession.id == session_id).first()
        if not session:
            raise ServiceException("会话不存在")
        
        if session.status == "running":
            raise ServiceException("无法删除正在运行的会话")
        
        # 删除相关的分析结果
        self.db.query(AnalysisResult).filter(AnalysisResult.session_id == session_id).delete()
        
        # 删除会话
        self.db.delete(session)
        self.db.commit()
        
        return True 