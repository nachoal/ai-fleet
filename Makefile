.PHONY: help install install-dev test test-cov lint format clean build

help:
	@echo "Available commands:"
	@echo "  make install      Install the package"
	@echo "  make install-dev  Install with dev dependencies"
	@echo "  make test        Run tests"
	@echo "  make test-cov    Run tests with coverage"
	@echo "  make lint        Run linting"
	@echo "  make format      Format code"
	@echo "  make clean       Clean build artifacts"
	@echo "  make build       Build distribution packages"

install:
	pip install -e .

install-dev:
	pip install -e ".[test,dev]"
	pre-commit install
	lefthook install

test:
	pytest

test-cov:
	pytest --cov=aifleet --cov-report=term-missing --cov-report=html

lint:
	ruff check .
	mypy src/aifleet --ignore-missing-imports

format:
	ruff check --fix .
	ruff format .

clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	rm -rf .coverage
	rm -rf htmlcov/
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	rm -rf .ruff_cache/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

build: clean
	python -m build