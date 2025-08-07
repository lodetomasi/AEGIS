"""Comparative analysis between agent and baseline performance."""

import statistics
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from scipy import stats as scipy_stats
import numpy as np
from statsmodels.stats.power import ttest_power
from statsmodels.stats.multitest import multipletests
import warnings
warnings.filterwarnings('ignore', category=RuntimeWarning)

from .baseline_simulator import BaselineResult, BaselineType


@dataclass
class ComparisonMetric:
    """Single comparison metric with advanced statistics."""
    
    name: str
    agent_value: float
    baseline_value: float
    difference: float
    relative_change: float  # Percentage change
    is_significant: bool
    p_value: Optional[float] = None
    confidence_interval: Optional[Tuple[float, float]] = None
    favors: str = ""  # "agent", "baseline", or "neutral"
    
    # Additional statistics (optional)
    effect_size: Optional[float] = None
    statistical_power: Optional[float] = None
    test_used: Optional[str] = None
    agent_std: Optional[float] = None
    baseline_std: Optional[float] = None
    bayesian_prob: Optional[float] = None
    bayes_factor: Optional[float] = None


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
        result = {
            'agent': metric.agent_value,
            'baseline': metric.baseline_value,
            'difference': metric.difference,
            'relative_change': metric.relative_change,
            'is_significant': metric.is_significant,
            'p_value': metric.p_value,
            'confidence_interval': metric.confidence_interval,
            'favors': metric.favors
        }
        
        # Add optional statistics if present
        if metric.effect_size is not None:
            result['effect_size'] = metric.effect_size
        if metric.statistical_power is not None:
            result['statistical_power'] = metric.statistical_power
        if metric.test_used is not None:
            result['test_used'] = metric.test_used
        if metric.agent_std is not None:
            result['agent_std'] = metric.agent_std
        if metric.baseline_std is not None:
            result['baseline_std'] = metric.baseline_std
        if metric.bayesian_prob is not None:
            result['bayesian_prob'] = metric.bayesian_prob
        if metric.bayes_factor is not None:
            result['bayes_factor'] = metric.bayes_factor
            
        return result


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
        
        # Apply multiple testing correction
        metrics_with_pvalues = [accuracy_comparison, speed_comparison, reliability_comparison]
        if cost_comparison:
            metrics_with_pvalues.append(cost_comparison)
        
        p_values = [m.p_value for m in metrics_with_pvalues if m.p_value is not None]
        if p_values:
            corrected_p_values = self.apply_multiple_testing_correction(
                [m.p_value for m in metrics_with_pvalues], method='bonferroni'
            )
            
            # Update metrics with corrected p-values
            for i, metric in enumerate(metrics_with_pvalues):
                if corrected_p_values[i] is not None:
                    metric.p_value = corrected_p_values[i]
                    metric.is_significant = corrected_p_values[i] < self.significance_level
        
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
        """Compare a single metric between agent and baseline with advanced statistics."""
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
        
        # Calculate means and standard deviations
        agent_mean = np.mean(agent_values)
        baseline_mean = np.mean(baseline_values)
        agent_std = np.std(agent_values, ddof=1) if len(agent_values) > 1 else 0
        baseline_std = np.std(baseline_values, ddof=1) if len(baseline_values) > 1 else 0
        
        # Calculate difference
        difference = agent_mean - baseline_mean
        relative_change = (difference / baseline_mean * 100) if baseline_mean != 0 else 0
        
        # Advanced statistical testing
        if len(agent_values) > 1 and len(baseline_values) > 1:
            # Check normality
            agent_normal = self._check_normality(agent_values)
            baseline_normal = self._check_normality(baseline_values)
            
            if agent_normal and baseline_normal:
                # Use parametric t-test
                t_stat, p_value = scipy_stats.ttest_ind(agent_values, baseline_values)
                test_used = "t-test"
            else:
                # Use non-parametric Mann-Whitney U test
                u_stat, p_value = scipy_stats.mannwhitneyu(agent_values, baseline_values, alternative='two-sided')
                test_used = "Mann-Whitney U"
            
            # Calculate effect size (Cohen's d)
            effect_size = self._calculate_cohens_d(agent_values, baseline_values)
            
            # Bootstrap confidence interval
            ci_lower, ci_upper = self._bootstrap_confidence_interval(
                agent_values, baseline_values, n_bootstrap=1000
            )
            confidence_interval = (ci_lower, ci_upper)
            
            # Determine significance
            is_significant = p_value < self.significance_level
            
            # Calculate statistical power
            if agent_normal and baseline_normal:
                power = self._calculate_power(agent_values, baseline_values, effect_size)
            else:
                power = None  # Power calculation not applicable for non-parametric tests
        else:
            p_value = None
            is_significant = False
            confidence_interval = None
            effect_size = None
            power = None
            test_used = "insufficient_data"
        
        # Determine who it favors
        if is_significant:
            if higher_is_better:
                favors = "agent" if difference > 0 else "baseline"
            else:
                favors = "baseline" if difference > 0 else "agent"
        else:
            favors = "neutral"
        
        # Perform Bayesian analysis for small samples
        bayesian_results = None
        if len(agent_values) < 30 or len(baseline_values) < 30:
            bayesian_results = self._bayesian_comparison(agent_values, baseline_values)
        
        return ComparisonMetric(
            name=name,
            agent_value=agent_mean,
            baseline_value=baseline_mean,
            difference=difference,
            relative_change=relative_change,
            is_significant=is_significant,
            p_value=p_value,
            confidence_interval=confidence_interval,
            favors=favors,
            effect_size=effect_size,
            statistical_power=power,
            test_used=test_used,
            agent_std=agent_std,
            baseline_std=baseline_std,
            bayesian_prob=bayesian_results['probability_better'] if bayesian_results else None,
            bayes_factor=bayesian_results['bayes_factor'] if bayesian_results else None
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
        # Simplified power calculation for overall summary
        # More detailed power calculation is done per metric
        effect_size = 0.5  # Medium effect size
        alpha = self.significance_level
        
        try:
            # Calculate power using statsmodels
            power = ttest_power(effect_size, sample_size, alpha, alternative='two-sided')
            return min(0.99, max(0.0, power))  # Ensure valid range
        except:
            # Fallback to approximation
            if sample_size < 10:
                return 0.2
            elif sample_size < 30:
                return 0.5
            elif sample_size < 100:
                return 0.8
            else:
                return 0.95
    
    def _check_normality(self, values: List[float], alpha: float = 0.05) -> bool:
        """Check if data follows normal distribution using Shapiro-Wilk test."""
        if len(values) < 3:
            return False  # Not enough data
        
        try:
            _, p_value = scipy_stats.shapiro(values)
            return p_value > alpha
        except:
            return False
    
    def _calculate_cohens_d(self, group1: List[float], group2: List[float]) -> float:
        """Calculate Cohen's d effect size."""
        n1, n2 = len(group1), len(group2)
        if n1 < 2 or n2 < 2:
            return 0.0
        
        mean1, mean2 = np.mean(group1), np.mean(group2)
        std1, std2 = np.std(group1, ddof=1), np.std(group2, ddof=1)
        
        # Pooled standard deviation
        pooled_std = np.sqrt(((n1 - 1) * std1**2 + (n2 - 1) * std2**2) / (n1 + n2 - 2))
        
        if pooled_std == 0:
            return 0.0
        
        return (mean1 - mean2) / pooled_std
    
    def _bootstrap_confidence_interval(
        self,
        group1: List[float],
        group2: List[float],
        n_bootstrap: int = 1000,
        confidence_level: float = 0.95
    ) -> Tuple[float, float]:
        """Calculate bootstrap confidence interval for difference in means."""
        differences = []
        
        for _ in range(n_bootstrap):
            # Resample with replacement
            sample1 = np.random.choice(group1, size=len(group1), replace=True)
            sample2 = np.random.choice(group2, size=len(group2), replace=True)
            
            # Calculate difference in means
            diff = np.mean(sample1) - np.mean(sample2)
            differences.append(diff)
        
        # Calculate percentiles
        alpha = 1 - confidence_level
        lower_percentile = (alpha / 2) * 100
        upper_percentile = (1 - alpha / 2) * 100
        
        ci_lower = np.percentile(differences, lower_percentile)
        ci_upper = np.percentile(differences, upper_percentile)
        
        return ci_lower, ci_upper
    
    def _calculate_power(
        self,
        group1: List[float],
        group2: List[float],
        effect_size: float
    ) -> float:
        """Calculate statistical power for t-test."""
        n = min(len(group1), len(group2))  # Conservative estimate
        
        try:
            power = ttest_power(effect_size, n, self.significance_level, alternative='two-sided')
            return min(0.99, max(0.0, power))
        except:
            return None
    
    def apply_multiple_testing_correction(
        self,
        p_values: List[float],
        method: str = 'bonferroni'
    ) -> List[float]:
        """Apply multiple testing correction to p-values."""
        if not p_values:
            return []
        
        # Filter out None values
        valid_p_values = [p for p in p_values if p is not None]
        if not valid_p_values:
            return p_values
        
        # Apply correction
        rejected, corrected_p_values, _, _ = multipletests(
            valid_p_values, alpha=self.significance_level, method=method
        )
        
        # Map back to original list
        corrected = []
        valid_idx = 0
        for p in p_values:
            if p is None:
                corrected.append(None)
            else:
                corrected.append(corrected_p_values[valid_idx])
                valid_idx += 1
        
        return corrected
    
    def _bayesian_comparison(
        self,
        group1: List[float],
        group2: List[float],
        prior_mean: float = 0.0,
        prior_std: float = 1.0
    ) -> Dict[str, float]:
        """Perform Bayesian comparison for small samples."""
        if len(group1) < 2 or len(group2) < 2:
            return {
                'probability_better': 0.5,
                'credible_interval': (0.0, 0.0),
                'bayes_factor': 1.0
            }
        
        # Calculate posterior parameters
        n1, n2 = len(group1), len(group2)
        mean1, mean2 = np.mean(group1), np.mean(group2)
        var1, var2 = np.var(group1, ddof=1), np.var(group2, ddof=1)
        
        # Pooled variance
        pooled_var = ((n1 - 1) * var1 + (n2 - 1) * var2) / (n1 + n2 - 2)
        
        # Posterior mean and variance for difference
        post_mean = mean1 - mean2
        post_var = pooled_var * (1/n1 + 1/n2)
        post_std = np.sqrt(post_var)
        
        # Probability that group1 > group2
        if post_std > 0:
            z_score = -post_mean / post_std
            prob_better = 1 - scipy_stats.norm.cdf(z_score)
        else:
            prob_better = 0.5 if post_mean == 0 else (1.0 if post_mean > 0 else 0.0)
        
        # 95% credible interval
        ci_lower = post_mean - 1.96 * post_std
        ci_upper = post_mean + 1.96 * post_std
        
        # Bayes factor (simplified)
        # BF10 = P(data|H1) / P(data|H0)
        # Using Savage-Dickey density ratio
        prior_density = scipy_stats.norm.pdf(0, prior_mean, prior_std)
        posterior_density = scipy_stats.norm.pdf(0, post_mean, post_std)
        bayes_factor = prior_density / posterior_density if posterior_density > 0 else 100.0
        
        return {
            'probability_better': prob_better,
            'credible_interval': (ci_lower, ci_upper),
            'bayes_factor': min(100.0, bayes_factor)  # Cap at 100 for display
        }