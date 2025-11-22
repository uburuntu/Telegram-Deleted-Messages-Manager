.PHONY: help install install-dev run test test-coverage clean build lint format test-workflows test-ci test-build-workflow

help:
	@echo "Available commands:"
	@echo "  make install       - Install production dependencies"
	@echo "  make install-dev   - Install development dependencies"
	@echo "  make run          - Run the application"
	@echo "  make test         - Run tests"
	@echo "  make test-coverage - Run tests with coverage report"
	@echo "  make clean        - Clean build artifacts"
	@echo "  make build            - Build standalone executable"
	@echo "  make lint             - Run linters"
	@echo "  make format           - Format code"
	@echo "  make test-workflows   - List all GitHub Actions workflows (requires act)"
	@echo "  make test-ci          - Test CI workflow locally (requires act)"
	@echo "  make test-build-workflow - Test build workflow locally (requires act)"

install:
	uv sync

install-dev:
	uv sync
	uv pip install -e ".[dev]"

run:
	uv run python main.py

test:
	uv run pytest

test-coverage:
	uv run pytest --cov=src --cov-report=html --cov-report=term

clean:
	rm -rf build/ dist/ *.spec
	rm -rf src/__pycache__ tests/__pycache__
	rm -rf .pytest_cache .coverage htmlcov/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete

build:
	uv pip install -e ".[build]"
	uv run python build.py

lint:
	uv run ruff check src/ tests/

format:
	uv run ruff format src/ tests/

# GitHub Actions local testing
test-workflows:
	@echo "Testing GitHub Actions workflows locally with act..."
	@command -v act >/dev/null 2>&1 || { echo "Error: act is not installed. Install with: brew install act"; exit 1; }
	act -l

test-ci:
	@echo "Running CI workflow locally..."
	act push -j lint-and-format -j test

test-build-workflow:
	@echo "Testing build workflow locally..."
	act -j build-test
