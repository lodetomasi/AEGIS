.PHONY: help install test lint format clean run-quick run-full

help:
	@echo "Available commands:"
	@echo "  make install    - Install dependencies"
	@echo "  make test      - Run all tests"
	@echo "  make lint      - Run linting checks"
	@echo "  make format    - Format code with black"
	@echo "  make clean     - Clean cache and temporary files"
	@echo "  make run-quick - Run quick test"
	@echo "  make run-full  - Run full challenge test"

install:
	pip install -r requirements.txt
	pip install pytest pytest-cov flake8 black mypy

test:
	python test_integration.py
	python quick_test.py

lint:
	flake8 src/ prism/ delta/ sentinel/ aegis/ --max-line-length=127
	mypy src/ --ignore-missing-imports

format:
	black src/ prism/ delta/ sentinel/ aegis/

clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name ".DS_Store" -delete
	rm -rf .pytest_cache
	rm -rf htmlcov
	rm -rf .coverage
	rm -rf dist/
	rm -rf build/
	rm -rf *.egg-info

run-quick:
	@if [ -z "$$OPENROUTER_API_KEY" ]; then \
		echo "Error: OPENROUTER_API_KEY not set"; \
		exit 1; \
	fi
	python quick_test.py

run-full:
	@if [ -z "$$OPENROUTER_API_KEY" ]; then \
		echo "Error: OPENROUTER_API_KEY not set"; \
		exit 1; \
	fi
	python challenge_test.py