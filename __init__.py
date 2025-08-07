"""
AETHER - Agentic Evaluation Through Holistic Evidence-based Risk

A comprehensive Python system for evaluating AI agents with focus on:
- Dynamic benchmark generation (AEGIS)
- Risk translation (PRISM)
- Comparative evaluation (DELTA)
- Static analysis (SENTINEL)
"""

__version__ = "0.1.0"
__author__ = "AETHER Team"

from .core.evaluator import AETHER
from .core.config import AgentConfig, EvaluationConfig

__all__ = ['AETHER', 'AgentConfig', 'EvaluationConfig']