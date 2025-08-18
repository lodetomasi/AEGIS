# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Conference Target: ICSE 2026 Industry Challenge Track

This framework is being prepared for submission to the **ICSE 2026 Industry Challenge Track** as a Solution Paper addressing the challenge "Evaluating Agentic AI Systems: From Performance to Risk".

### Important Dates
- **Challenge Dissemination**: July 31st, 2025
- **Solution Paper Submission**: November 7th, 2025
- **Notification**: December 20th, 2025
- **Conference Presentation**: April 15-17, 2026

### Paper Requirements
- Must demonstrate technical soundness, relevance to the challenge, and potential for impact
- Double-anonymous submission policy
- Eligible for Distinguished Solution Paper award ($1,000-$5,000 prize)

## Challenge Objectives

This framework addresses the research challenge "Evaluating Agentic AI Systems: From Performance to Risk" which identifies FOUR key hurdles in agentic AI evaluation:

### 1. Dynamic vs Static Evaluation
**Problem**: Static benchmarks fail to reflect continuously evolving agentic AI behavior and enable eval-aware gaming.
**Solution**: AEGIS module generates unique evaluation tasks on every run using cryptographic uniqueness guarantees.

### 2. Technical-to-Risk Translation
**Problem**: Technical evaluation results don't communicate business impact to governance bodies.
**Solution**: PRISM module translates technical metrics into financial risk using real regulatory data.

### 3. Baseline Comparison Without Ground Truth
**Problem**: Absence of meaningful baselines for AI performance comparison.
**Solution**: DELTA module compares against empirical human expert baselines without requiring absolute ground truth.

### 4. Static Architecture Analysis
**Problem**: Agentic AI systems rarely evaluated before execution despite architectural impact on performance.
**Solution**: SENTINEL module analyzes system architecture pre-deployment to identify design-time risks.

## Development Commands

### Installation and Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Set required API key for model access
export OPENROUTER_API_KEY=your_key_here
```

### Main Evaluation Commands
```bash
# Run comprehensive evaluation (production test)
python challenge_test.py

# Run quick verification test
python quick_test.py

# Run integration tests
python test_integration.py
```

### Key Environment Variables
- `OPENROUTER_API_KEY` - Required for API access to production models

## Architecture Overview

AETHER is a comprehensive AI evaluation framework consisting of four core modules:

### Core Modules
- **AEGIS** (`src/aegis.py`): Dynamic adversarial task generation with cryptographic uniqueness
- **PRISM** (`prism/`): Risk translation from technical metrics to business impact
- **DELTA** (`delta/`): Baseline comparison against human performance data  
- **SENTINEL** (`sentinel/`): Static architecture analysis for pre-deployment risk

### Key Components
- **Advanced Scorer v2** (`src/advanced_scorer_v2.py`): Implements 2024 scoring methodology with ASR metrics
- **OpenRouter Client** (`src/openrouter_client.py`): API interface for production model testing
- **Storage System** (`src/storage.py`): Atomic file operations for caching and persistence

### Data Structure
```
data/
├── cache/completions/     # API response caching
├── cache/usage/          # Usage tracking
├── tasks/               # Generated evaluation tasks by category
│   ├── safety/
│   ├── harmful/
│   ├── bias/
│   └── accuracy/
└── config/              # Risk mappings and templates
```

## Task Categories and Evaluation

### Supported Categories
- **safety**: Safety assessment and risk evaluation
- **harmful**: Harmful content detection and prevention
- **bias**: Bias detection and fairness evaluation
- **accuracy**: Factual accuracy and hallucination detection
- **reasoning**: Logical reasoning and problem-solving

### Evaluation Methodology
The framework uses a multi-dimensional scoring system:
1. **Adversarial Resistance (35%)**: Attack Success Rate (ASR) based
2. **Contextual Appropriateness (35%)**: Relevance and hallucination detection
3. **Business Risk Assessment (30%)**: Financial impact quantification

## Production Models Tested
- `mistralai/mixtral-8x22b-instruct`
- `anthropic/claude-opus-4`
- `meta-llama/llama-3.3-70b-instruct`
- `deepseek/deepseek-r1-0528`
- `google/gemini-2.5-pro`

## Key Design Patterns

### Real Data Requirements
**IMPORTANT**: This framework uses only real, production data. No fake data, mockups, simulated results, or placeholder values are acceptable. All evaluations must use:
- Real production models via OpenRouter API
- Actual regulatory cost data (HIPAA, SEC fines, etc.)
- Empirical human performance baselines from peer-reviewed studies
- Genuine API responses and evaluation metrics

### Unique Task Generation
Each task uses cryptographic uniqueness: `hashlib.md5(category + timestamp + random)` to prevent benchmark gaming.

### Risk Quantification
Industry-specific risk models based on real regulatory data:
- Healthcare: HIPAA violations ($1,913/record), malpractice costs
- Finance: SEC fines (up to $25M), trading losses
- Legal: Malpractice liability, ethics violations

### Empirical Baselines
Human performance data from peer-reviewed sources:
- Medical diagnosis: Mayo Clinic studies (88% accuracy)
- Financial analysis: CFA Institute data (79% accuracy)
- Safety assessment: Industry benchmarks (92% accuracy)

## File Organization Patterns
- Module initialization in `__init__.py` files
- Configuration in `config/` with JSON/YAML formats
- Results stored in timestamped files under `results/`
- Caching system prevents redundant API calls

## Rate Limiting and API Usage
The system implements 10-second delays between API calls to respect rate limits. All API responses are cached to prevent redundant requests.

## Development Principles
**IMPORTANT**: When encountering bugs or errors in the codebase, ALWAYS fix them properly at the source. Never work around problems with temporary solutions or bypasses. All fixes should be permanent and address the root cause of the issue.