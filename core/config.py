"""Configuration classes for AETHER system."""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime


@dataclass
class AgentConfig:
    """Configuration for an AI agent to be evaluated."""
    
    model: str
    tools: List[str] = field(default_factory=list)
    permissions: Dict[str, bool] = field(default_factory=dict)
    context_window: int = 4096
    max_tokens: int = 2048
    temperature: float = 0.7
    system_prompt: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            'model': self.model,
            'tools': self.tools,
            'permissions': self.permissions,
            'context_window': self.context_window,
            'max_tokens': self.max_tokens,
            'temperature': self.temperature,
            'system_prompt': self.system_prompt,
            'metadata': self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AgentConfig':
        """Create from dictionary."""
        return cls(**data)
    
    def has_permission(self, permission: str) -> bool:
        """Check if agent has specific permission."""
        return self.permissions.get(permission, False)
    
    def has_tool(self, tool: str) -> bool:
        """Check if agent has access to specific tool."""
        return tool in self.tools


@dataclass
class EvaluationConfig:
    """Configuration for evaluation run."""
    
    # Test configuration
    num_tests: int = 100
    test_timeout: int = 300  # seconds
    parallel_tests: int = 1
    randomize_order: bool = True
    
    # Baseline configuration
    baseline_type: str = "human_expert"  # human_expert, rule_based, previous_version
    baseline_config: Dict[str, Any] = field(default_factory=dict)
    
    # Risk configuration
    risk_context: str = "general"  # general, healthcare, finance, education, etc.
    risk_weights: Dict[str, float] = field(default_factory=dict)
    risk_thresholds: Dict[str, float] = field(default_factory=dict)
    
    # Reporting configuration
    report_format: List[str] = field(default_factory=lambda: ["markdown", "json"])
    report_detail_level: str = "standard"  # minimal, standard, detailed
    include_raw_data: bool = False
    
    # Module configuration
    modules: Dict[str, bool] = field(default_factory=lambda: {
        "aegis": True,
        "prism": True,
        "delta": True,
        "sentinel": True
    })
    
    # Advanced configuration
    seed: Optional[int] = None
    cache_results: bool = True
    log_level: str = "INFO"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            'num_tests': self.num_tests,
            'test_timeout': self.test_timeout,
            'parallel_tests': self.parallel_tests,
            'randomize_order': self.randomize_order,
            'baseline_type': self.baseline_type,
            'baseline_config': self.baseline_config,
            'risk_context': self.risk_context,
            'risk_weights': self.risk_weights,
            'risk_thresholds': self.risk_thresholds,
            'report_format': self.report_format,
            'report_detail_level': self.report_detail_level,
            'include_raw_data': self.include_raw_data,
            'modules': self.modules,
            'seed': self.seed,
            'cache_results': self.cache_results,
            'log_level': self.log_level
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'EvaluationConfig':
        """Create from dictionary."""
        return cls(**data)
    
    def is_module_enabled(self, module: str) -> bool:
        """Check if specific module is enabled."""
        return self.modules.get(module, True)


@dataclass
class TestResult:
    """Result from a single test execution."""
    
    test_id: str
    test_type: str
    success: bool
    score: float
    execution_time: float
    
    # Detailed results
    agent_output: Any = None
    expected_output: Any = None
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    
    # Risk assessment
    risk_score: float = 0.0
    risk_factors: List[str] = field(default_factory=list)
    
    # Metadata
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            'test_id': self.test_id,
            'test_type': self.test_type,
            'success': self.success,
            'score': self.score,
            'execution_time': self.execution_time,
            'agent_output': self.agent_output,
            'expected_output': self.expected_output,
            'errors': self.errors,
            'warnings': self.warnings,
            'risk_score': self.risk_score,
            'risk_factors': self.risk_factors,
            'timestamp': self.timestamp.isoformat(),
            'metadata': self.metadata
        }


@dataclass
class EvaluationResult:
    """Complete evaluation results."""
    
    evaluation_id: str
    agent_config: AgentConfig
    evaluation_config: EvaluationConfig
    
    # Overall scores
    overall_score: float
    overall_risk_score: float
    recommendation: str
    
    # Module results
    aegis_results: Dict[str, Any] = field(default_factory=dict)
    prism_results: Dict[str, Any] = field(default_factory=dict)
    delta_results: Dict[str, Any] = field(default_factory=dict)
    sentinel_results: Dict[str, Any] = field(default_factory=dict)
    
    # Individual test results
    test_results: List[TestResult] = field(default_factory=list)
    
    # Timing
    start_time: datetime = field(default_factory=datetime.utcnow)
    end_time: Optional[datetime] = None
    total_duration: Optional[float] = None
    
    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            'evaluation_id': self.evaluation_id,
            'agent_config': self.agent_config.to_dict(),
            'evaluation_config': self.evaluation_config.to_dict(),
            'overall_score': self.overall_score,
            'overall_risk_score': self.overall_risk_score,
            'recommendation': self.recommendation,
            'aegis_results': self.aegis_results,
            'prism_results': self.prism_results,
            'delta_results': self.delta_results,
            'sentinel_results': self.sentinel_results,
            'test_results': [r.to_dict() for r in self.test_results],
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'total_duration': self.total_duration,
            'metadata': self.metadata
        }
    
    def add_test_result(self, result: TestResult):
        """Add a test result."""
        self.test_results.append(result)
    
    def finalize(self):
        """Finalize evaluation results."""
        self.end_time = datetime.utcnow()
        self.total_duration = (self.end_time - self.start_time).total_seconds()