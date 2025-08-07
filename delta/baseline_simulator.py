"""Baseline performance simulation for comparison."""

import random
import time
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
import numpy as np
from scipy import stats


class BaselineType(Enum):
    """Types of baseline systems."""
    
    HUMAN_EXPERT = "human_expert"
    HUMAN_AVERAGE = "human_average"
    RULE_BASED = "rule_based"
    PREVIOUS_VERSION = "previous_version"
    RANDOM = "random"
    NO_SYSTEM = "no_system"


@dataclass
class BaselineConfig:
    """Configuration for baseline simulation."""
    
    baseline_type: BaselineType
    performance_params: Dict[str, Any]
    variability_params: Dict[str, Any] = field(default_factory=dict)
    constraints: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class BaselineResult:
    """Result from baseline simulation."""
    
    task_id: str
    baseline_type: BaselineType
    success: bool
    score: float
    execution_time: float
    confidence: float
    errors: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class BaselineSimulator:
    """Simulates baseline performance for comparison."""
    
    def __init__(self):
        """Initialize baseline simulator."""
        self.configs: Dict[BaselineType, BaselineConfig] = {}
        self._initialize_default_configs()
    
    def _initialize_default_configs(self):
        """Initialize default baseline configurations."""
        # Human expert configuration
        self.configs[BaselineType.HUMAN_EXPERT] = BaselineConfig(
            baseline_type=BaselineType.HUMAN_EXPERT,
            performance_params={
                'mean_accuracy': 0.85,
                'std_accuracy': 0.10,
                'mean_time': 300,  # 5 minutes average
                'std_time': 120,   # 2 minutes std
                'fatigue_factor': 0.02,  # 2% degradation per hour
                'error_types': {
                    'oversight': 0.4,
                    'knowledge_gap': 0.3,
                    'calculation_error': 0.2,
                    'misinterpretation': 0.1
                }
            },
            variability_params={
                'time_of_day_effect': True,
                'complexity_scaling': True,
                'experience_factor': 1.0
            },
            constraints={
                'max_continuous_hours': 8,
                'break_duration': 900,  # 15 minutes
                'daily_capacity': 50  # tasks per day
            }
        )
        
        # Average human configuration
        self.configs[BaselineType.HUMAN_AVERAGE] = BaselineConfig(
            baseline_type=BaselineType.HUMAN_AVERAGE,
            performance_params={
                'mean_accuracy': 0.65,
                'std_accuracy': 0.15,
                'mean_time': 600,  # 10 minutes average
                'std_time': 300,   # 5 minutes std
                'fatigue_factor': 0.05,  # 5% degradation per hour
                'error_types': {
                    'oversight': 0.3,
                    'knowledge_gap': 0.4,
                    'calculation_error': 0.2,
                    'misinterpretation': 0.1
                }
            },
            variability_params={
                'time_of_day_effect': True,
                'complexity_scaling': True,
                'experience_factor': 0.7
            }
        )
        
        # Rule-based system configuration
        self.configs[BaselineType.RULE_BASED] = BaselineConfig(
            baseline_type=BaselineType.RULE_BASED,
            performance_params={
                'coverage': 0.60,  # 60% of cases covered by rules
                'accuracy_in_coverage': 0.95,
                'accuracy_out_coverage': 0.10,
                'mean_time': 5,  # 5 seconds
                'std_time': 2,
                'error_types': {
                    'rule_gap': 0.6,
                    'edge_case': 0.3,
                    'parsing_error': 0.1
                }
            },
            constraints={
                'max_rule_complexity': 100,
                'requires_structured_input': True
            }
        )
        
        # Random baseline configuration
        self.configs[BaselineType.RANDOM] = BaselineConfig(
            baseline_type=BaselineType.RANDOM,
            performance_params={
                'mean_accuracy': 0.25,  # Random among 4 choices
                'std_accuracy': 0.1,
                'mean_time': 1,
                'std_time': 0.5
            }
        )
        
        # No system baseline (manual process)
        self.configs[BaselineType.NO_SYSTEM] = BaselineConfig(
            baseline_type=BaselineType.NO_SYSTEM,
            performance_params={
                'mean_accuracy': 0.0,  # Task cannot be done
                'std_accuracy': 0.0,
                'mean_time': float('inf'),
                'std_time': 0,
                'feasibility': 0.0
            }
        )
    
    def simulate(
        self,
        task_id: str,
        baseline_type: BaselineType,
        task_complexity: float = 0.5,
        context: Optional[Dict[str, Any]] = None
    ) -> BaselineResult:
        """
        Simulate baseline performance on a task.
        
        Args:
            task_id: Task identifier
            baseline_type: Type of baseline to simulate
            task_complexity: Task complexity (0-1)
            context: Additional context for simulation
            
        Returns:
            Baseline performance result
        """
        if baseline_type not in self.configs:
            raise ValueError(f"Unknown baseline type: {baseline_type}")
        
        config = self.configs[baseline_type]
        
        # Simulate based on baseline type
        if baseline_type in [BaselineType.HUMAN_EXPERT, BaselineType.HUMAN_AVERAGE]:
            return self._simulate_human(task_id, config, task_complexity, context)
        elif baseline_type == BaselineType.RULE_BASED:
            return self._simulate_rule_based(task_id, config, task_complexity, context)
        elif baseline_type == BaselineType.RANDOM:
            return self._simulate_random(task_id, config)
        elif baseline_type == BaselineType.NO_SYSTEM:
            return self._simulate_no_system(task_id, config)
        elif baseline_type == BaselineType.PREVIOUS_VERSION:
            return self._simulate_previous_version(task_id, config, task_complexity, context)
        else:
            raise ValueError(f"Simulation not implemented for {baseline_type}")
    
    def _simulate_human(
        self,
        task_id: str,
        config: BaselineConfig,
        task_complexity: float,
        context: Optional[Dict[str, Any]]
    ) -> BaselineResult:
        """Simulate human performance."""
        params = config.performance_params
        variability = config.variability_params
        
        # Base accuracy from normal distribution
        base_accuracy = np.random.normal(
            params['mean_accuracy'],
            params['std_accuracy']
        )
        
        # Adjust for complexity
        if variability.get('complexity_scaling', True):
            complexity_penalty = (task_complexity - 0.5) * 0.2
            base_accuracy -= complexity_penalty
        
        # Apply fatigue if context provided
        if context and 'hours_worked' in context:
            fatigue_penalty = params['fatigue_factor'] * context['hours_worked']
            base_accuracy -= fatigue_penalty
        
        # Time of day effect
        if variability.get('time_of_day_effect', True) and context and 'hour_of_day' in context:
            hour = context['hour_of_day']
            if hour < 6 or hour > 22:  # Night shift penalty
                base_accuracy -= 0.1
            elif 14 <= hour <= 15:  # Post-lunch dip
                base_accuracy -= 0.05
        
        # Experience factor
        experience = variability.get('experience_factor', 1.0)
        base_accuracy *= experience
        
        # Ensure accuracy is in valid range
        accuracy = max(0.0, min(1.0, base_accuracy))
        
        # Determine success (with some randomness)
        success = random.random() < accuracy
        
        # Simulate execution time
        time_mean = params['mean_time'] * (1 + (task_complexity - 0.5))
        execution_time = max(0, np.random.normal(time_mean, params['std_time']))
        
        # Generate errors if failed
        errors = []
        if not success:
            error_probs = params.get('error_types', {})
            for error_type, prob in error_probs.items():
                if random.random() < prob:
                    errors.append(f"Human error: {error_type}")
        
        # Confidence based on accuracy and variability
        confidence = accuracy * (1 - params['std_accuracy'] / params['mean_accuracy'])
        
        return BaselineResult(
            task_id=task_id,
            baseline_type=config.baseline_type,
            success=success,
            score=accuracy,
            execution_time=execution_time,
            confidence=confidence,
            errors=errors,
            metadata={
                'complexity': task_complexity,
                'adjusted_accuracy': accuracy,
                'base_accuracy': base_accuracy
            }
        )
    
    def _simulate_rule_based(
        self,
        task_id: str,
        config: BaselineConfig,
        task_complexity: float,
        context: Optional[Dict[str, Any]]
    ) -> BaselineResult:
        """Simulate rule-based system performance."""
        params = config.performance_params
        
        # Check if task is covered by rules
        coverage_threshold = params['coverage'] * (1 - task_complexity * 0.3)
        is_covered = random.random() < coverage_threshold
        
        if is_covered:
            # Task covered by rules - high accuracy
            accuracy = params['accuracy_in_coverage']
            success = random.random() < accuracy
            confidence = 0.95  # High confidence in rule coverage
        else:
            # Task not covered - poor performance
            accuracy = params['accuracy_out_coverage']
            success = random.random() < accuracy
            confidence = 0.1  # Low confidence outside coverage
        
        # Execution time (very fast)
        execution_time = max(0, np.random.normal(
            params['mean_time'],
            params['std_time']
        ))
        
        # Generate errors
        errors = []
        if not success:
            if not is_covered:
                errors.append("Rule-based error: rule_gap - No rule covers this case")
            else:
                error_probs = params.get('error_types', {})
                for error_type, prob in error_probs.items():
                    if random.random() < prob:
                        errors.append(f"Rule-based error: {error_type}")
        
        return BaselineResult(
            task_id=task_id,
            baseline_type=config.baseline_type,
            success=success,
            score=accuracy,
            execution_time=execution_time,
            confidence=confidence,
            errors=errors,
            metadata={
                'covered_by_rules': is_covered,
                'complexity': task_complexity
            }
        )
    
    def _simulate_random(self, task_id: str, config: BaselineConfig) -> BaselineResult:
        """Simulate random baseline."""
        params = config.performance_params
        
        # Random performance
        accuracy = np.random.normal(
            params['mean_accuracy'],
            params['std_accuracy']
        )
        accuracy = max(0.0, min(1.0, accuracy))
        
        success = random.random() < accuracy
        
        execution_time = max(0, np.random.normal(
            params['mean_time'],
            params['std_time']
        ))
        
        return BaselineResult(
            task_id=task_id,
            baseline_type=config.baseline_type,
            success=success,
            score=accuracy,
            execution_time=execution_time,
            confidence=0.0,  # No confidence in random
            errors=["Random baseline: no systematic approach"] if not success else []
        )
    
    def _simulate_no_system(self, task_id: str, config: BaselineConfig) -> BaselineResult:
        """Simulate absence of any system."""
        params = config.performance_params
        
        return BaselineResult(
            task_id=task_id,
            baseline_type=config.baseline_type,
            success=False,
            score=params['mean_accuracy'],
            execution_time=params['mean_time'],
            confidence=0.0,
            errors=["No system: task cannot be completed without automation"],
            metadata={'feasibility': params.get('feasibility', 0.0)}
        )
    
    def _simulate_previous_version(
        self,
        task_id: str,
        config: BaselineConfig,
        task_complexity: float,
        context: Optional[Dict[str, Any]]
    ) -> BaselineResult:
        """Simulate previous AI version performance."""
        # Use provided config or default
        if not config.performance_params:
            # Default previous version parameters
            config.performance_params = {
                'mean_accuracy': 0.70,
                'std_accuracy': 0.12,
                'mean_time': 30,
                'std_time': 10,
                'complexity_penalty': 0.15
            }
        
        params = config.performance_params
        
        # Base accuracy
        base_accuracy = np.random.normal(
            params['mean_accuracy'],
            params['std_accuracy']
        )
        
        # Complexity adjustment
        complexity_penalty = params.get('complexity_penalty', 0.15) * (task_complexity - 0.5)
        accuracy = max(0.0, min(1.0, base_accuracy - complexity_penalty))
        
        success = random.random() < accuracy
        
        # Execution time
        execution_time = max(0, np.random.normal(
            params['mean_time'],
            params['std_time']
        ))
        
        errors = []
        if not success:
            errors.append("Previous version error: capability limitation")
        
        return BaselineResult(
            task_id=task_id,
            baseline_type=config.baseline_type,
            success=success,
            score=accuracy,
            execution_time=execution_time,
            confidence=accuracy,
            errors=errors,
            metadata={
                'version': config.metadata.get('version', 'unknown'),
                'complexity': task_complexity
            }
        )
    
    def set_custom_baseline(
        self,
        baseline_type: BaselineType,
        config: BaselineConfig
    ):
        """Set custom baseline configuration."""
        self.configs[baseline_type] = config
    
    def simulate_batch(
        self,
        task_ids: List[str],
        baseline_type: BaselineType,
        task_complexities: Optional[List[float]] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> List[BaselineResult]:
        """Simulate baseline for multiple tasks."""
        if task_complexities is None:
            task_complexities = [0.5] * len(task_ids)
        
        results = []
        for i, task_id in enumerate(task_ids):
            # Update context for fatigue simulation
            if context and baseline_type in [BaselineType.HUMAN_EXPERT, BaselineType.HUMAN_AVERAGE]:
                hours_worked = i * self.configs[baseline_type].performance_params['mean_time'] / 3600
                context['hours_worked'] = hours_worked
            
            result = self.simulate(
                task_id,
                baseline_type,
                task_complexities[i],
                context
            )
            results.append(result)
        
        return results