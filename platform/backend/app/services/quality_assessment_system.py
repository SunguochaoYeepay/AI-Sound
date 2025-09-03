"""
第五阶段：质量评估与优化 - 质量评估系统
实现多维度评估指标、智能评分算法和质量报告生成
"""

import json
import logging
import time
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from app.services.reasoning_chain_builder import reasoning_chain_builder
from app.services.logic_validator import logic_validator

logger = logging.getLogger(__name__)

class QualityDimension(Enum):
    """质量维度枚举"""
    ACCURACY = "accuracy"           # 准确性
    CONSISTENCY = "consistency"     # 一致性
    COMPLETENESS = "completeness"   # 完整性
    RELEVANCE = "relevance"         # 相关性
    COHERENCE = "coherence"         # 连贯性
    EFFICIENCY = "efficiency"       # 效率性

class AssessmentLevel(Enum):
    """评估级别枚举"""
    EXCELLENT = "excellent"         # 优秀 (90-100)
    GOOD = "good"                   # 良好 (80-89)
    SATISFACTORY = "satisfactory"   # 满意 (70-79)
    NEEDS_IMPROVEMENT = "needs_improvement"  # 需改进 (60-69)
    POOR = "poor"                   # 差 (0-59)

@dataclass
class QualityMetric:
    """质量指标数据类"""
    dimension: QualityDimension
    score: float
    weight: float
    description: str
    evidence: List[str]
    suggestions: List[str]
    timestamp: datetime

@dataclass
class QualityAssessment:
    """质量评估结果数据类"""
    assessment_id: str
    session_id: str
    chapter_id: int
    overall_score: float
    level: AssessmentLevel
    metrics: Dict[QualityDimension, QualityMetric]
    summary: str
    recommendations: List[str]
    assessment_time: datetime
    metadata: Dict[str, Any]

class QualityAssessmentSystem:
    """质量评估系统"""
    
    def __init__(self):
        self.assessment_history: Dict[str, QualityAssessment] = {}
        self.quality_standards = self._initialize_quality_standards()
        self.assessment_counter = 0
    
    def _initialize_quality_standards(self) -> Dict[QualityDimension, Dict[str, Any]]:
        """初始化质量标准"""
        return {
            QualityDimension.ACCURACY: {
                "description": "分析结果的准确性",
                "weight": 0.25,
                "target_score": 0.85,
                "assessment_criteria": [
                    "角色识别准确率",
                    "情节分析准确性",
                    "上下文理解正确性"
                ]
            },
            QualityDimension.CONSISTENCY: {
                "description": "分析结果的一致性",
                "weight": 0.20,
                "target_score": 0.80,
                "assessment_criteria": [
                    "概念使用一致性",
                    "逻辑推理一致性",
                    "风格表达一致性"
                ]
            },
            QualityDimension.COMPLETENESS: {
                "description": "分析内容的完整性",
                "weight": 0.20,
                "target_score": 0.85,
                "assessment_criteria": [
                    "内容覆盖完整性",
                    "分析深度充分性",
                    "细节描述完整性"
                ]
            },
            QualityDimension.RELEVANCE: {
                "description": "分析内容的相关性",
                "weight": 0.15,
                "target_score": 0.80,
                "assessment_criteria": [
                    "内容相关性",
                    "重点突出性",
                    "信息价值性"
                ]
            },
            QualityDimension.COHERENCE: {
                "description": "分析逻辑的连贯性",
                "weight": 0.15,
                "target_score": 0.80,
                "assessment_criteria": [
                    "逻辑连贯性",
                    "结构清晰性",
                    "表达流畅性"
                ]
            },
            QualityDimension.EFFICIENCY: {
                "description": "分析过程的效率性",
                "weight": 0.05,
                "target_score": 0.75,
                "assessment_criteria": [
                    "处理速度",
                    "资源消耗",
                    "响应时间"
                ]
            }
        }
    
    def assess_analysis_quality(
        self,
        session_id: str,
        chapter_id: int,
        analysis_results: Dict[str, Any],
        processing_time: float,
        context_data: Optional[Dict[str, Any]] = None
    ) -> QualityAssessment:
        """评估分析质量"""
        start_time = datetime.now()
        
        # 创建评估ID
        assessment_id = f"assessment_{self.assessment_counter}_{session_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.assessment_counter += 1
        
        # 执行各维度评估
        metrics = {}
        total_weighted_score = 0.0
        total_weight = 0.0
        
        for dimension in QualityDimension:
            metric = self._assess_dimension(dimension, analysis_results, processing_time, context_data)
            metrics[dimension] = metric
            
            # 计算加权分数
            weight = self.quality_standards[dimension]["weight"]
            total_weighted_score += metric.score * weight
            total_weight += weight
        
        # 计算整体分数
        overall_score = total_weighted_score / total_weight if total_weight > 0 else 0.0
        
        # 确定评估级别
        level = self._determine_assessment_level(overall_score)
        
        # 生成摘要和建议
        summary = self._generate_assessment_summary(metrics, overall_score, level)
        recommendations = self._generate_recommendations(metrics, overall_score)
        
        # 创建评估结果
        assessment = QualityAssessment(
            assessment_id=assessment_id,
            session_id=session_id,
            chapter_id=chapter_id,
            overall_score=overall_score,
            level=level,
            metrics=metrics,
            summary=summary,
            recommendations=recommendations,
            assessment_time=start_time,
            metadata={
                "processing_time": processing_time,
                "analysis_type": analysis_results.get("analysis_type", "unknown"),
                "model_used": analysis_results.get("model", "unknown")
            }
        )
        
        # 保存评估历史
        self.assessment_history[assessment_id] = assessment
        
        logger.info(f"质量评估完成: {assessment_id}, 分数: {overall_score:.3f}, 级别: {level.value}")
        return assessment
    
    def _assess_dimension(
        self,
        dimension: QualityDimension,
        analysis_results: Dict[str, Any],
        processing_time: float,
        context_data: Optional[Dict[str, Any]]
    ) -> QualityMetric:
        """评估特定维度"""
        standards = self.quality_standards[dimension]
        
        if dimension == QualityDimension.ACCURACY:
            score, evidence, suggestions = self._assess_accuracy(analysis_results, context_data)
        elif dimension == QualityDimension.CONSISTENCY:
            score, evidence, suggestions = self._assess_consistency(analysis_results, context_data)
        elif dimension == QualityDimension.COMPLETENESS:
            score, evidence, suggestions = self._assess_completeness(analysis_results, context_data)
        elif dimension == QualityDimension.RELEVANCE:
            score, evidence, suggestions = self._assess_relevance(analysis_results, context_data)
        elif dimension == QualityDimension.COHERENCE:
            score, evidence, suggestions = self._assess_coherence(analysis_results, context_data)
        elif dimension == QualityDimension.EFFICIENCY:
            score, evidence, suggestions = self._assess_efficiency(processing_time, analysis_results)
        else:
            score, evidence, suggestions = 0.0, ["未知维度"], ["无法评估"]
        
        return QualityMetric(
            dimension=dimension,
            score=score,
            weight=standards["weight"],
            description=standards["description"],
            evidence=evidence,
            suggestions=suggestions,
            timestamp=datetime.now()
        )
    
    def _assess_accuracy(self, analysis_results: Dict[str, Any], context_data: Optional[Dict[str, Any]]) -> Tuple[float, List[str], List[str]]:
        """评估准确性"""
        score = 0.8  # 基础分数
        evidence = []
        suggestions = []
        
        # 检查角色识别准确性
        if "characters" in analysis_results:
            character_count = len(analysis_results["characters"])
            if character_count > 0:
                evidence.append(f"识别到 {character_count} 个角色")
                if character_count >= 3:
                    score += 0.1
                else:
                    suggestions.append("建议增加角色识别数量")
        
        # 检查情节分析准确性
        if "plot_analysis" in analysis_results:
            plot_score = analysis_results.get("plot_confidence", 0.7)
            score = (score + plot_score) / 2
            evidence.append(f"情节分析置信度: {plot_score:.3f}")
        
        # 检查上下文理解
        if context_data and "context_quality" in context_data:
            context_score = context_data["context_quality"]
            score = (score + context_score) / 2
            evidence.append(f"上下文理解质量: {context_score:.3f}")
        
        return min(score, 1.0), evidence, suggestions
    
    def _assess_consistency(self, analysis_results: Dict[str, Any], context_data: Optional[Dict[str, Any]]) -> Tuple[float, List[str], List[str]]:
        """评估一致性"""
        score = 0.8
        evidence = []
        suggestions = []
        
        # 检查概念使用一致性
        if "concepts" in analysis_results:
            concept_count = len(analysis_results["concepts"])
            evidence.append(f"使用 {concept_count} 个核心概念")
            if concept_count >= 5:
                score += 0.1
        
        # 检查逻辑推理一致性
        if "reasoning_chains" in analysis_results:
            chain_count = len(analysis_results["reasoning_chains"])
            evidence.append(f"构建 {chain_count} 个推理链")
            if chain_count >= 2:
                score += 0.1
        
        return min(score, 1.0), evidence, suggestions
    
    def _assess_completeness(self, analysis_results: Dict[str, Any], context_data: Optional[Dict[str, Any]]) -> Tuple[float, List[str], List[str]]:
        """评估完整性"""
        score = 0.8
        evidence = []
        suggestions = []
        
        # 检查内容覆盖
        required_fields = ["characters", "plot_analysis", "scene_description", "emotion_analysis"]
        covered_fields = [field for field in required_fields if field in analysis_results]
        
        coverage_ratio = len(covered_fields) / len(required_fields)
        score = 0.6 + coverage_ratio * 0.4
        
        evidence.append(f"内容覆盖度: {coverage_ratio:.1%}")
        
        if coverage_ratio < 0.8:
            suggestions.append("建议增加分析内容的覆盖范围")
        
        return min(score, 1.0), evidence, suggestions
    
    def _assess_relevance(self, analysis_results: Dict[str, Any], context_data: Optional[Dict[str, Any]]) -> Tuple[float, List[str], List[str]]:
        """评估相关性"""
        score = 0.8
        evidence = []
        suggestions = []
        
        # 检查内容相关性
        if "relevance_score" in analysis_results:
            relevance_score = analysis_results["relevance_score"]
            score = relevance_score
            evidence.append(f"内容相关性评分: {relevance_score:.3f}")
        
        # 检查重点突出性
        if "key_points" in analysis_results:
            key_points_count = len(analysis_results["key_points"])
            evidence.append(f"识别 {key_points_count} 个关键点")
            if key_points_count >= 3:
                score += 0.1
        
        return min(score, 1.0), evidence, suggestions
    
    def _assess_coherence(self, analysis_results: Dict[str, Any], context_data: Optional[Dict[str, Any]]) -> Tuple[float, List[str], List[str]]:
        """评估连贯性"""
        score = 0.8
        evidence = []
        suggestions = []
        
        # 检查逻辑连贯性
        if "logical_flow" in analysis_results:
            flow_score = analysis_results["logical_flow"]
            score = flow_score
            evidence.append(f"逻辑连贯性: {flow_score:.3f}")
        
        # 检查结构清晰性
        if "structure_quality" in analysis_results:
            structure_score = analysis_results["structure_quality"]
            score = (score + structure_score) / 2
            evidence.append(f"结构清晰性: {structure_score:.3f}")
        
        return min(score, 1.0), evidence, suggestions
    
    def _assess_efficiency(self, processing_time: float, analysis_results: Dict[str, Any]) -> Tuple[float, List[str], List[str]]:
        """评估效率性"""
        score = 0.8
        evidence = []
        suggestions = []
        
        # 检查处理速度
        if processing_time < 10.0:
            score += 0.1
            evidence.append("处理速度优秀")
        elif processing_time < 30.0:
            evidence.append("处理速度良好")
        else:
            score -= 0.1
            evidence.append("处理速度较慢")
            suggestions.append("建议优化处理算法，提升速度")
        
        evidence.append(f"处理时间: {processing_time:.2f}秒")
        
        return min(score, 1.0), evidence, suggestions
    
    def _determine_assessment_level(self, score: float) -> AssessmentLevel:
        """确定评估级别"""
        if score >= 0.9:
            return AssessmentLevel.EXCELLENT
        elif score >= 0.8:
            return AssessmentLevel.GOOD
        elif score >= 0.7:
            return AssessmentLevel.SATISFACTORY
        elif score >= 0.6:
            return AssessmentLevel.NEEDS_IMPROVEMENT
        else:
            return AssessmentLevel.POOR
    
    def _generate_assessment_summary(self, metrics: Dict[QualityDimension, QualityMetric], overall_score: float, level: AssessmentLevel) -> str:
        """生成评估摘要"""
        summary_parts = [
            f"整体质量评分: {overall_score:.3f} ({level.value})",
            f"评估时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        ]
        
        # 添加各维度摘要
        for dimension, metric in metrics.items():
            summary_parts.append(f"{dimension.value}: {metric.score:.3f}")
        
        return " | ".join(summary_parts)
    
    def _generate_recommendations(self, metrics: Dict[QualityDimension, QualityMetric], overall_score: float) -> List[str]:
        """生成改进建议"""
        recommendations = []
        
        # 基于整体分数生成建议
        if overall_score < 0.7:
            recommendations.append("整体质量需要显著提升，建议重新分析")
        
        # 基于各维度分数生成建议
        for dimension, metric in metrics.items():
            if metric.score < 0.7:
                recommendations.append(f"提升{metric.description}，当前分数: {metric.score:.3f}")
        
        # 添加通用建议
        if not recommendations:
            recommendations.append("质量表现良好，继续保持")
        
        return recommendations
    
    def get_assessment_history(self, session_id: Optional[str] = None) -> Dict[str, QualityAssessment]:
        """获取评估历史"""
        if session_id is None:
            return self.assessment_history
        
        return {
            aid: assessment for aid, assessment in self.assessment_history.items()
            if assessment.session_id == session_id
        }
    
    def get_quality_trends(self, session_id: str) -> Dict[str, Any]:
        """获取质量趋势"""
        session_assessments = self.get_assessment_history(session_id)
        
        if not session_assessments:
            return {}
        
        # 按时间排序
        sorted_assessments = sorted(
            session_assessments.values(),
            key=lambda x: x.assessment_time
        )
        
        trends = {
            "overall_scores": [a.overall_score for a in sorted_assessments],
            "assessment_times": [a.assessment_time.isoformat() for a in sorted_assessments],
            "dimension_trends": {}
        }
        
        # 计算各维度趋势
        for dimension in QualityDimension:
            dimension_scores = []
            for assessment in sorted_assessments:
                if dimension in assessment.metrics:
                    dimension_scores.append(assessment.metrics[dimension].score)
            
            if dimension_scores:
                trends["dimension_trends"][dimension.value] = dimension_scores
        
        return trends
    
    def export_assessment_report(self, assessment_id: str) -> Dict[str, Any]:
        """导出评估报告"""
        if assessment_id not in self.assessment_history:
            return {"error": "评估不存在"}
        
        assessment = self.assessment_history[assessment_id]
        
        report = {
            "assessment_id": assessment.assessment_id,
            "session_id": assessment.session_id,
            "chapter_id": assessment.chapter_id,
            "overall_score": assessment.overall_score,
            "level": assessment.level.value,
            "summary": assessment.summary,
            "recommendations": assessment.recommendations,
            "assessment_time": assessment.assessment_time.isoformat(),
            "metrics": {},
            "metadata": assessment.metadata
        }
        
        # 添加各维度指标
        for dimension, metric in assessment.metrics.items():
            report["metrics"][dimension.value] = {
                "score": metric.score,
                "weight": metric.weight,
                "description": metric.description,
                "evidence": metric.evidence,
                "suggestions": metric.suggestions
            }
        
        return report

# 创建全局质量评估系统实例
quality_assessment_system = QualityAssessmentSystem()
