# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python project named "aim" that appears to be in its initial stages. The project uses Python 3.12+ and is configured with pyproject.toml.

## Development Commands

### Running the Application

```bash
python hello.py
```

### Project Structure

The codebase is minimal with:

- `hello.py` - Main entry point containing a simple hello world function
- `pyproject.toml` - Python project configuration file
- Currently no test suite or lint configuration detected

## Architecture Notes

This is a simple Python project with no complex architecture yet. The main entry point is `hello.py` which contains a `main()` function that prints a greeting message.

## UV Package Manager

- Use uv run to run Python tools without activating virtual environments
- For adding packages:
  - uv add package-name to add a package
  - uv add package-name --upgrade to upgrade a package
  - Be careful with uv pip install as it may downgrade packages
