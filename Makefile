.PHONY: help install install-dev update clean test lint format check format-check security docker-build docker-run docker-stop pre-commit-install

# Default target
help:
	@echo "Google Store Funnel Analysis - Development Commands"
	@echo ""
	@echo "Setup:"
	@echo "  make install          - Install production dependencies"
	@echo "  make install-dev      - Install development dependencies"
	@echo "  make update           - Update dependencies to latest compatible versions"
	@echo "  make pre-commit-install - Install pre-commit hooks"
	@echo ""
	@echo "Development:"
	@echo "  make run              - Run Streamlit dashboard locally"
	@echo "  make notebook         - Start Jupyter notebook server"
	@echo ""
	@echo "Code Quality:"
	@echo "  make lint             - Run linters (ruff, mypy, bandit)"
	@echo "  make format           - Format code with black and ruff"
	@echo "  make format-check     - Check code formatting without changes"
	@echo "  make check            - Run all quality checks (lint + format-check)"
	@echo "  make security         - Run security audit with bandit"
	@echo ""
	@echo "Testing:"
	@echo "  make test             - Run test suite with coverage"
	@echo "  make test-verbose     - Run tests with verbose output"
	@echo "  make test-cov         - Run tests and generate coverage report"
	@echo ""
	@echo "Docker:"
	@echo "  make docker-build     - Build Docker image"
	@echo "  make docker-run       - Run Docker container"
	@echo "  make docker-stop      - Stop Docker container"
	@echo "  make docker-compose-up - Run with docker-compose"
	@echo "  make docker-compose-down - Stop docker-compose"
	@echo ""
	@echo "Cleanup:"
	@echo "  make clean            - Remove Python cache and build artifacts"
	@echo "  make clean-all        - Remove all generated files including venv"

# Installation
install:
	python -m pip install --upgrade pip
	pip install -e .

install-dev:
	python -m pip install --upgrade pip
	pip install -e ".[dev]"

update:
	pip install --upgrade pip
	pip install --upgrade -e ".[dev]"

pre-commit-install:
	pre-commit install

# Development
run:
	streamlit run app.py

notebook:
	jupyter notebook notebooks/

# Code Quality
lint:
	@echo "Running ruff..."
	ruff check .
	@echo "Running mypy..."
	mypy dashboard/ --ignore-missing-imports || true
	@echo "Running bandit..."
	bandit -r dashboard/ -c pyproject.toml

format:
	@echo "Formatting with black..."
	black dashboard/ tests/
	@echo "Formatting with ruff..."
	ruff check . --fix

format-check:
	@echo "Checking black formatting..."
	black --check dashboard/ tests/
	@echo "Checking ruff formatting..."
	ruff check .

check: lint format-check

security:
	bandit -r dashboard/ -c pyproject.toml

# Testing
test:
	pytest

test-verbose:
	pytest -v

test-cov:
	pytest --cov=dashboard --cov-report=html --cov-report=term

# Docker
docker-build:
	docker build -t google-store-funnel-analysis .

docker-run:
	docker run -p 8501:8501 google-store-funnel-analysis

docker-stop:
	docker ps -q --filter ancestor=google-store-funnel-analysis | xargs -r docker stop

docker-compose-up:
	docker-compose up -d

docker-compose-down:
	docker-compose down

# Cleanup
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name "*.pyo" -delete 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".coverage" -exec rm -rf {} + 2>/dev/null || true
	rm -rf .coverage coverage.xml htmlcov/ 2>/dev/null || true
	rm -rf build/ dist/ *.egg-info 2>/dev/null || true

clean-all: clean
	rm -rf .venv venv env 2>/dev/null || true
	rm -rf .pre-commit-cache 2>/dev/null || true
