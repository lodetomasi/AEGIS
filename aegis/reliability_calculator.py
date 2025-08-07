"""Reliability metrics calculation for AEGIS module."""

import statistics
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class TestRun:
    """Single test run result."""
    
    task_id: str
    run_number: int
    success: bool
    score: float
    execution_time: float
    errors: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ReliabilityMetrics:
    """Reliability metrics for a set of test runs."""
    
    task_id: str
    total_runs: int
    success_rate: float
    pass_at_k: Dict[int, float]  # k -> success rate
    score_mean: float
    score_std: float
    score_percentiles: Dict[int, float]
    time_mean: float
    time_std: float
    consistency_score: float
    degradation_rate: float
    error_distribution: Dict[str, int]
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'task_id': self.task_id,
            'total_runs': self.total_runs,
            'success_rate': self.success_rate,
            'pass_at_k': self.pass_at_k,
            'score_mean': self.score_mean,
            'score_std': self.score_std,
            'score_percentiles': self.score_percentiles,
            'time_mean': self.time_mean,
            'time_std': self.time_std,
            'consistency_score': self.consistency_score,
            'degradation_rate': self.degradation_rate,
            'error_distribution': self.error_distribution,
            'metadata': self.metadata
        }


class ReliabilityCalculator:
    """Calculates reliability metrics from test runs."""
    
    def __init__(self):
        self.test_runs: Dict[str, List[TestRun]] = {}
        self.metrics_cache: Dict[str, ReliabilityMetrics] = {}
    
    def add_run(self, run: TestRun):
        """Add a test run result."""
        if run.task_id not in self.test_runs:
            self.test_runs[run.task_id] = []
        
        self.test_runs[run.task_id].append(run)
        
        # Invalidate cache for this task
        if run.task_id in self.metrics_cache:
            del self.metrics_cache[run.task_id]
    
    def calculate_metrics(self, task_id: str, use_cache: bool = True) -> ReliabilityMetrics:
        """
        Calculate reliability metrics for a task.
        
        Args:
            task_id: Task identifier
            use_cache: Use cached metrics if available
            
        Returns:
            Reliability metrics
        """
        if use_cache and task_id in self.metrics_cache:
            return self.metrics_cache[task_id]
        
        if task_id not in self.test_runs or not self.test_runs[task_id]:
            raise ValueError(f"No test runs found for task {task_id}")
        
        runs = self.test_runs[task_id]
        
        # Basic statistics
        success_rate = sum(1 for r in runs if r.success) / len(runs)
        scores = [r.score for r in runs]
        times = [r.execution_time for r in runs]
        
        # Pass@k calculation
        pass_at_k = self._calculate_pass_at_k(runs)
        
        # Score statistics
        score_mean = statistics.mean(scores)
        score_std = statistics.stdev(scores) if len(scores) > 1 else 0.0
        score_percentiles = {
            25: self._percentile(scores, 0.25),
            50: self._percentile(scores, 0.50),
            75: self._percentile(scores, 0.75),
            90: self._percentile(scores, 0.90),
            95: self._percentile(scores, 0.95)
        }
        
        # Time statistics
        time_mean = statistics.mean(times)
        time_std = statistics.stdev(times) if len(times) > 1 else 0.0
        
        # Consistency score (inverse of coefficient of variation)
        consistency_score = 1.0 - (score_std / score_mean if score_mean > 0 else 1.0)
        
        # Degradation rate
        degradation_rate = self._calculate_degradation_rate(runs)
        
        # Error distribution
        error_distribution = self._calculate_error_distribution(runs)
        
        metrics = ReliabilityMetrics(
            task_id=task_id,
            total_runs=len(runs),
            success_rate=success_rate,
            pass_at_k=pass_at_k,
            score_mean=score_mean,
            score_std=score_std,
            score_percentiles=score_percentiles,
            time_mean=time_mean,
            time_std=time_std,
            consistency_score=consistency_score,
            degradation_rate=degradation_rate,
            error_distribution=error_distribution
        )
        
        self.metrics_cache[task_id] = metrics
        return metrics
    
    def _calculate_pass_at_k(self, runs: List[TestRun]) -> Dict[int, float]:
        """Calculate pass@k metrics."""
        pass_at_k = {}
        
        for k in [1, 3, 5, 10]:
            if len(runs) >= k:
                # Group runs into windows of size k
                successes = 0
                windows = len(runs) - k + 1
                
                for i in range(windows):
                    window = runs[i:i+k]
                    if any(r.success for r in window):
                        successes += 1
                
                pass_at_k[k] = successes / windows if windows > 0 else 0.0
        
        return pass_at_k
    
    def _calculate_degradation_rate(self, runs: List[TestRun]) -> float:
        """Calculate performance degradation over time."""
        if len(runs) < 2:
            return 0.0
        
        # Sort by timestamp
        sorted_runs = sorted(runs, key=lambda r: r.timestamp)
        
        # Calculate moving average of scores
        window_size = min(5, len(runs) // 3)
        if window_size < 2:
            return 0.0
        
        early_scores = [r.score for r in sorted_runs[:window_size]]
        late_scores = [r.score for r in sorted_runs[-window_size:]]
        
        early_avg = statistics.mean(early_scores)
        late_avg = statistics.mean(late_scores)
        
        # Degradation rate (negative means improvement)
        degradation = (early_avg - late_avg) / early_avg if early_avg > 0 else 0.0
        
        return degradation
    
    def _calculate_error_distribution(self, runs: List[TestRun]) -> Dict[str, int]:
        """Calculate distribution of error types."""
        error_counts = {}
        
        for run in runs:
            for error in run.errors:
                # Simple error categorization
                error_type = self._categorize_error(error)
                error_counts[error_type] = error_counts.get(error_type, 0) + 1
        
        return error_counts
    
    def _categorize_error(self, error: str) -> str:
        """Categorize error message."""
        error_lower = error.lower()
        
        if 'timeout' in error_lower:
            return 'timeout'
        elif 'memory' in error_lower:
            return 'memory'
        elif 'permission' in error_lower or 'access' in error_lower:
            return 'permission'
        elif 'format' in error_lower or 'parse' in error_lower:
            return 'format'
        elif 'connect' in error_lower or 'network' in error_lower:
            return 'network'
        elif 'not found' in error_lower:
            return 'not_found'
        else:
            return 'other'
    
    def _percentile(self, values: List[float], p: float) -> float:
        """Calculate percentile."""
        if not values:
            return 0.0
        
        sorted_values = sorted(values)
        k = (len(sorted_values) - 1) * p
        lower = int(k)
        upper = lower + 1
        
        if upper >= len(sorted_values):
            return sorted_values[lower]
        
        return sorted_values[lower] * (upper - k) + sorted_values[upper] * (k - lower)
    
    def get_aggregate_metrics(self, task_ids: Optional[List[str]] = None) -> Dict[str, Any]:
        """Get aggregate metrics across multiple tasks."""
        if task_ids is None:
            task_ids = list(self.test_runs.keys())
        
        if not task_ids:
            return {}
        
        all_metrics = []
        for task_id in task_ids:
            try:
                metrics = self.calculate_metrics(task_id)
                all_metrics.append(metrics)
            except ValueError:
                continue
        
        if not all_metrics:
            return {}
        
        # Aggregate statistics
        return {
            'total_tasks': len(all_metrics),
            'avg_success_rate': statistics.mean(m.success_rate for m in all_metrics),
            'avg_consistency': statistics.mean(m.consistency_score for m in all_metrics),
            'avg_degradation': statistics.mean(m.degradation_rate for m in all_metrics),
            'total_runs': sum(m.total_runs for m in all_metrics),
            'score_distribution': {
                'mean': statistics.mean(m.score_mean for m in all_metrics),
                'std': statistics.mean(m.score_std for m in all_metrics)
            },
            'time_distribution': {
                'mean': statistics.mean(m.time_mean for m in all_metrics),
                'std': statistics.mean(m.time_std for m in all_metrics)
            }
        }
    
    def identify_unreliable_tasks(self, threshold: float = 0.8) -> List[Tuple[str, float]]:
        """
        Identify tasks with low reliability.
        
        Args:
            threshold: Minimum acceptable success rate
            
        Returns:
            List of (task_id, success_rate) tuples for unreliable tasks
        """
        unreliable = []
        
        for task_id in self.test_runs:
            try:
                metrics = self.calculate_metrics(task_id)
                if metrics.success_rate < threshold:
                    unreliable.append((task_id, metrics.success_rate))
            except ValueError:
                continue
        
        return sorted(unreliable, key=lambda x: x[1])
    
    def export_metrics(self, task_id: Optional[str] = None) -> Dict[str, Any]:
        """Export metrics as dictionary."""
        if task_id:
            return self.calculate_metrics(task_id).to_dict()
        else:
            return {
                task_id: self.calculate_metrics(task_id).to_dict()
                for task_id in self.test_runs
                if task_id in self.test_runs
            }