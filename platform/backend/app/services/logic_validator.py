"""
智能推理引擎 - 逻辑验证器
实现逻辑一致性检查、推理结果验证和矛盾检测与解决
"""

import json
import logging
import re
from typing import Dict, Any, List, Optional, Tuple, Set
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from app.services.reasoning_chain_builder import reasoning_chain_builder, ReasoningChain, ReasoningNode

logger = logging.getLogger(__name__)

class ValidationLevel(Enum):
    """验证级别枚举"""
    CRITICAL = "critical"       # 关键错误
    WARNING = "warning"         # 警告
    INFO = "info"              # 信息
    SUCCESS = "success"         # 成功

class LogicRule(Enum):
    """逻辑规则枚举"""
    NON_CONTRADICTION = "non_contradiction"    # 非矛盾律
    IDENTITY = "identity"                      # 同一律
    EXCLUDED_MIDDLE = "excluded_middle"       # 排中律
    CAUSALITY = "causality"                   # 因果律
    TEMPORAL_ORDER = "temporal_order"         # 时序律
    CONSISTENCY = "consistency"               # 一致性

@dataclass
class ValidationIssue:
    """验证问题数据类"""
    issue_id: str
    issue_type: str
    level: ValidationLevel
    description: str
    location: str
    evidence: List[str]
    suggested_fix: str
    timestamp: datetime
    resolved: bool = False

@dataclass
class ValidationResult:
    """验证结果数据类"""
    chain_id: str
    overall_valid: bool
    validation_score: float
    issues: List[ValidationIssue]
    passed_checks: int
    total_checks: int
    validation_time: datetime
    metadata: Dict[str, Any]

class LogicValidator:
    """逻辑验证器"""
    
    def __init__(self):
        self.validation_rules = self._initialize_validation_rules()
        self.issue_counter = 0
        self.validation_history: Dict[str, ValidationResult] = {}
    
    def _initialize_validation_rules(self) -> Dict[LogicRule, Dict[str, Any]]:
        """初始化验证规则"""
        return {
            LogicRule.NON_CONTRADICTION: {
                "description": "非矛盾律：不能同时为真和假",
                "priority": 1,
                "check_function": self._check_non_contradiction,
                "weight": 1.0
            },
            LogicRule.IDENTITY: {
                "description": "同一律：概念在推理过程中保持一致",
                "priority": 2,
                "check_function": self._check_identity,
                "weight": 0.8
            },
            LogicRule.EXCLUDED_MIDDLE: {
                "description": "排中律：命题要么为真要么为假",
                "priority": 3,
                "check_function": self._check_excluded_middle,
                "weight": 0.7
            },
            LogicRule.CAUSALITY: {
                "description": "因果律：因果关系逻辑合理",
                "priority": 4,
                "check_function": self._check_causality,
                "weight": 0.9
            },
            LogicRule.TEMPORAL_ORDER: {
                "description": "时序律：时间顺序逻辑合理",
                "priority": 5,
                "check_function": self._check_temporal_order,
                "weight": 0.8
            },
            LogicRule.CONSISTENCY: {
                "description": "一致性：推理过程保持逻辑一致",
                "priority": 6,
                "check_function": self._check_consistency,
                "weight": 1.0
            }
        }
    
    def validate_reasoning_chain(self, chain_id: str) -> ValidationResult:
        """验证推理链"""
        start_time = datetime.now()
        
        # 获取推理链
        reasoning_chain = reasoning_chain_builder.get_reasoning_chain(chain_id)
        if not reasoning_chain:
            return ValidationResult(
                chain_id=chain_id,
                overall_valid=False,
                validation_score=0.0,
                issues=[],
                passed_checks=0,
                total_checks=0,
                validation_time=start_time,
                metadata={"error": "推理链不存在"}
            )
        
        # 执行所有验证检查
        all_issues = []
        passed_checks = 0
        total_checks = 0
        
        for rule_enum, rule_config in self.validation_rules.items():
            try:
                check_function = rule_config["check_function"]
                issues = check_function(reasoning_chain)
                
                if issues:
                    all_issues.extend(issues)
                    total_checks += 1
                else:
                    passed_checks += 1
                    total_checks += 1
                    
            except Exception as e:
                logger.error(f"验证规则 {rule_enum.value} 执行失败: {e}")
                # 创建验证错误问题
                error_issue = ValidationIssue(
                    issue_id=f"error_{self.issue_counter}",
                    issue_type="validation_error",
                    level=ValidationLevel.CRITICAL,
                    description=f"验证规则执行失败: {rule_enum.value}",
                    location="validation_engine",
                    evidence=[str(e)],
                    suggested_fix="检查验证规则配置",
                    timestamp=datetime.now()
                )
                all_issues.append(error_issue)
                self.issue_counter += 1
                total_checks += 1
        
        # 计算验证分数
        validation_score = passed_checks / total_checks if total_checks > 0 else 0.0
        
        # 确定整体有效性
        critical_issues = [issue for issue in all_issues if issue.level == ValidationLevel.CRITICAL]
        overall_valid = len(critical_issues) == 0 and validation_score >= 0.7
        
        # 创建验证结果
        validation_result = ValidationResult(
            chain_id=chain_id,
            overall_valid=overall_valid,
            validation_score=validation_score,
            issues=all_issues,
            passed_checks=passed_checks,
            total_checks=total_checks,
            validation_time=start_time,
            metadata={
                "reasoning_type": reasoning_chain.reasoning_type.value,
                "node_count": len(reasoning_chain.nodes),
                "confidence_score": reasoning_chain.confidence_score
            }
        )
        
        # 保存验证历史
        self.validation_history[chain_id] = validation_result
        
        logger.info(f"推理链验证完成: {chain_id}, 分数: {validation_score:.3f}, 有效: {overall_valid}")
        return validation_result
    
    def _check_non_contradiction(self, reasoning_chain: ReasoningChain) -> List[ValidationIssue]:
        """检查非矛盾律"""
        issues = []
        contradictions = []
        
        # 检查节点内容中的矛盾
        for i, node1 in enumerate(reasoning_chain.nodes):
            for j, node2 in enumerate(reasoning_chain.nodes[i+1:], i+1):
                if self._has_contradiction(node1.content, node2.content):
                    contradictions.append((node1, node2))
        
        # 创建验证问题
        for node1, node2 in contradictions:
            issue = ValidationIssue(
                issue_id=f"contradiction_{self.issue_counter}",
                issue_type="contradiction",
                level=ValidationLevel.CRITICAL,
                description=f"发现逻辑矛盾：节点 {node1.node_id} 与 {node2.node_id}",
                location=f"节点 {node1.node_id} 和 {node2.node_id}",
                evidence=[node1.content, node2.content],
                suggested_fix="检查并修正矛盾的内容，确保逻辑一致",
                timestamp=datetime.now()
            )
            issues.append(issue)
            self.issue_counter += 1
        
        return issues
    
    def _check_identity(self, reasoning_chain: ReasoningChain) -> List[ValidationIssue]:
        """检查同一律"""
        issues = []
        concept_changes = []
        
        # 检查概念一致性
        concept_mapping = {}
        for node in reasoning_chain.nodes:
            concepts = self._extract_concepts(node.content)
            for concept in concepts:
                if concept in concept_mapping:
                    if concept_mapping[concept] != node.content:
                        concept_changes.append((concept, concept_mapping[concept], node.content))
                else:
                    concept_mapping[concept] = node.content
        
        # 创建验证问题
        for concept, old_content, new_content in concept_changes:
            issue = ValidationIssue(
                issue_id=f"identity_{self.issue_counter}",
                issue_type="identity_violation",
                level=ValidationLevel.WARNING,
                description=f"概念 '{concept}' 在不同节点中的定义不一致",
                location=f"概念: {concept}",
                evidence=[old_content, new_content],
                suggested_fix="统一概念定义，确保概念在推理过程中保持一致",
                timestamp=datetime.now()
            )
            issues.append(issue)
            self.issue_counter += 1
        
        return issues
    
    def _check_excluded_middle(self, reasoning_chain: ReasoningChain) -> List[ValidationIssue]:
        """检查排中律"""
        issues = []
        
        # 检查是否有明确的真假判断
        for node in reasoning_chain.nodes:
            if self._has_ambiguous_truth_value(node.content):
                issue = ValidationIssue(
                    issue_id=f"excluded_middle_{self.issue_counter}",
                    issue_type="ambiguous_truth",
                    level=ValidationLevel.WARNING,
                    description=f"节点 {node.node_id} 的真假值不明确",
                    location=f"节点: {node.node_id}",
                    evidence=[node.content],
                    suggested_fix="明确表达命题的真假值，避免模糊表述",
                    timestamp=datetime.now()
                )
                issues.append(issue)
                self.issue_counter += 1
        
        return issues
    
    def _check_causality(self, reasoning_chain: ReasoningChain) -> List[ValidationIssue]:
        """检查因果律"""
        issues = []
        
        # 检查因果关系逻辑
        for i, node1 in enumerate(reasoning_chain.nodes):
            for j, node2 in enumerate(reasoning_chain.nodes[i+1:], i+1):
                if self._has_invalid_causality(node1.content, node2.content):
                    issue = ValidationIssue(
                        issue_id=f"causality_{self.issue_counter}",
                        issue_type="invalid_causality",
                        level=ValidationLevel.WARNING,
                        description=f"节点 {node1.node_id} 与 {node2.node_id} 的因果关系不合理",
                        location=f"节点: {node1.node_id} -> {node2.node_id}",
                        evidence=[node1.content, node2.content],
                        suggested_fix="检查因果关系逻辑，确保因果链条合理",
                        timestamp=datetime.now()
                    )
                    issues.append(issue)
                    self.issue_counter += 1
        
        return issues
    
    def _check_temporal_order(self, reasoning_chain: ReasoningChain) -> List[ValidationIssue]:
        """检查时序律"""
        issues = []
        
        # 检查时间顺序逻辑
        temporal_events = []
        for node in reasoning_chain.nodes:
            temporal_info = self._extract_temporal_info(node.content)
            if temporal_info:
                temporal_events.append((node, temporal_info))
        
        # 检查时序一致性
        for i, (node1, time1) in enumerate(temporal_events):
            for j, (node2, time2) in enumerate(temporal_events[i+1:], i+1):
                if self._has_temporal_conflict(time1, time2):
                    issue = ValidationIssue(
                        issue_id=f"temporal_{self.issue_counter}",
                        issue_type="temporal_conflict",
                        level=ValidationLevel.WARNING,
                        description=f"节点 {node1.node_id} 与 {node2.node_id} 的时间顺序冲突",
                        location=f"节点: {node1.node_id} -> {node2.node_id}",
                        evidence=[f"{node1.content} (时间: {time1})", f"{node2.content} (时间: {time2})"],
                        suggested_fix="检查并修正时间顺序，确保时序逻辑一致",
                        timestamp=datetime.now()
                    )
                    issues.append(issue)
                    self.issue_counter += 1
        
        return issues
    
    def _check_consistency(self, reasoning_chain: ReasoningChain) -> List[ValidationIssue]:
        """检查一致性"""
        issues = []
        
        # 检查推理过程的一致性
        if len(reasoning_chain.nodes) < 2:
            return issues
        
        # 检查相邻节点的逻辑连贯性
        for i in range(len(reasoning_chain.nodes) - 1):
            node1 = reasoning_chain.nodes[i]
            node2 = reasoning_chain.nodes[i + 1]
            
            if not self._are_nodes_logically_connected(node1, node2):
                issue = ValidationIssue(
                    issue_id=f"consistency_{self.issue_counter}",
                    issue_type="logical_disconnection",
                    level=ValidationLevel.WARNING,
                    description=f"节点 {node1.node_id} 与 {node2.node_id} 逻辑连接不紧密",
                    location=f"节点: {node1.node_id} -> {node2.node_id}",
                    evidence=[node1.content, node2.content],
                    suggested_fix="增强节点间的逻辑连接，确保推理过程连贯",
                    timestamp=datetime.now()
                )
                issues.append(issue)
                self.issue_counter += 1
        
        return issues
    
    def _has_contradiction(self, content1: str, content2: str) -> bool:
        """检查两个内容是否存在矛盾"""
        # 简单的矛盾检测逻辑
        contradictions = [
            ("是", "不是"),
            ("有", "没有"),
            ("存在", "不存在"),
            ("正确", "错误"),
            ("真", "假")
        ]
        
        for pos, neg in contradictions:
            if pos in content1 and neg in content2:
                return True
            if neg in content1 and pos in content2:
                return True
        
        return False
    
    def _extract_concepts(self, content: str) -> List[str]:
        """提取内容中的概念"""
        # 简单的概念提取逻辑
        concepts = []
        
        # 提取引号中的概念
        quoted_concepts = re.findall(r'[""]([^""]+)[""]', content)
        concepts.extend(quoted_concepts)
        
        # 提取"的"前面的概念
        de_concepts = re.findall(r'([^，。！？]+)的', content)
        concepts.extend(de_concepts)
        
        return list(set(concepts))
    
    def _has_ambiguous_truth_value(self, content: str) -> bool:
        """检查内容是否有模糊的真假值"""
        ambiguous_patterns = [
            r'可能',
            r'也许',
            r'大概',
            r'似乎',
            r'看起来',
            r'不确定'
        ]
        
        for pattern in ambiguous_patterns:
            if re.search(pattern, content):
                return True
        
        return False
    
    def _has_invalid_causality(self, content1: str, content2: str) -> bool:
        """检查因果关系是否合理"""
        # 简单的因果合理性检查
        causal_keywords = [
            "因为", "由于", "所以", "因此", "导致", "引起", "造成"
        ]
        
        has_causal_keyword = any(keyword in content1 or keyword in content2 for keyword in causal_keywords)
        
        # 如果有关键词但逻辑不合理，则标记为问题
        if has_causal_keyword:
            # 这里可以添加更复杂的因果逻辑检查
            return False
        
        return False
    
    def _extract_temporal_info(self, content: str) -> Optional[str]:
        """提取时间信息"""
        temporal_patterns = [
            r'([^，。！？]*时[^，。！？]*)',
            r'([^，。！？]*前[^，。！？]*)',
            r'([^，。！？]*后[^，。！？]*)',
            r'([^，。！？]*期间[^，。！？]*)'
        ]
        
        for pattern in temporal_patterns:
            match = re.search(pattern, content)
            if match:
                return match.group(1)
        
        return None
    
    def _has_temporal_conflict(self, time1: str, time2: str) -> bool:
        """检查时间冲突"""
        # 简单的时间冲突检测
        if "前" in time1 and "后" in time2:
            return False  # 时间顺序正确
        elif "后" in time1 and "前" in time2:
            return True   # 时间顺序错误
        
        return False
    
    def _are_nodes_logically_connected(self, node1: ReasoningNode, node2: ReasoningNode) -> bool:
        """检查两个节点是否逻辑连接"""
        # 检查是否有共同的证据或依赖
        common_evidence = set(node1.evidence) & set(node2.evidence)
        if common_evidence:
            return True
        
        # 检查依赖关系
        if node2.node_id in node1.dependencies or node1.node_id in node2.dependencies:
            return True
        
        # 检查内容相似性
        content_similarity = self._calculate_content_similarity(node1.content, node2.content)
        return content_similarity > 0.3
    
    def _calculate_content_similarity(self, content1: str, content2: str) -> float:
        """计算内容相似性"""
        words1 = set(content1.split())
        words2 = set(content2.split())
        
        if not words1 and not words2:
            return 1.0
        
        intersection = len(words1 & words2)
        union = len(words1 | words2)
        
        return intersection / union if union > 0 else 0.0
    
    def get_validation_history(self, chain_id: Optional[str] = None) -> Dict[str, ValidationResult]:
        """获取验证历史"""
        if chain_id is None:
            return self.validation_history
        
        return {chain_id: self.validation_history.get(chain_id)} if chain_id in self.validation_history else {}
    
    def resolve_validation_issue(self, chain_id: str, issue_id: str) -> bool:
        """解决验证问题"""
        if chain_id not in self.validation_history:
            return False
        
        validation_result = self.validation_history[chain_id]
        for issue in validation_result.issues:
            if issue.issue_id == issue_id:
                issue.resolved = True
                logger.info(f"验证问题已解决: {issue_id}")
                return True
        
        return False
    
    def get_validation_summary(self, chain_id: str) -> Dict[str, Any]:
        """获取验证摘要"""
        if chain_id not in self.validation_history:
            return {}
        
        validation_result = self.validation_history[chain_id]
        
        # 按级别统计问题
        issue_summary = {
            "critical": len([i for i in validation_result.issues if i.level == ValidationLevel.CRITICAL]),
            "warning": len([i for i in validation_result.issues if i.level == ValidationLevel.WARNING]),
            "info": len([i for i in validation_result.issues if i.level == ValidationLevel.INFO]),
            "success": len([i for i in validation_result.issues if i.level == ValidationLevel.SUCCESS])
        }
        
        # 按类型统计问题
        type_summary = {}
        for issue in validation_result.issues:
            issue_type = issue.issue_type
            type_summary[issue_type] = type_summary.get(issue_type, 0) + 1
        
        return {
            "chain_id": chain_id,
            "overall_valid": validation_result.overall_valid,
            "validation_score": validation_result.validation_score,
            "issue_summary": issue_summary,
            "type_summary": type_summary,
            "passed_checks": validation_result.passed_checks,
            "total_checks": validation_result.total_checks,
            "validation_time": validation_result.validation_time.isoformat(),
            "metadata": validation_result.metadata
        }

# 创建全局逻辑验证器实例
logic_validator = LogicValidator()
