# AETHER: Agentic Evaluation Through Holistic Evidence-based Risk

<div align="center">
  <img src="https://img.shields.io/badge/Python-3.8+-blue.svg" alt="Python">
  <img src="https://img.shields.io/badge/License-MIT-green.svg" alt="License">
  <img src="https://img.shields.io/badge/Status-Production_Ready-brightgreen.svg" alt="Status">
  <img src="https://img.shields.io/badge/PRs-Welcome-brightgreen.svg" alt="PRs">
</div>

## Overview

AETHER is a comprehensive evaluation framework designed to address the fundamental challenges in assessing agentic AI systems. Unlike traditional static benchmarks, AETHER provides dynamic evaluation, risk translation, baseline comparison, and architectural analysis in a single integrated system.

## Key Features

- **🛡️ Dynamic Benchmarking (AEGIS)**: Generates fresh adversarial tasks on every run to prevent eval-aware behavior
- **🔍 Risk Translation (PRISM)**: Converts technical metrics into business risks executives can understand
- **📊 Baseline Comparison (DELTA)**: Benchmarks AI against human experts and rule-based systems
- **🏛️ Static Analysis (SENTINEL)**: Identifies architectural vulnerabilities before deployment

## Table of Contents

- [Installation](#installation)
- [Quick Start](#quick-start)
- [Architecture](#architecture)
- [Modules](#modules)
- [Usage Examples](#usage-examples)
- [Evaluation Results](#evaluation-results)
- [API Reference](#api-reference)
- [Contributing](#contributing)
- [Citation](#citation)
- [License](#license)

## Installation

### Requirements

- Python 3.8+
- No external dependencies beyond popular Python libraries
- OpenRouter API key for LLM evaluation

### Install from source

```bash
git clone https://github.com/yourusername/AETHER.git
cd AETHER
pip install -r requirements.txt
```

### Install as package

```bash
pip install -e .
```

### Configuration

1. Copy the example environment file:
```bash
cp .env.example .env
```

2. Add your OpenRouter API key:
```bash
# .env
OPENROUTER_API_KEY=your_api_key_here
```

## Quick Start

### Basic Evaluation

```python
from aether import AETHER

# Initialize AETHER
aether = AETHER()

# Run comprehensive evaluation
results = aether.evaluate(
    agent_system=my_agent,
    evaluation_config={
        'dynamic_tasks': 50,
        'risk_context': 'healthcare',
        'baseline_comparison': 'human',
        'architecture_analysis': True
    }
)

# Generate report
aether.generate_report(results, output_dir='./evaluation_results')
```

### Command Line Usage

```bash
# Run evaluation with default settings
python test_real_evaluation.py

# View results
python view_results.py

# Quick model test
python test_models_quick.py
```

## Architecture

AETHER consists of four core modules working in concert:

```
AETHER/
├── aegis/          # Dynamic benchmark generation
├── prism/          # Risk translation engine
├── delta/          # Comparative evaluation
├── sentinel/       # Static architecture analysis
├── core/           # Core evaluation framework
├── utils/          # Utilities and helpers
└── src/            # Storage and API clients
```

## Modules

### AEGIS: Adversarial Evaluation & Generation of Intelligence Standards

AEGIS creates dynamic, adversarial benchmarks that adapt to prevent gaming:

```python
from aegis import AEGIS

aegis = AEGIS()
tasks = aegis.generate_adversarial_tasks(
    count=100,
    categories=['safety', 'accuracy', 'bias', 'reasoning'],
    difficulty='adaptive'
)
```

**Features:**
- Procedural task generation with no repetition
- Domain-specific adversarial scenarios
- Multi-step reasoning challenges
- Automatic difficulty adjustment

### PRISM: Performance & Risk Intelligence System Monitor

PRISM translates technical metrics into business-relevant risk assessments:

```python
from prism import PRISM

prism = PRISM()
risk_report = prism.translate_risk({
    'jailbreak_rate': 0.15,
    'hallucination_rate': 0.08,
    'context': 'financial_services',
    'deployment_scale': 50000
})
```

**Features:**
- Industry-specific risk mappings
- Quantified business impact estimates
- Compliance risk assessment
- Executive-friendly reporting

### DELTA: Differential Evaluation & Learning Through Analysis

DELTA enables meaningful comparison between AI and baseline systems:

```python
from delta import DELTA

delta = DELTA()
comparison = delta.compare_performance(
    ai_results=ai_evaluation,
    baseline_type='human_expert',
    domain='medical_diagnosis'
)
```

**Features:**
- Human performance baselines
- Rule-based system comparison
- Marginal risk calculation
- Cost-benefit analysis

### SENTINEL: Static Evaluation Network for Threat Identification & Neutralization

SENTINEL analyzes system architecture for potential risks:

```python
from sentinel import SENTINEL

sentinel = SENTINEL()
arch_risks = sentinel.analyze_architecture({
    'components': system_components,
    'interactions': interaction_map,
    'permissions': permission_matrix
})
```

**Features:**
- Pre-deployment risk identification
- Architectural pattern analysis
- Permission boundary checking
- Vulnerability scoring

## Usage Examples

### Healthcare AI Evaluation

```python
# Evaluate a medical diagnosis AI agent
results = aether.evaluate(
    agent_system=medical_ai,
    evaluation_config={
        'dynamic_tasks': 100,
        'task_categories': ['diagnosis_accuracy', 'safety', 'privacy'],
        'risk_context': 'healthcare',
        'compliance_frameworks': ['HIPAA', 'FDA'],
        'baseline_comparison': 'board_certified_physician'
    }
)
```

### Financial Services Risk Assessment

```python
# Assess risks for a trading AI agent
risk_assessment = aether.evaluate(
    agent_system=trading_agent,
    evaluation_config={
        'dynamic_tasks': 200,
        'task_categories': ['market_manipulation', 'fairness', 'compliance'],
        'risk_context': 'financial_services',
        'regulatory_requirements': ['MiFID_II', 'Dodd_Frank'],
        'stress_test_scenarios': True
    }
)
```

### Multi-Model Comparison

```python
# Compare multiple AI models
models = ['gpt-4', 'claude-3', 'llama-3']
comparative_results = aether.batch_evaluate(
    models=models,
    evaluation_suite='comprehensive',
    output_format='executive_dashboard'
)
```

## Evaluation Results

AETHER generates comprehensive reports including:

- **Performance Metrics**: Task success rates, latency, resource usage
- **Risk Assessments**: Quantified risks with business impact estimates
- **Comparative Analysis**: AI vs baseline performance differentials
- **Architecture Recommendations**: Suggested improvements for safety

### Sample Output

```
📊 AETHER Evaluation Report
═══════════════════════════════════════════

Model: GPT-4-Agent-System
Date: 2024-11-07
Tasks: 100 (Dynamic)

Performance Summary:
✅ Overall Success Rate: 92.3%
⚡ Average Latency: 2.4s
🎯 Accuracy Score: 94.1%

Risk Assessment:
⚠️ Jailbreak Vulnerability: MEDIUM (8.2%)
   → Business Impact: $1.2M potential compliance cost
⚠️ Hallucination Rate: LOW (3.1%)
   → Business Impact: 155 incorrect decisions/month

Baseline Comparison:
📊 vs Human Expert: +5.2% accuracy, -12% decision time
📊 vs Rule-Based: +18.7% coverage, +2.1% error rate

Architecture Analysis:
🔴 High Risk: Unrestricted tool access
🟡 Medium Risk: No audit logging for decisions
🟢 Low Risk: Proper input validation
```

## API Reference

### Core Classes

#### AETHER
Main orchestrator class that coordinates all evaluation modules.

```python
class AETHER:
    def evaluate(self, agent_system, evaluation_config)
    def generate_report(self, results, output_dir)
    def batch_evaluate(self, models, evaluation_suite)
```

#### AEGIS
Dynamic benchmark generator.

```python
class AEGIS:
    def generate_adversarial_tasks(self, count, categories, difficulty)
    def create_domain_specific_tests(self, domain, complexity)
```

#### PRISM
Risk translation engine.

```python
class PRISM:
    def translate_risk(self, technical_metrics)
    def generate_executive_summary(self, risk_data)
```

#### DELTA
Comparative evaluator.

```python
class DELTA:
    def compare_performance(self, ai_results, baseline_type, domain)
    def calculate_marginal_risk(self, ai_metrics, baseline_metrics)
```

#### SENTINEL
Architecture analyzer.

```python
class SENTINEL:
    def analyze_architecture(self, system_design)
    def identify_vulnerabilities(self, component_map)
```

## Contributing

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md) for details.

### Development Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/AETHER.git
cd AETHER

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode
pip install -e .
pip install -r requirements-dev.txt

# Run tests
pytest tests/
```

### Code Style

We follow PEP 8 with a line length of 100 characters. Use `black` for formatting:

```bash
black . --line-length 100
```

## Citation

If you use AETHER in your research, please cite:

```bibtex
@software{aether2024,
  title = {AETHER: Agentic Evaluation Through Holistic Evidence-based Risk},
  author = {Your Name},
  year = {2024},
  url = {https://github.com/yourusername/AETHER}
}
```

## Related Work

- [Anthropic's Evaluation Suite](https://github.com/anthropics/evals)
- [OpenAI Evals](https://github.com/openai/evals)
- [HELM](https://crfm.stanford.edu/helm/)

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- OpenRouter for providing unified API access to multiple LLMs
- The AI safety community for invaluable feedback and suggestions
- Meta FAIR for inspiration on documentation standards

## Contact

- **Issues**: [GitHub Issues](https://github.com/yourusername/AETHER/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/AETHER/discussions)
- **Email**: aether-dev@example.com

---

<div align="center">
  <strong>Built with ❤️ for safer AI deployment</strong>
</div>