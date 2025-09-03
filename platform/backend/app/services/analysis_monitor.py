"""
分析监控服务
用于跟踪AI分析的质量和性能指标
"""

import time
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from dataclasses import dataclass
from app.config.analysis_config import analysis_config

logger = logging.getLogger(__name__)

@dataclass
class AnalysisMetrics:
    """分析指标数据类"""
    session_id: int
    chapter_id: int
    start_time: datetime
    end_time: Optional[datetime] = None
    processing_time: Optional[float] = None
    accuracy_score: Optional[float] = None
    confidence_scores: Dict[str, float] = None
    consistency_score: Optional[float] = None
    error_count: int = 0
    retry_count: int = 0
    
    def __post_init__(self):
        if self.confidence_scores is None:
            self.confidence_scores = {}
    
    def calculate_overall_score(self) -> float:
        """计算综合评分"""
        if not self.confidence_scores:
            return 0.0
        
        # 使用加权平均计算综合评分
        weights = analysis_config.MONITORING_METRICS
        total_score = 0.0
        total_weight = 0.0
        
        for metric_name, score in self.confidence_scores.items():
            if metric_name in weights:
                weight = weights[metric_name].get("weight", 0.1)
                total_score += score * weight
                total_weight += weight
        
        if total_weight > 0:
            return total_score / total_weight
        return 0.0

class AnalysisMonitor:
    """分析监控器"""
    
    def __init__(self):
        self.metrics_store: Dict[int, AnalysisMetrics] = {}
        self.session_metrics: Dict[int, List[AnalysisMetrics]] = {}
        self.performance_history: List[Dict[str, Any]] = []
    
    def start_analysis(self, session_id: int, chapter_id: int) -> str:
        """开始分析监控"""
        metric_id = f"{session_id}_{chapter_id}"
        metrics = AnalysisMetrics(
            session_id=session_id,
            chapter_id=chapter_id,
            start_time=datetime.now()
        )
        
        self.metrics_store[metric_id] = metrics
        
        # 初始化会话指标列表
        if session_id not in self.session_metrics:
            self.session_metrics[session_id] = []
        self.session_metrics[session_id].append(metrics)
        
        logger.info(f"开始监控分析: 会话{session_id}, 章节{chapter_id}")
        return metric_id
    
    def end_analysis(self, metric_id: str, results: Dict[str, Any]) -> AnalysisMetrics:
        """结束分析监控"""
        if metric_id not in self.metrics_store:
            logger.warning(f"未找到指标ID: {metric_id}")
            return None
        
        metrics = self.metrics_store[metric_id]
        metrics.end_time = datetime.now()
        metrics.processing_time = (metrics.end_time - metrics.start_time).total_seconds()
        
        # 计算质量指标
        self._calculate_quality_metrics(metrics, results)
        
        # 记录性能历史
        self._record_performance(metrics)
        
        logger.info(f"分析完成: {metric_id}, 处理时间: {metrics.processing_time:.2f}秒")
        return metrics
    
    def _calculate_quality_metrics(self, metrics: AnalysisMetrics, results: Dict[str, Any]):
        """计算质量指标"""
        # 计算置信度分布
        if "cards" in results:
            cards = results["cards"]
            for card_type, card_list in cards.items():
                if isinstance(card_list, list) and card_list:
                    # 计算该类型卡片的平均置信度
                    scores = [card.get("confidence_score", 0.0) for card in card_list]
                    if scores:
                        avg_score = sum(scores) / len(scores)
                        metrics.confidence_scores[card_type] = avg_score
        
        # 计算一致性评分
        metrics.consistency_score = self._calculate_consistency_score(results)
        
        # 计算准确性评分（基于置信度阈值）
        metrics.accuracy_score = self._calculate_accuracy_score(metrics.confidence_scores)
    
    def _calculate_consistency_score(self, results: Dict[str, Any]) -> float:
        """计算一致性评分"""
        # 这里可以实现更复杂的一致性检查逻辑
        # 暂时返回一个基于置信度的一致性评分
        if "cards" not in results:
            return 0.0
        
        cards = results["cards"]
        total_cards = 0
        consistent_cards = 0
        
        for card_type, card_list in cards.items():
            if isinstance(card_list, list):
                total_cards += len(card_list)
                for card in card_list:
                    # 检查卡片内容的一致性
                    if self._check_card_consistency(card):
                        consistent_cards += 1
        
        if total_cards > 0:
            return consistent_cards / total_cards
        return 0.0
    
    def _check_card_consistency(self, card: Dict[str, Any]) -> bool:
        """检查单个卡片的一致性"""
        # 基础一致性检查
        required_fields = ["content", "confidence_score"]
        for field in required_fields:
            if field not in card:
                return False
        
        # 检查置信度是否合理
        confidence = card.get("confidence_score", 0.0)
        if not isinstance(confidence, (int, float)) or confidence < 0 or confidence > 1:
            return False
        
        return True
    
    def _calculate_accuracy_score(self, confidence_scores: Dict[str, float]) -> float:
        """计算准确性评分"""
        if not confidence_scores:
            return 0.0
        
        thresholds = analysis_config.get_confidence_thresholds()
        total_score = 0.0
        total_weight = 0.0
        
        for card_type, score in confidence_scores.items():
            if card_type in thresholds:
                threshold = thresholds[card_type]
                # 如果达到阈值，给予满分；否则按比例计算
                if score >= threshold:
                    accuracy = 1.0
                else:
                    accuracy = score / threshold
                
                weight = analysis_config.MONITORING_METRICS.get(card_type, {}).get("weight", 0.1)
                total_score += accuracy * weight
                total_weight += weight
        
        if total_weight > 0:
            return total_score / total_weight
        return 0.0
    
    def _record_performance(self, metrics: AnalysisMetrics):
        """记录性能数据"""
        performance_record = {
            "timestamp": datetime.now(),
            "session_id": metrics.session_id,
            "chapter_id": metrics.chapter_id,
            "processing_time": metrics.processing_time,
            "accuracy_score": metrics.accuracy_score,
            "overall_score": metrics.calculate_overall_score(),
            "confidence_scores": metrics.confidence_scores.copy() if metrics.confidence_scores else {},
            "consistency_score": metrics.consistency_score
        }
        
        self.performance_history.append(performance_record)
        
        # 保持历史记录在合理范围内
        if len(self.performance_history) > 1000:
            self.performance_history = self.performance_history[-500:]
    
    def get_session_summary(self, session_id: int) -> Dict[str, Any]:
        """获取会话分析摘要"""
        if session_id not in self.session_metrics:
            return {}
        
        metrics_list = self.session_metrics[session_id]
        if not metrics_list:
            return {}
        
        # 计算会话级别的统计信息
        total_chapters = len(metrics_list)
        completed_chapters = len([m for m in metrics_list if m.end_time])
        
        if completed_chapters == 0:
            return {
                "session_id": session_id,
                "total_chapters": total_chapters,
                "completed_chapters": completed_chapters,
                "status": "in_progress"
            }
        
        # 计算平均指标
        avg_processing_time = sum(m.processing_time or 0 for m in metrics_list) / completed_chapters
        avg_accuracy = sum(m.accuracy_score or 0 for m in metrics_list) / completed_chapters
        avg_consistency = sum(m.consistency_score or 0 for m in metrics_list) / completed_chapters
        
        # 计算置信度分布
        confidence_distribution = {}
        for metrics in metrics_list:
            for card_type, score in metrics.confidence_scores.items():
                if card_type not in confidence_distribution:
                    confidence_distribution[card_type] = []
                confidence_distribution[card_type].append(score)
        
        # 计算各类型的平均置信度
        avg_confidence_scores = {}
        for card_type, scores in confidence_distribution.items():
            if scores:
                avg_confidence_scores[card_type] = sum(scores) / len(scores)
        
        return {
            "session_id": session_id,
            "total_chapters": total_chapters,
            "completed_chapters": completed_chapters,
            "status": "completed" if completed_chapters == total_chapters else "in_progress",
            "avg_processing_time": avg_processing_time,
            "avg_accuracy_score": avg_accuracy,
            "avg_consistency_score": avg_consistency,
            "avg_confidence_scores": avg_confidence_scores,
            "overall_quality_score": (avg_accuracy + avg_consistency) / 2
        }
    
    def get_performance_report(self) -> Dict[str, Any]:
        """获取性能报告"""
        if not self.performance_history:
            return {"message": "暂无性能数据"}
        
        # 计算总体统计
        total_analyses = len(self.performance_history)
        avg_processing_time = sum(r["processing_time"] or 0 for r in self.performance_history) / total_analyses
        avg_accuracy = sum(r["accuracy_score"] or 0 for r in self.performance_history) / total_analyses
        avg_overall_score = sum(r["overall_score"] or 0 for r in self.performance_history) / total_analyses
        
        # 计算趋势（最近10次 vs 之前10次）
        recent_analyses = self.performance_history[-10:] if len(self.performance_history) >= 10 else self.performance_history
        previous_analyses = self.performance_history[-20:-10] if len(self.performance_history) >= 20 else []
        
        recent_avg = sum(r["overall_score"] or 0 for r in recent_analyses) / len(recent_analyses) if recent_analyses else 0
        previous_avg = sum(r["overall_score"] or 0 for r in previous_analyses) / len(previous_analyses) if previous_analyses else 0
        
        trend = "improving" if recent_avg > previous_avg else "declining" if recent_avg < previous_avg else "stable"
        
        return {
            "total_analyses": total_analyses,
            "avg_processing_time": avg_processing_time,
            "avg_accuracy_score": avg_accuracy,
            "avg_overall_score": avg_overall_score,
            "trend": trend,
            "recent_performance": recent_avg,
            "previous_performance": previous_avg,
            "improvement": recent_avg - previous_avg if previous_analyses else 0
        }

# 创建全局监控器实例
analysis_monitor = AnalysisMonitor()
