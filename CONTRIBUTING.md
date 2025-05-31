# Contributing to AI Fleet

Thank you for your interest in contributing to AI Fleet! This document provides guidelines and instructions for contributing.

## Development Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/nachoal/ai-fleet.git
   cd ai-fleet
   ```

2. **Install the package in development mode**
   ```bash
   pip install -e ".[test,dev]"
   ```

3. **Install pre-commit hooks**
   ```bash
   pip install pre-commit
   pre-commit install
   ```

4. **Install Lefthook hooks** (alternative to pre-commit)
   ```bash
   pip install lefthook
   lefthook install
   ```
   
   Or with uv:
   ```bash
   uv pip install lefthook
   uv run lefthook install
   ```

## Code Style

We use [Ruff](https://github.com/astral-sh/ruff) for linting and formatting:

```bash
# Check linting
ruff check .

# Fix linting issues
ruff check --fix .

# Format code
ruff format .
```

## Running Tests

We use pytest for testing:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=aifleet --cov-report=term-missing

# Run specific test file
pytest tests/test_config.py

# Run with verbose output
pytest -v
```

## Git Hooks

We support both pre-commit and Lefthook for git hooks. Choose one:

### Pre-commit
Pre-commit hooks will automatically:
- Run Ruff linting and formatting
- Check for trailing whitespace
- Ensure files end with a newline
- Validate YAML and TOML files
- Run mypy type checking

### Lefthook (Recommended)
Lefthook is faster and runs with `uv`. It provides:

**On commit:**
- Ruff linting with auto-fix on staged files
- Ruff formatting on staged files
- YAML and TOML validation
- Trailing whitespace removal

**On push:**
- Full test suite with coverage
- Type checking with mypy
- Format and lint checks on entire codebase

## Making Changes

1. **Create a new branch**
   ```bash
   git checkout -b feat/your-feature-name
   # or
   git checkout -b fix/your-bug-fix
   ```

2. **Make your changes**
   - Write clear, concise commit messages
   - Add tests for new functionality
   - Update documentation as needed

3. **Run tests and linting**
   ```bash
   pytest
   ruff check .
   ruff format .
   ```

4. **Submit a pull request**
   - Provide a clear description of the changes
   - Reference any related issues
   - Ensure all CI checks pass

## Testing Guidelines

- Write unit tests for all new functionality
- Use pytest fixtures for common test setup
- Mock external dependencies (tmux, git, etc.)
- Aim for high test coverage (>80%)

## Documentation

- Update docstrings for any modified functions/classes
- Use Google-style docstrings
- Update README.md if adding new features
- Add examples for new commands

## Release Process

Releases are automated via GitHub Actions:

1. Update version in `src/aifleet/__init__.py`
2. Create a git tag: `git tag v0.1.0`
3. Push the tag: `git push origin v0.1.0`
4. GitHub Actions will build and publish to PyPI

## Questions?

Feel free to open an issue for any questions or concerns!