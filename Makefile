.PHONY: help install install-dev run test test-coverage clean build lint format

help:
	@echo "Available commands:"
	@echo "  make install       - Install production dependencies"
	@echo "  make install-dev   - Install development dependencies"
	@echo "  make run          - Run the application"
	@echo "  make test         - Run tests"
	@echo "  make test-coverage - Run tests with coverage report"
	@echo "  make clean        - Clean build artifacts"
	@echo "  make build        - Build standalone executable"
	@echo "  make lint         - Run linters (if configured)"
	@echo "  make format       - Format code (if configured)"

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
