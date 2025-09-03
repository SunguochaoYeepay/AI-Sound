"""
多轮验证服务
实现分析结果的迭代优化和质量提升
"""

import json
import logging
import asyncio
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
from app.services.prompt_engine import prompt_engine
from app.config.analysis_config import analysis_config

logger = logging.getLogger(__name__)

@dataclass
class ValidationResult:
    """验证结果数据类"""
    round_number: int
    validation_type: str
    is_passed: bool
    confidence_score: float
    issues_found: List[str]
    improvement_suggestions: List[str]
    corrected_content: Optional[str] = None
    processing_time: float = 0.0

@dataclass
class AnalysisSession:
    """分析会话数据类"""
    session_id: str
    chapter_id: int
    original_content: str
    analysis_results: Dict[str, Any]
    validation_history: List[ValidationResult]
    current_round: int
    max_rounds: int
    overall_confidence: float
    status: str  # 'in_progress', 'completed', 'failed'
    created_at: datetime
    updated_at: datetime

class MultiRoundValidator:
    """多轮验证器"""
    
    def __init__(self):
        self.sessions: Dict[str, AnalysisSession] = {}
        self.validation_strategies = self._initialize_validation_strategies()
    
    def _initialize_validation_strategies(self) -> Dict[str, Dict[str, Any]]:
        """初始化验证策略"""
        return {
            "consistency": {
                "description": "一致性验证",
                "prompt_type": "consistency_check",
                "threshold": 0.90,
                "max_rounds": 3,
                "priority": 1
            },
            "accuracy": {
                "description": "准确性验证",
                "prompt_type": "accuracy_verification",
                "threshold": 0.92,
                "max_rounds": 3,
                "priority": 2
            },
            "quality": {
                "description": "质量评估",
                "prompt_type": "quality_assessment",
                "threshold": 0.85,
                "max_rounds": 2,
                "priority": 3
            },
            "completeness": {
                "description": "完整性验证",
                "prompt_type": "completeness_check",
                "threshold": 0.88,
                "max_rounds": 2,
                "priority": 4
            }
        }
    
    def create_analysis_session(
        self,
        session_id: str,
        chapter_id: int,
        original_content: str,
        analysis_results: Dict[str, Any],
        max_rounds: int = 5
    ) -> AnalysisSession:
        """创建分析会话"""
        session = AnalysisSession(
            session_id=session_id,
            chapter_id=chapter_id,
            original_content=original_content,
            analysis_results=analysis_results,
            validation_history=[],
            current_round=1,
            max_rounds=max_rounds,
            overall_confidence=0.0,
            status='in_progress',
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        self.sessions[session_id] = session
        logger.info(f"创建分析会话: {session_id}")
        return session
    
    async def run_multi_round_validation(
        self,
        session_id: str,
        validation_types: Optional[List[str]] = None
    ) -> AnalysisSession:
        """运行多轮验证"""
        if session_id not in self.sessions:
            raise ValueError(f"会话 '{session_id}' 不存在")
        
        session = self.sessions[session_id]
        
        # 如果没有指定验证类型，使用所有类型
        if validation_types is None:
            validation_types = list(self.validation_strategies.keys())
        
        # 按优先级排序验证类型
        validation_types.sort(
            key=lambda x: self.validation_strategies[x]["priority"]
        )
        
        logger.info(f"开始多轮验证: {session_id}, 验证类型: {validation_types}")
        
        for round_num in range(1, session.max_rounds + 1):
            session.current_round = round_num
            session.updated_at = datetime.now()
            
            logger.info(f"开始第 {round_num} 轮验证")
            
            # 运行所有验证类型
            for validation_type in validation_types:
                if validation_type not in self.validation_strategies:
                    continue
                
                strategy = self.validation_strategies[validation_type]
                
                # 检查是否达到最大轮数
                if round_num > strategy["max_rounds"]:
                    continue
                
                # 执行验证
                validation_result = await self._execute_validation(
                    session, validation_type, round_num
                )
                
                # 记录验证结果
                session.validation_history.append(validation_result)
                
                # 如果验证通过，更新分析结果
                if validation_result.is_passed and validation_result.corrected_content:
                    session.analysis_results = self._update_analysis_results(
                        session.analysis_results,
                        validation_result.corrected_content
                    )
                
                logger.info(f"第 {round_num} 轮 {validation_type} 验证: {'通过' if validation_result.is_passed else '失败'}")
            
            # 计算整体置信度
            session.overall_confidence = self._calculate_overall_confidence(session)
            
            # 检查是否达到目标置信度
            if session.overall_confidence >= 0.95:
                session.status = 'completed'
                logger.info(f"会话 {session_id} 达到目标置信度，验证完成")
                break
            
            # 检查是否还有改进空间
            if not self._has_improvement_potential(session):
                session.status = 'completed'
                logger.info(f"会话 {session_id} 无改进空间，验证完成")
                break
        
        # 如果达到最大轮数仍未完成，标记为失败
        if session.status == 'in_progress':
            session.status = 'failed'
            logger.warning(f"会话 {session_id} 达到最大轮数，验证失败")
        
        session.updated_at = datetime.now()
        return session
    
    async def _execute_validation(
        self,
        session: AnalysisSession,
        validation_type: str,
        round_number: int
    ) -> ValidationResult:
        """执行单次验证"""
        start_time = datetime.now()
        
        strategy = self.validation_strategies[validation_type]
        prompt_type = strategy["prompt_type"]
        threshold = strategy["threshold"]
        
        try:
            # 获取验证Prompt
            validation_prompt = prompt_engine.get_validation_prompt(
                prompt_type,
                {
                    "original_analysis": json.dumps(session.analysis_results, ensure_ascii=False),
                    "original_text": session.original_content,
                    "validation_points": self._get_validation_points(validation_type)
                }
            )
            
            # 这里应该调用LLM进行验证
            # 暂时使用模拟结果
            validation_result = await self._simulate_llm_validation(
                validation_prompt, session, validation_type, threshold
            )
            
            # 计算处理时间
            end_time = datetime.now()
            processing_time = (end_time - start_time).total_seconds()
            validation_result.processing_time = processing_time
            validation_result.round_number = round_number
            
            return validation_result
            
        except Exception as e:
            logger.error(f"验证执行失败: {e}")
            return ValidationResult(
                round_number=round_number,
                validation_type=validation_type,
                is_passed=False,
                confidence_score=0.0,
                issues_found=[f"验证执行失败: {str(e)}"],
                improvement_suggestions=["请检查系统配置和网络连接"]
            )
    
    async def _simulate_llm_validation(
        self,
        prompt: str,
        session: AnalysisSession,
        validation_type: str,
        threshold: float
    ) -> ValidationResult:
        """模拟LLM验证（实际实现中应调用真实的LLM服务）"""
        # 模拟验证逻辑
        import random
        
        # 基于当前轮数调整置信度
        base_confidence = 0.85 + (session.current_round - 1) * 0.03
        confidence_score = min(base_confidence + random.uniform(-0.05, 0.05), 1.0)
        
        is_passed = confidence_score >= threshold
        
        # 模拟发现的问题和改进建议
        issues_found = []
        improvement_suggestions = []
        
        if not is_passed:
            if validation_type == "consistency":
                issues_found.append("角色描述存在不一致")
                improvement_suggestions.append("统一角色特征描述")
            elif validation_type == "accuracy":
                issues_found.append("部分情节理解有偏差")
                improvement_suggestions.append("重新分析关键情节")
            elif validation_type == "quality":
                issues_found.append("分析深度不够")
                improvement_suggestions.append("增加分析维度和细节")
        
        # 模拟修正后的内容
        corrected_content = None
        if is_passed and session.current_round > 1:
            corrected_content = self._simulate_corrected_content(session.analysis_results)
        
        return ValidationResult(
            round_number=session.current_round,
            validation_type=validation_type,
            is_passed=is_passed,
            confidence_score=confidence_score,
            issues_found=issues_found,
            improvement_suggestions=improvement_suggestions,
            corrected_content=corrected_content
        )
    
    def _simulate_corrected_content(self, analysis_results: Dict[str, Any]) -> str:
        """模拟修正后的内容"""
        # 这里应该实现实际的内容修正逻辑
        corrected = analysis_results.copy()
        corrected["last_corrected"] = datetime.now().isoformat()
        corrected["correction_notes"] = "已根据验证结果进行修正"
        return json.dumps(corrected, ensure_ascii=False)
    
    def _get_validation_points(self, validation_type: str) -> List[str]:
        """获取验证要点"""
        validation_points = {
            "consistency": [
                "角色描述一致性",
                "情节逻辑一致性",
                "时间线一致性",
                "设定一致性"
            ],
            "accuracy": [
                "事实准确性",
                "理解准确性",
                "推理准确性",
                "引用准确性"
            ],
            "quality": [
                "分析深度",
                "分析广度",
                "逻辑清晰度",
                "实用性"
            ],
            "completeness": [
                "信息完整性",
                "分析完整性",
                "覆盖完整性",
                "结构完整性"
            ]
        }
        
        return validation_points.get(validation_type, [])
    
    def _calculate_overall_confidence(self, session: AnalysisSession) -> float:
        """计算整体置信度"""
        if not session.validation_history:
            return 0.0
        
        # 获取最新一轮的验证结果
        latest_round = max(session.validation_history, key=lambda x: x.round_number)
        latest_results = [
            result for result in session.validation_history
            if result.round_number == latest_round.round_number
        ]
        
        if not latest_results:
            return 0.0
        
        # 计算加权平均置信度
        total_score = 0.0
        total_weight = 0.0
        
        for result in latest_results:
            strategy = self.validation_strategies.get(result.validation_type, {})
            weight = strategy.get("priority", 1)
            total_score += result.confidence_score * weight
            total_weight += weight
        
        return total_score / total_weight if total_weight > 0 else 0.0
    
    def _has_improvement_potential(self, session: AnalysisSession) -> bool:
        """检查是否还有改进空间"""
        if not session.validation_history:
            return True
        
        # 检查最新一轮是否有失败的验证
        latest_round = max(session.validation_history, key=lambda x: x.round_number)
        latest_results = [
            result for result in session.validation_history
            if result.round_number == latest_round.round_number
        ]
        
        return any(not result.is_passed for result in latest_results)
    
    def _update_analysis_results(
        self,
        current_results: Dict[str, Any],
        corrected_content: str
    ) -> Dict[str, Any]:
        """更新分析结果"""
        try:
            corrected_data = json.loads(corrected_content)
            # 合并修正后的内容
            updated_results = current_results.copy()
            updated_results.update(corrected_data)
            return updated_results
        except json.JSONDecodeError:
            logger.warning("修正内容格式错误，保持原结果")
            return current_results
    
    def get_session(self, session_id: str) -> Optional[AnalysisSession]:
        """获取分析会话"""
        return self.sessions.get(session_id)
    
    def get_session_summary(self, session_id: str) -> Dict[str, Any]:
        """获取会话摘要"""
        session = self.get_session(session_id)
        if not session:
            return {}
        
        return {
            "session_id": session.session_id,
            "chapter_id": session.chapter_id,
            "current_round": session.current_round,
            "max_rounds": session.max_rounds,
            "overall_confidence": session.overall_confidence,
            "status": session.status,
            "validation_count": len(session.validation_history),
            "created_at": session.created_at.isoformat(),
            "updated_at": session.updated_at.isoformat()
        }
    
    def get_validation_report(self, session_id: str) -> Dict[str, Any]:
        """获取验证报告"""
        session = self.get_session(session_id)
        if not session:
            return {}
        
        # 按轮数分组验证结果
        rounds_summary = {}
        for result in session.validation_history:
            round_num = result.round_number
            if round_num not in rounds_summary:
                rounds_summary[round_num] = []
            rounds_summary[round_num].append({
                "validation_type": result.validation_type,
                "is_passed": result.is_passed,
                "confidence_score": result.confidence_score,
                "issues_found": result.issues_found,
                "improvement_suggestions": result.improvement_suggestions
            })
        
        return {
            "session_id": session.session_id,
            "overall_confidence": session.overall_confidence,
            "status": session.status,
            "rounds_summary": rounds_summary,
            "total_validations": len(session.validation_history)
        }

# 创建全局多轮验证器实例
multi_round_validator = MultiRoundValidator()
