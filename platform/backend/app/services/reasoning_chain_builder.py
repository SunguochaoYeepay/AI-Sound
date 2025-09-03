"""
智能推理引擎 - 推理链构建器
实现高级推理能力和逻辑分析，提升AI分析深度和准确性
"""

import json
import logging
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from app.services.context_manager import context_manager

logger = logging.getLogger(__name__)

class ReasoningType(Enum):
    """推理类型枚举"""
    CAUSAL = "causal"           # 因果推理
    TEMPORAL = "temporal"       # 时序推理
    LOGICAL = "logical"         # 逻辑推理
    INFERENTIAL = "inferential" # 推断推理
    ANALOGICAL = "analogical"   # 类比推理

class ReasoningStep(Enum):
    """推理步骤枚举"""
    OBSERVATION = "observation"     # 观察
    HYPOTHESIS = "hypothesis"      # 假设
    EVIDENCE = "evidence"          # 证据
    REASONING = "reasoning"        # 推理
    CONCLUSION = "conclusion"      # 结论
    VALIDATION = "validation"      # 验证

@dataclass
class ReasoningNode:
    """推理节点数据类"""
    node_id: str
    step_type: ReasoningStep
    content: str
    confidence: float
    evidence: List[str]
    dependencies: List[str]
    timestamp: datetime
    metadata: Dict[str, Any]

@dataclass
class ReasoningChain:
    """推理链数据类"""
    chain_id: str
    reasoning_type: ReasoningType
    nodes: List[ReasoningNode]
    start_time: datetime
    end_time: Optional[datetime]
    confidence_score: float
    validation_status: str
    metadata: Dict[str, Any]

class ReasoningChainBuilder:
    """推理链构建器"""
    
    def __init__(self):
        self.reasoning_chains: Dict[str, ReasoningChain] = {}
        self.reasoning_rules = self._initialize_reasoning_rules()
        self.chain_counter = 0
    
    def _initialize_reasoning_rules(self) -> Dict[ReasoningType, Dict[str, Any]]:
        """初始化推理规则"""
        return {
            ReasoningType.CAUSAL: {
                "description": "因果推理规则",
                "required_steps": [ReasoningStep.OBSERVATION, ReasoningStep.HYPOTHESIS, ReasoningStep.EVIDENCE, ReasoningStep.CONCLUSION],
                "confidence_threshold": 0.8,
                "max_hypotheses": 3,
                "validation_required": True
            },
            ReasoningType.TEMPORAL: {
                "description": "时序推理规则",
                "required_steps": [ReasoningStep.OBSERVATION, ReasoningStep.EVIDENCE, ReasoningStep.REASONING, ReasoningStep.CONCLUSION],
                "confidence_threshold": 0.75,
                "max_hypotheses": 2,
                "validation_required": False
            },
            ReasoningType.LOGICAL: {
                "description": "逻辑推理规则",
                "required_steps": [ReasoningStep.OBSERVATION, ReasoningStep.REASONING, ReasoningStep.CONCLUSION],
                "confidence_threshold": 0.9,
                "max_hypotheses": 1,
                "validation_required": True
            },
            ReasoningType.INFERENTIAL: {
                "description": "推断推理规则",
                "required_steps": [ReasoningStep.OBSERVATION, ReasoningStep.HYPOTHESIS, ReasoningStep.EVIDENCE, ReasoningStep.CONCLUSION],
                "confidence_threshold": 0.7,
                "max_hypotheses": 4,
                "validation_required": False
            },
            ReasoningType.ANALOGICAL: {
                "description": "类比推理规则",
                "required_steps": [ReasoningStep.OBSERVATION, ReasoningStep.EVIDENCE, ReasoningStep.REASONING, ReasoningStep.CONCLUSION],
                "confidence_threshold": 0.6,
                "max_hypotheses": 3,
                "validation_required": False
            }
        }
    
    def create_reasoning_chain(
        self,
        reasoning_type: ReasoningType,
        initial_observation: str,
        session_id: str,
        chapter_id: int
    ) -> ReasoningChain:
        """创建推理链"""
        chain_id = f"chain_{self.chain_counter}_{reasoning_type.value}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.chain_counter += 1
        
        # 创建初始观察节点
        observation_node = ReasoningNode(
            node_id=f"{chain_id}_obs_1",
            step_type=ReasoningStep.OBSERVATION,
            content=initial_observation,
            confidence=0.9,
            evidence=[initial_observation],
            dependencies=[],
            timestamp=datetime.now(),
            metadata={"source": "user_input", "session_id": session_id, "chapter_id": chapter_id}
        )
        
        # 创建推理链
        reasoning_chain = ReasoningChain(
            chain_id=chain_id,
            reasoning_type=reasoning_type,
            nodes=[observation_node],
            start_time=datetime.now(),
            end_time=None,
            confidence_score=0.9,
            validation_status="in_progress",
            metadata={
                "session_id": session_id,
                "chapter_id": chapter_id,
                "created_by": "reasoning_engine"
            }
        )
        
        self.reasoning_chains[chain_id] = reasoning_chain
        logger.info(f"创建推理链: {chain_id}, 类型: {reasoning_type.value}")
        
        return reasoning_chain
    
    def add_reasoning_step(
        self,
        chain_id: str,
        step_type: ReasoningStep,
        content: str,
        confidence: float,
        evidence: List[str],
        dependencies: Optional[List[str]] = None
    ) -> Optional[ReasoningNode]:
        """添加推理步骤"""
        if chain_id not in self.reasoning_chains:
            logger.error(f"推理链不存在: {chain_id}")
            return None
        
        reasoning_chain = self.reasoning_chains[chain_id]
        
        # 验证步骤类型是否符合推理规则
        if not self._validate_step_type(reasoning_chain.reasoning_type, step_type):
            logger.warning(f"步骤类型 {step_type.value} 不符合推理类型 {reasoning_chain.reasoning_type.value} 的规则")
            return None
        
        # 创建推理节点
        node_id = f"{chain_id}_{step_type.value}_{len(reasoning_chain.nodes) + 1}"
        reasoning_node = ReasoningNode(
            node_id=node_id,
            step_type=step_type,
            content=content,
            confidence=confidence,
            evidence=evidence or [],
            dependencies=dependencies or [],
            timestamp=datetime.now(),
            metadata={"step_number": len(reasoning_chain.nodes) + 1}
        )
        
        # 添加到推理链
        reasoning_chain.nodes.append(reasoning_node)
        
        # 更新置信度
        self._update_chain_confidence(reasoning_chain)
        
        logger.info(f"添加推理步骤: {node_id}, 类型: {step_type.value}")
        return reasoning_node
    
    def _validate_step_type(self, reasoning_type: ReasoningType, step_type: ReasoningStep) -> bool:
        """验证步骤类型是否符合推理规则"""
        rules = self.reasoning_rules[reasoning_type]
        required_steps = rules["required_steps"]
        
        # 检查是否是必需步骤
        if step_type in required_steps:
            return True
        
        # 检查是否允许可选步骤
        return True  # 目前允许所有步骤类型
    
    def _update_chain_confidence(self, reasoning_chain: ReasoningChain):
        """更新推理链置信度"""
        if not reasoning_chain.nodes:
            reasoning_chain.confidence_score = 0.0
            return
        
        # 计算加权平均置信度
        total_weight = 0
        weighted_sum = 0
        
        for node in reasoning_chain.nodes:
            # 根据步骤类型分配权重
            weight = self._get_step_weight(node.step_type)
            weighted_sum += node.confidence * weight
            total_weight += weight
        
        if total_weight > 0:
            reasoning_chain.confidence_score = weighted_sum / total_weight
        else:
            reasoning_chain.confidence_score = 0.0
    
    def _get_step_weight(self, step_type: ReasoningStep) -> float:
        """获取步骤权重"""
        weights = {
            ReasoningStep.OBSERVATION: 1.0,
            ReasoningStep.HYPOTHESIS: 0.8,
            ReasoningStep.EVIDENCE: 1.2,
            ReasoningStep.REASONING: 1.5,
            ReasoningStep.CONCLUSION: 1.3,
            ReasoningStep.VALIDATION: 1.1
        }
        return weights.get(step_type, 1.0)
    
    def build_causal_chain(
        self,
        event: str,
        context: str,
        session_id: str,
        chapter_id: int
    ) -> ReasoningChain:
        """构建因果推理链"""
        # 创建因果推理链
        chain = self.create_reasoning_chain(
            ReasoningType.CAUSAL,
            f"观察事件: {event}",
            session_id,
            chapter_id
        )
        
        # 添加假设步骤
        hypothesis_content = f"基于上下文分析，{event}可能的原因包括："
        self.add_reasoning_step(
            chain.chain_id,
            ReasoningStep.HYPOTHESIS,
            hypothesis_content,
            0.7,
            [context]
        )
        
        # 添加证据步骤
        evidence_content = f"从上下文提取的证据：{context}"
        self.add_reasoning_step(
            chain.chain_id,
            ReasoningStep.EVIDENCE,
            evidence_content,
            0.8,
            [context]
        )
        
        # 添加推理步骤
        reasoning_content = f"通过因果分析，{event}与上下文中的要素存在逻辑关联"
        self.add_reasoning_step(
            chain.chain_id,
            ReasoningStep.REASONING,
            reasoning_content,
            0.75,
            [event, context]
        )
        
        # 添加结论步骤
        conclusion_content = f"结论：{event}是由上下文中的相关因素引起的"
        self.add_reasoning_step(
            chain.chain_id,
            ReasoningStep.CONCLUSION,
            conclusion_content,
            0.8,
            [event, context]
        )
        
        return chain
    
    def build_temporal_chain(
        self,
        events: List[str],
        session_id: str,
        chapter_id: int
    ) -> ReasoningChain:
        """构建时序推理链"""
        # 创建时序推理链
        chain = self.create_reasoning_chain(
            ReasoningType.TEMPORAL,
            f"观察时序事件: {' -> '.join(events)}",
            session_id,
            chapter_id
        )
        
        # 添加证据步骤
        evidence_content = f"时序证据：{', '.join(events)}"
        self.add_reasoning_step(
            chain.chain_id,
            ReasoningStep.EVIDENCE,
            evidence_content,
            0.9,
            events
        )
        
        # 添加推理步骤
        reasoning_content = f"时序逻辑分析：事件按时间顺序发展，存在因果关系"
        self.add_reasoning_step(
            chain.chain_id,
            ReasoningStep.REASONING,
            reasoning_content,
            0.8,
            events
        )
        
        # 添加结论步骤
        conclusion_content = f"结论：事件发展符合时序逻辑，具有连贯性"
        self.add_reasoning_step(
            chain.chain_id,
            ReasoningStep.CONCLUSION,
            conclusion_content,
            0.85,
            events
        )
        
        return chain
    
    def build_logical_chain(
        self,
        premises: List[str],
        conclusion: str,
        session_id: str,
        chapter_id: int
    ) -> ReasoningChain:
        """构建逻辑推理链"""
        # 创建逻辑推理链
        chain = self.create_reasoning_chain(
            ReasoningType.LOGICAL,
            f"逻辑前提: {'; '.join(premises)}",
            session_id,
            chapter_id
        )
        
        # 添加推理步骤
        reasoning_content = f"逻辑推理：从前提 {' + '.join(premises)} 推导出结论"
        self.add_reasoning_step(
            chain.chain_id,
            ReasoningStep.REASONING,
            reasoning_content,
            0.9,
            premises
        )
        
        # 添加结论步骤
        conclusion_content = f"逻辑结论：{conclusion}"
        self.add_reasoning_step(
            chain.chain_id,
            ReasoningStep.CONCLUSION,
            conclusion_content,
            0.95,
            [conclusion]
        )
        
        return chain
    
    def validate_reasoning_chain(self, chain_id: str) -> Dict[str, Any]:
        """验证推理链"""
        if chain_id not in self.reasoning_chains:
            return {"valid": False, "error": "推理链不存在"}
        
        reasoning_chain = self.reasoning_chains[chain_id]
        rules = self.reasoning_rules[reasoning_chain.reasoning_type]
        
        validation_result = {
            "valid": True,
            "chain_id": chain_id,
            "reasoning_type": reasoning_chain.reasoning_type.value,
            "validation_checks": [],
            "overall_score": 0.0
        }
        
        # 检查必需步骤
        required_steps = rules["required_steps"]
        missing_steps = []
        for step in required_steps:
            if not any(node.step_type == step for node in reasoning_chain.nodes):
                missing_steps.append(step.value)
        
        if missing_steps:
            validation_result["valid"] = False
            validation_result["validation_checks"].append({
                "check": "required_steps",
                "status": "failed",
                "details": f"缺少必需步骤: {', '.join(missing_steps)}"
            })
        else:
            validation_result["validation_checks"].append({
                "check": "required_steps",
                "status": "passed",
                "details": "所有必需步骤都存在"
            })
        
        # 检查置信度阈值
        confidence_threshold = rules["confidence_threshold"]
        if reasoning_chain.confidence_score < confidence_threshold:
            validation_result["validation_checks"].append({
                "check": "confidence_threshold",
                "status": "warning",
                "details": f"置信度 {reasoning_chain.confidence_score:.3f} 低于阈值 {confidence_threshold}"
            })
        else:
            validation_result["validation_checks"].append({
                "check": "confidence_threshold",
                "status": "passed",
                "details": f"置信度 {reasoning_chain.confidence_score:.3f} 达到阈值"
            })
        
        # 计算整体评分
        passed_checks = sum(1 for check in validation_result["validation_checks"] if check["status"] == "passed")
        total_checks = len(validation_result["validation_checks"])
        validation_result["overall_score"] = passed_checks / total_checks if total_checks > 0 else 0.0
        
        # 更新验证状态
        if validation_result["valid"] and validation_result["overall_score"] >= 0.8:
            reasoning_chain.validation_status = "validated"
        elif validation_result["overall_score"] >= 0.6:
            reasoning_chain.validation_status = "partially_validated"
        else:
            reasoning_chain.validation_status = "validation_failed"
        
        return validation_result
    
    def get_reasoning_chain(self, chain_id: str) -> Optional[ReasoningChain]:
        """获取推理链"""
        return self.reasoning_chains.get(chain_id)
    
    def get_all_chains(self, session_id: Optional[str] = None) -> List[ReasoningChain]:
        """获取所有推理链"""
        if session_id is None:
            return list(self.reasoning_chains.values())
        
        return [
            chain for chain in self.reasoning_chains.values()
            if chain.metadata.get("session_id") == session_id
        ]
    
    def complete_reasoning_chain(self, chain_id: str) -> bool:
        """完成推理链"""
        if chain_id not in self.reasoning_chains:
            return False
        
        reasoning_chain = self.reasoning_chains[chain_id]
        reasoning_chain.end_time = datetime.now()
        
        # 最终验证
        validation_result = self.validate_reasoning_chain(chain_id)
        if validation_result["valid"]:
            reasoning_chain.validation_status = "completed"
            logger.info(f"推理链完成: {chain_id}")
            return True
        else:
            reasoning_chain.validation_status = "completed_with_issues"
            logger.warning(f"推理链完成但存在问题: {chain_id}")
            return False

# 创建全局推理链构建器实例
reasoning_chain_builder = ReasoningChainBuilder()
