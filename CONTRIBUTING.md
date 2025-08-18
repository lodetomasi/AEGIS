# Contributing to AETHER

We welcome contributions to the AETHER framework! This document provides guidelines for contributors.

## Development Setup

### Prerequisites
- Python 3.8+ 
- OpenRouter API key for model access
- Git for version control

### Installation
```bash
git clone https://github.com/lodetomasi/AEGIS.git
cd AEGIS
pip install -r requirements.txt
export OPENROUTER_API_KEY="your_key_here"
```

### Testing
```bash
# Run unit tests
python -m pytest tests/

# Run integration tests (requires API key)
python test_integration.py

# Run quick validation
python quick_test.py
```

## Code Quality Standards

### Python Style
- Follow PEP 8 style guidelines
- Use `black` for code formatting: `black src/ prism/ delta/ sentinel/ aegis/`
- Use `flake8` for linting: `flake8 . --max-line-length=127`
- Use type hints where appropriate

### Documentation
- All mathematical formulations must be properly documented
- Empirical claims must be supported by statistical tests
- Use GitHub-compatible mathematical notation (avoid LaTeX)
- Provide clear docstrings for all functions and classes

### Testing Requirements
- Unit tests for all new functionality
- Integration tests for API-dependent features
- Performance benchmarks for core algorithms
- Statistical validation for evaluation metrics

## Research Integrity

### Data Requirements
**CRITICAL**: Never invent, fabricate, or make up empirical results. All claims must be:
- Based on actual framework execution
- Supported by real data from legitimate sources  
- Verifiable through the codebase and test results
- Conservative and accurate representations

### Citation Requirements
- Provide citations for all external data sources
- Reference peer-reviewed studies for human baselines
- Include regulatory data sources for risk models
- Credit original research for methodology inspiration

## Contribution Types

### Bug Fixes
- Fix issues at the source, not through workarounds
- Include regression tests
- Update documentation if behavior changes

### New Features
- Discuss major changes in GitHub Issues first
- Maintain backward compatibility where possible
- Include comprehensive tests and documentation
- Follow existing architectural patterns

### Research Enhancements
- Multi-turn conversation evaluation
- Semantic relevance scoring using embeddings
- Automated architecture vulnerability discovery
- Cross-lingual evaluation framework extension

### Documentation Improvements
- README enhancements
- API documentation
- Tutorial content
- Academic paper preparation

## Submission Guidelines

### Pull Request Process
1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Make your changes with proper tests
4. Ensure all CI checks pass
5. Submit pull request with clear description

### Commit Message Format
```
type(scope): brief description

Detailed explanation of changes.
Include motivation and context.
Reference any related issues.
```

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

### Review Criteria
- Technical correctness
- Test coverage
- Documentation quality
- Performance impact
- Research integrity
- Code style compliance

## Academic Collaboration

### ICSE 2026 Submission
This framework is being prepared for ICSE 2026 Industry Challenge Track. Contributors may be acknowledged in the submission if their contributions are substantial.

### Publication Ethics
- All contributions must follow academic integrity standards
- No plagiarism or unauthorized use of external code
- Proper attribution for all sources and inspirations
- Transparent reporting of methodology and results

## Recognition

### Contributor Types
- **Core Contributors**: Substantial code or research contributions
- **Documentation Contributors**: Significant documentation improvements  
- **Bug Reporters**: Identify and help resolve issues
- **Academic Collaborators**: Research insights and validation

### Acknowledgments
Significant contributors will be acknowledged in:
- Repository README
- Academic publications (where appropriate)
- Conference presentations
- Project documentation

## Getting Help

### Communication Channels
- GitHub Issues for bug reports and feature requests
- GitHub Discussions for questions and ideas
- Email maintainers for sensitive topics

### Documentation
- README.md for framework overview
- CLAUDE.md for development guidance
- API documentation in code docstrings
- Academic paper draft (coming soon)

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

**Questions?** Open an issue or contact the maintainers. We appreciate your interest in improving AETHER!