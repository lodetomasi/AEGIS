"""Comparative analysis between agent and baseline performance."""

import statistics
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from scipy import stats as scipy_stats
import numpy as np

from .baseline_simulator import BaselineResult, BaselineType


@dataclass
class ComparisonMetric:
    """Single comparison metric."""
    
    name: str
    agent_value: float
    baseline_value: float
    difference: float
    relative_change: float  # Percentage change
    is_significant: bool
    p_value: Optional[float] = None
    confidence_interval: Optional[Tuple[float, float]] = None
    favors: str = ""  # "agent", "baseline", or "neutral"


@dataclass
class ComparisonResult:
    """Complete comparison between agent and baseline."""
    
    # Overall comparison
    overall_winner: str  # "agent", "baseline", or "tie"
    confidence_score: float  # 0-1 confidence in winner determination
    
    # Performance metrics
    accuracy_comparison: ComparisonMetric
    speed_comparison: ComparisonMetric
    reliability_comparison: ComparisonMetric
    
    # Additional metrics
    cost_comparison: Optional[ComparisonMetric] = None
    scalability_comparison: Optional[ComparisonMetric] = None
    
    # Detailed analysis
    strengths_agent: List[str] = field(default_factory=list)
    strengths_baseline: List[str] = field(default_factory=list)
    
    # Statistical summary
    sample_size: int = 0
    statistical_power: float = 0.0
    
    # Areas of concern
    degradation_areas: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'overall_winner': self.overall_winner,
            'confidence_score': self.confidence_score,
            'metrics': {
                'accuracy': self._metric_to_dict(self.accuracy_comparison),
                'speed': self._metric_to_dict(self.speed_comparison),
                'reliability': self._metric_to_dict(self.reliability_comparison),
                'cost': self._metric_to_dict(self.cost_comparison) if self.cost_comparison else None,
                'scalability': self._metric_to_dict(self.scalability_comparison) if self.scalability_comparison else None
            },
            'strengths': {
                'agent': self.strengths_agent,
                'baseline': self.strengths_baseline
            },
            'statistics': {
                'sample_size': self.sample_size,
                'statistical_power': self.statistical_power
            },
            'concerns': {
                'degradation_areas': self.degradation_areas
            }
        }
    
    def _metric_to_dict(self, metric: ComparisonMetric) -> Dict[str, Any]:
        """Convert metric to dictionary."""
        return {
            'agent': metric.agent_value,
            'baseline': metric.baseline_value,
            'difference': metric.difference,
            'relative_change': metric.relative_change,
            'is_significant': metric.is_significant,
            'p_value': metric.p_value,
            'confidence_interval': metric.confidence_interval,
            'favors': metric.favors
        }


class ComparativeAnalyzer:
    """Analyzes comparative performance between agent and baselines."""
    
    def __init__(self, significance_level: float = 0.05):
        """
        Initialize comparative analyzer.
        
        Args:
            significance_level: Statistical significance threshold
        """
        self.significance_level = significance_level
    
    def compare(
        self,
        agent_results: List[Dict[str, Any]],
        baseline_results: List[BaselineResult],
        baseline_type: BaselineType,
        cost_model: Optional[Dict[str, float]] = None
    ) -> ComparisonResult:
        """
        Compare agent performance against baseline.
        
        Args:
            agent_results: List of agent test results
            baseline_results: List of baseline test results
            baseline_type: Type of baseline being compared
            cost_model: Optional cost model for comparison
            
        Returns:
            Comprehensive comparison result
        """
        # Ensure equal number of results
        min_len = min(len(agent_results), len(baseline_results))
        agent_results = agent_results[:min_len]
        baseline_results = baseline_results[:min_len]
        
        # Extract metrics
        agent_metrics = self._extract_agent_metrics(agent_results)
        baseline_metrics = self._extract_baseline_metrics(baseline_results)
        
        # Compare accuracy
        accuracy_comparison = self._compare_metric(
            "accuracy",
            agent_metrics['accuracy'],
            baseline_metrics['accuracy'],
            higher_is_better=True
        )
        
        # Compare speed
        speed_comparison = self._compare_metric(
            "speed",
            agent_metrics['speed'],
            baseline_metrics['speed'],
            higher_is_better=False  # Lower time is better
        )
        
        # Compare reliability
        reliability_comparison = self._compare_metric(
            "reliability",
            agent_metrics['reliability'],
            baseline_metrics['reliability'],
            higher_is_better=True
        )
        
        # Optional comparisons
        cost_comparison = None
        if cost_model:
            cost_comparison = self._calculate_cost_comparison(
                agent_metrics, baseline_metrics, cost_model, baseline_type
            )
        
        scalability_comparison = self._calculate_scalability_comparison(
            agent_metrics, baseline_metrics, baseline_type
        )
        
        # Determine overall winner
        overall_winner, confidence_score = self._determine_winner(
            accuracy_comparison,
            speed_comparison,
            reliability_comparison,
            cost_comparison
        )
        
        # Identify strengths
        strengths_agent, strengths_baseline = self._identify_strengths(
            accuracy_comparison,
            speed_comparison,
            reliability_comparison,
            baseline_type
        )
        
        # Identify degradation areas
        degradation_areas = self._identify_degradation_areas(
            accuracy_comparison,
            speed_comparison,
            reliability_comparison
        )
        
        # Calculate statistical power
        statistical_power = self._calculate_statistical_power(len(agent_results))
        
        return ComparisonResult(
            overall_winner=overall_winner,
            confidence_score=confidence_score,
            accuracy_comparison=accuracy_comparison,
            speed_comparison=speed_comparison,
            reliability_comparison=reliability_comparison,
            cost_comparison=cost_comparison,
            scalability_comparison=scalability_comparison,
            strengths_agent=strengths_agent,
            strengths_baseline=strengths_baseline,
            sample_size=len(agent_results),
            statistical_power=statistical_power,
            degradation_areas=degradation_areas
        )
    
    def _extract_agent_metrics(self, results: List[Dict[str, Any]]) -> Dict[str, List[float]]:
        """Extract metrics from agent results."""
        metrics = {
            'accuracy': [],
            'speed': [],
            'reliability': []
        }
        
        for result in results:
            # Accuracy (score or success rate)
            if 'score' in result:
                metrics['accuracy'].append(result['score'])
            elif 'success' in result:
                metrics['accuracy'].append(1.0 if result['success'] else 0.0)
            
            # Speed (execution time)
            if 'execution_time' in result:
                metrics['speed'].append(result['execution_time'])
            
            # Reliability (inverse of error count)
            error_count = len(result.get('errors', []))
            metrics['reliability'].append(1.0 / (1 + error_count))
        
        return metrics
    
    def _extract_baseline_metrics(self, results: List[BaselineResult]) -> Dict[str, List[float]]:
        """Extract metrics from baseline results."""
        metrics = {
            'accuracy': [],
            'speed': [],
            'reliability': []
        }
        
        for result in results:
            metrics['accuracy'].append(result.score)
            metrics['speed'].append(result.execution_time)
            
            # Reliability based on confidence and errors
            error_count = len(result.errors)
            reliability = result.confidence * (1.0 / (1 + error_count))
            metrics['reliability'].append(reliability)
        
        return metrics
    
    def _compare_metric(
        self,
        name: str,
        agent_values: List[float],
        baseline_values: List[float],
        higher_is_better: bool = True
    ) -> ComparisonMetric:
        """Compare a single metric between agent and baseline."""
        # Filter out invalid values
        agent_values = [v for v in agent_values if v is not None and not np.isnan(v) and not np.isinf(v)]
        baseline_values = [v for v in baseline_values if v is not None and not np.isnan(v) and not np.isinf(v)]
        
        if not agent_values or not baseline_values:
            return ComparisonMetric(
                name=name,
                agent_value=0.0,
                baseline_value=0.0,
                difference=0.0,
                relative_change=0.0,
                is_significant=False,
                favors="neutral"
            )
        
        # Calculate means
        agent_mean = statistics.mean(agent_values)
        baseline_mean = statistics.mean(baseline_values)
        
        # Calculate difference
        difference = agent_mean - baseline_mean
        relative_change = (difference / baseline_mean * 100) if baseline_mean != 0 else 0
        
        # Statistical test (t-test)
        if len(agent_values) > 1 and len(baseline_values) > 1:
            t_stat, p_value = scipy_stats.ttest_ind(agent_values, baseline_values)
            is_significant = p_value < self.significance_level
            
            # Confidence interval for difference
            pooled_std = np.sqrt(
                (np.var(agent_values) + np.var(baseline_values)) / 2
            )
            margin = 1.96 * pooled_std * np.sqrt(1/len(agent_values) + 1/len(baseline_values))
            confidence_interval = (difference - margin, difference + margin)
        else:
            p_value = None
            is_significant = False
            confidence_interval = None
        
        # Determine who it favors
        if is_significant:
            if higher_is_better:
                favors = "agent" if difference > 0 else "baseline"
            else:
                favors = "baseline" if difference > 0 else "agent"
        else:
            favors = "neutral"
        
        return ComparisonMetric(
            name=name,
            agent_value=agent_mean,
            baseline_value=baseline_mean,
            difference=difference,
            relative_change=relative_change,
            is_significant=is_significant,
            p_value=p_value,
            confidence_interval=confidence_interval,
            favors=favors
        )
    
    def _calculate_cost_comparison(
        self,
        agent_metrics: Dict[str, List[float]],
        baseline_metrics: Dict[str, List[float]],
        cost_model: Dict[str, float],
        baseline_type: BaselineType
    ) -> ComparisonMetric:
        """Calculate cost comparison."""
        # Agent costs
        agent_costs = []
        for i in range(len(agent_metrics['speed'])):
            time_cost = agent_metrics['speed'][i] * cost_model.get('agent_per_second', 0.01)
            api_cost = cost_model.get('agent_per_request', 0.1)
            agent_costs.append(time_cost + api_cost)
        
        # Baseline costs
        baseline_costs = []
        if baseline_type in [BaselineType.HUMAN_EXPERT, BaselineType.HUMAN_AVERAGE]:
            hourly_rate = cost_model.get('human_hourly_rate', 50.0)
            for time in baseline_metrics['speed']:
                baseline_costs.append(time / 3600 * hourly_rate)
        else:
            # Other baselines
            for time in baseline_metrics['speed']:
                baseline_costs.append(time * cost_model.get('baseline_per_second', 0.001))
        
        return self._compare_metric(
            "cost",
            agent_costs,
            baseline_costs,
            higher_is_better=False
        )
    
    def _calculate_scalability_comparison(
        self,
        agent_metrics: Dict[str, List[float]],
        baseline_metrics: Dict[str, List[float]],
        baseline_type: BaselineType
    ) -> ComparisonMetric:
        """Calculate scalability comparison."""
        # Scalability score based on speed consistency and parallelization potential
        
        # Agent scalability (low variance in speed, fast execution)
        agent_speed_cv = (
            statistics.stdev(agent_metrics['speed']) / statistics.mean(agent_metrics['speed'])
            if len(agent_metrics['speed']) > 1 and statistics.mean(agent_metrics['speed']) > 0
            else 0
        )
        agent_scalability = 1 / (1 + agent_speed_cv)
        
        # Baseline scalability
        if baseline_type in [BaselineType.HUMAN_EXPERT, BaselineType.HUMAN_AVERAGE]:
            # Humans have limited scalability
            baseline_scalability = 0.2
        elif baseline_type == BaselineType.RULE_BASED:
            # Rule-based systems scale well
            baseline_scalability = 0.9
        else:
            baseline_speed_cv = (
                statistics.stdev(baseline_metrics['speed']) / statistics.mean(baseline_metrics['speed'])
                if len(baseline_metrics['speed']) > 1 and statistics.mean(baseline_metrics['speed']) > 0
                else 0
            )
            baseline_scalability = 1 / (1 + baseline_speed_cv)
        
        return ComparisonMetric(
            name="scalability",
            agent_value=agent_scalability,
            baseline_value=baseline_scalability,
            difference=agent_scalability - baseline_scalability,
            relative_change=(agent_scalability - baseline_scalability) / baseline_scalability * 100
            if baseline_scalability > 0 else 0,
            is_significant=abs(agent_scalability - baseline_scalability) > 0.2,
            favors="agent" if agent_scalability > baseline_scalability else "baseline"
        )
    
    def _determine_winner(
        self,
        accuracy: ComparisonMetric,
        speed: ComparisonMetric,
        reliability: ComparisonMetric,
        cost: Optional[ComparisonMetric]
    ) -> Tuple[str, float]:
        """Determine overall winner and confidence."""
        # Count wins for each
        agent_wins = sum([
            1 for metric in [accuracy, speed, reliability, cost]
            if metric and metric.favors == "agent"
        ])
        
        baseline_wins = sum([
            1 for metric in [accuracy, speed, reliability, cost]
            if metric and metric.favors == "baseline"
        ])
        
        # Weight importance (accuracy and reliability more important)
        weighted_agent = 0
        weighted_baseline = 0
        
        weights = {
            "accuracy": 0.4,
            "reliability": 0.3,
            "speed": 0.2,
            "cost": 0.1
        }
        
        for metric, weight in [
            (accuracy, weights["accuracy"]),
            (reliability, weights["reliability"]),
            (speed, weights["speed"]),
            (cost, weights.get("cost", 0.1) if cost else None)
        ]:
            if metric and metric.favors == "agent":
                weighted_agent += weight
            elif metric and metric.favors == "baseline":
                weighted_baseline += weight
        
        # Determine winner
        if weighted_agent > weighted_baseline * 1.1:  # 10% margin
            winner = "agent"
            confidence = min(0.95, weighted_agent / (weighted_agent + weighted_baseline))
        elif weighted_baseline > weighted_agent * 1.1:
            winner = "baseline"
            confidence = min(0.95, weighted_baseline / (weighted_agent + weighted_baseline))
        else:
            winner = "tie"
            confidence = 0.5
        
        return winner, confidence
    
    def _identify_strengths(
        self,
        accuracy: ComparisonMetric,
        speed: ComparisonMetric,
        reliability: ComparisonMetric,
        baseline_type: BaselineType
    ) -> Tuple[List[str], List[str]]:
        """Identify strengths of agent and baseline."""
        agent_strengths = []
        baseline_strengths = []
        
        # Accuracy strengths
        if accuracy.favors == "agent" and accuracy.relative_change > 10:
            agent_strengths.append(
                f"{accuracy.relative_change:.1f}% more accurate than {baseline_type.value}"
            )
        elif accuracy.favors == "baseline" and accuracy.relative_change < -10:
            baseline_strengths.append(
                f"{-accuracy.relative_change:.1f}% more accurate than AI agent"
            )
        
        # Speed strengths
        if speed.favors == "agent" and speed.relative_change < -50:
            agent_strengths.append(
                f"{-speed.relative_change:.1f}% faster execution time"
            )
        elif speed.favors == "baseline":
            baseline_strengths.append(
                "Faster response time for simple tasks"
            )
        
        # Reliability strengths
        if reliability.favors == "agent":
            agent_strengths.append("More consistent and reliable performance")
        elif reliability.favors == "baseline":
            baseline_strengths.append("More predictable error patterns")
        
        # Baseline-specific strengths
        if baseline_type in [BaselineType.HUMAN_EXPERT, BaselineType.HUMAN_AVERAGE]:
            baseline_strengths.append("Better contextual understanding and judgment")
            baseline_strengths.append("Ability to handle novel situations")
        elif baseline_type == BaselineType.RULE_BASED:
            baseline_strengths.append("Deterministic and auditable decisions")
            baseline_strengths.append("No hallucination risk")
        
        # Agent-specific strengths
        agent_strengths.append("24/7 availability without fatigue")
        agent_strengths.append("Consistent performance at scale")
        
        return agent_strengths, baseline_strengths
    
    def _identify_degradation_areas(
        self,
        accuracy: ComparisonMetric,
        speed: ComparisonMetric,
        reliability: ComparisonMetric
    ) -> List[str]:
        """Identify areas where agent performs worse than baseline."""
        degradation_areas = []
        
        if accuracy.favors == "baseline" and accuracy.is_significant:
            degradation_areas.append(
                f"Accuracy degradation: {accuracy.relative_change:.1f}% worse than baseline"
            )
        
        if speed.favors == "baseline" and speed.is_significant:
            degradation_areas.append(
                f"Speed degradation: {speed.relative_change:.1f}% slower than baseline"
            )
        
        if reliability.favors == "baseline" and reliability.is_significant:
            degradation_areas.append(
                f"Reliability issues: {reliability.relative_change:.1f}% less reliable"
            )
        
        return degradation_areas
    
    def _calculate_statistical_power(self, sample_size: int) -> float:
        """Calculate statistical power of the comparison."""
        # Simplified power calculation
        # Assumes medium effect size (d=0.5)
        effect_size = 0.5
        alpha = self.significance_level
        
        # Using approximation for two-sample t-test
        if sample_size < 10:
            return 0.2
        elif sample_size < 30:
            return 0.5
        elif sample_size < 100:
            return 0.8
        else:
            return 0.95