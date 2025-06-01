# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AI Fleet is a Python CLI tool for managing multiple AI coding agents in parallel. Each agent runs in its own git worktree with an isolated tmux session. The project uses Python 3.12+ and is configured with pyproject.toml.

## Development Commands

### Running Tests
```bash
# Run all tests
python -m pytest

# Run with coverage
python -m pytest --cov=aifleet

# Run specific test file
python -m pytest tests/test_state.py -v
```

### Linting and Formatting
```bash
# Run all checks
make lint

# Format code
ruff format .

# Type checking
mypy src/aifleet --ignore-missing-imports
```

### Installing for Development
```bash
# Install in development mode
pipx install -e .

# Reinstall after changes
pipx reinstall ai-fleet
```

## Project Structure

```
src/aifleet/
├── __init__.py
├── cli.py           # Main CLI entry point
├── commands/        # CLI command implementations
│   ├── attach.py    # Attach to tmux session
│   ├── create.py    # Create single agent
│   ├── fanout.py    # Create multiple agents with same prompt
│   ├── init.py      # Initialize project config
│   ├── kill.py      # Kill agents
│   ├── list.py      # List active agents
│   ├── logs.py      # View agent logs
│   ├── multi.py     # Create multiple agents with different prompts
│   ├── prompt.py    # Send prompts to running agents
│   └── update.py    # Update AI Fleet
├── config.py        # Configuration management
├── state.py         # Agent state persistence
├── tmux.py          # Tmux session management
├── worktree.py      # Git worktree management
└── utils.py         # Utility functions
```

## Architecture Notes

- **State Management**: Uses JSON files to track agent state (either project-local `.aifleet/state.json` or global `~/.ai_fleet/state.json`)
- **Tmux Integration**: All agents run in tmux sessions with prefix (default "ai_")
- **Git Worktrees**: Each agent gets its own worktree to work independently
- **Configuration**: Hierarchical config system (user config → project config)

## Key Patterns

1. **Command Structure**: All commands inherit from Click commands and use `ensure_project_config()` to load configuration
2. **Manager Classes**: TmuxManager, WorktreeManager, StateManager handle core functionality
3. **Agent Lifecycle**: Create worktree → Setup environment → Create tmux session → Start agent → Track in state
4. **Session Naming**: Tmux methods expect branch names and add prefix internally (don't pass full session names)

## Common Development Tasks

### Adding a New Command
1. Create new file in `src/aifleet/commands/`
2. Implement Click command
3. Register in `src/aifleet/cli.py`
4. Add tests in `tests/test_commands_*.py`

### Debugging Sessions
```bash
# Check tmux sessions directly
tmux list-sessions

# Check agent state
cat .aifleet/state.json

# Check worktrees
git worktree list
```

## Important Implementation Details

- The `Agent` dataclass has optional fields at the end (pid, prompt)
- Tmux methods take branch names, not full session names
- State reconciliation happens on `fleet list` to clean up dead sessions
- The claude CLI doesn't have a `--yes` flag

## UV Package Manager

- Use uv for package management
- Add dependencies with `uv add package-name`
- Run tools with `uv run` without activating virtual environments