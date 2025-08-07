"""Metrics collection utilities for AETHER system."""

import time
import statistics
from typing import Dict, List, Any, Optional, Callable
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime
import json


@dataclass
class MetricPoint:
    """Single metric measurement."""
    name: str
    value: float
    timestamp: datetime = field(default_factory=datetime.utcnow)
    tags: Dict[str, str] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'value': self.value,
            'timestamp': self.timestamp.isoformat(),
            'tags': self.tags
        }


class MetricsCollector:
    """Collects and aggregates metrics."""
    
    def __init__(self):
        self._metrics: Dict[str, List[MetricPoint]] = {}
        self._timers: Dict[str, float] = {}
    
    def record(self, name: str, value: float, tags: Optional[Dict[str, str]] = None):
        """Record a single metric value."""
        if name not in self._metrics:
            self._metrics[name] = []
        
        point = MetricPoint(name=name, value=value, tags=tags or {})
        self._metrics[name].append(point)
    
    def start_timer(self, name: str):
        """Start a timer for performance measurement."""
        self._timers[name] = time.time()
    
    def stop_timer(self, name: str, tags: Optional[Dict[str, str]] = None) -> float:
        """Stop timer and record elapsed time."""
        if name not in self._timers:
            raise ValueError(f"Timer '{name}' not started")
        
        elapsed = time.time() - self._timers[name]
        del self._timers[name]
        
        self.record(f"{name}_duration", elapsed, tags)
        return elapsed
    
    @contextmanager
    def timer(self, name: str, tags: Optional[Dict[str, str]] = None):
        """Context manager for timing operations."""
        start = time.time()
        try:
            yield
        finally:
            elapsed = time.time() - start
            self.record(f"{name}_duration", elapsed, tags)
    
    def get_metrics(self, name: str) -> List[MetricPoint]:
        """Get all metrics for a given name."""
        return self._metrics.get(name, [])
    
    def get_stats(self, name: str) -> Dict[str, float]:
        """Get statistical summary for a metric."""
        points = self.get_metrics(name)
        if not points:
            return {}
        
        values = [p.value for p in points]
        
        return {
            'count': len(values),
            'mean': statistics.mean(values),
            'median': statistics.median(values),
            'std': statistics.stdev(values) if len(values) > 1 else 0,
            'min': min(values),
            'max': max(values),
            'p95': self._percentile(values, 0.95),
            'p99': self._percentile(values, 0.99)
        }
    
    def _percentile(self, values: List[float], p: float) -> float:
        """Calculate percentile."""
        sorted_values = sorted(values)
        k = (len(sorted_values) - 1) * p
        lower = int(k)
        upper = lower + 1
        
        if upper >= len(sorted_values):
            return sorted_values[lower]
        
        return sorted_values[lower] * (upper - k) + sorted_values[upper] * (k - lower)
    
    def export_json(self) -> str:
        """Export all metrics as JSON."""
        export_data = {}
        
        for name, points in self._metrics.items():
            export_data[name] = {
                'points': [p.to_dict() for p in points],
                'stats': self.get_stats(name)
            }
        
        return json.dumps(export_data, indent=2)
    
    def reset(self):
        """Reset all metrics."""
        self._metrics.clear()
        self._timers.clear()


# Global metrics instance
_global_metrics = MetricsCollector()


def record_metric(name: str, value: float, tags: Optional[Dict[str, str]] = None):
    """Record metric to global collector."""
    _global_metrics.record(name, value, tags)


@contextmanager
def timer_context(name: str, tags: Optional[Dict[str, str]] = None):
    """Timer context manager using global collector."""
    with _global_metrics.timer(name, tags):
        yield


def get_global_metrics() -> MetricsCollector:
    """Get global metrics collector instance."""
    return _global_metrics


def metric_decorator(name: Optional[str] = None):
    """Decorator to automatically time function execution."""
    def decorator(func: Callable) -> Callable:
        def wrapper(*args, **kwargs):
            metric_name = name or f"{func.__module__}.{func.__name__}"
            with timer_context(metric_name):
                return func(*args, **kwargs)
        return wrapper
    return decorator