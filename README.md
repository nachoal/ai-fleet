# ai-fleet 🚀

*"Spin up and command a **fleet** of AI developer agents from your terminal."*

---

## Table of Contents

- [Quick Start](#quick-start)
- [Installation](#installation)
- [Core Features](#core-features)
- [Commands Reference](#commands-reference)
- [Configuration](#configuration)
- [Development Setup](#development-setup)
- [Examples](#examples)
- [Troubleshooting](#troubleshooting)
- [Product Requirements](#product-requirements-document)

---

## Quick Start

```bash
# Install from PyPI (when published)
pipx install ai-fleet

# Or install from source (see Development Setup)
uv pip install -e .

# Set up your API key
export ANTHROPIC_API_KEY=sk-...

# Navigate to your project
cd /path/to/your/project

# Initialize AI Fleet in your project
fleet init

# Create your first agent
fleet create fix-auth --prompt "Fix the authentication bug in login.py"

# List running agents
fleet list

# Check logs
fleet logs fix-auth

# Send additional instructions
fleet prompt fix-auth "Make sure to add tests"

# Attach to see live output
fleet attach fix-auth

# Clean up when done
fleet kill fix-auth
```

---

## Installation

### From PyPI (when published)

```bash
# Using pipx (recommended)
pipx install ai-fleet

# Or using pip
pip install ai-fleet
```

### From Source (Development)

See [Development Setup](#development-setup) section below.

---

## Key Concepts

### Project-Based Configuration

AI Fleet works on a per-project basis. Each git repository you want to use AI Fleet with needs to be initialized:

1. **One config per project**: Configuration lives in `.aifleet/config.toml` within your project
2. **Automatic detection**: Commands work from any subdirectory within your project
3. **Isolated state**: Each project maintains its own agent state and worktrees
4. **Team friendly**: Configuration can be committed and shared with your team

---

## Core Features

### 🎯 Single Agent Management
- Create individual agents with custom prompts
- Each agent runs in an isolated git worktree
- Full tmux session management
- Real-time CPU/memory monitoring

### 🚀 Parallel Agent Orchestration
- **Fanout**: Launch N agents with the same prompt
- **Multi**: Launch multiple agents with different tasks
- Batch management and cleanup
- Pattern-based operations (glob support)

### 🔧 Project Integration
- Automatic credential file copying
- Custom setup commands per project
- Git worktree isolation
- Branch naming conventions

### 📊 Monitoring & Control
- Real-time agent status with CPU/RAM usage
- Log tailing and session attachment
- Interactive prompt sending
- Batch operations

---

## Commands Reference

### Core Commands

#### `fleet create <branch> [--prompt PROMPT]`
Create a new agent on a specific branch.

```bash
fleet create fix-auth --prompt "Fix the login authentication bug"
```

Options:
- `--prompt, -p`: Initial prompt to send to the agent
- `--agent, -a`: AI agent to use (default: claude)
- `--quick`: Skip setup commands for faster creation

#### `fleet list [--grouped]`
List all running agents with their status.

```bash
fleet list          # Simple table view
fleet list --grouped # Group by batch ID
```

Shows:
- Branch name
- Session status
- CPU/memory usage
- Runtime duration
- Batch ID (if applicable)

#### `fleet prompt <branch> "<message>"`
Send additional instructions to a running agent.

```bash
fleet prompt fix-auth "Add unit tests for the changes"
```

#### `fleet attach <branch>`
Attach to an agent's tmux session interactively.

```bash
fleet attach fix-auth
# Press Ctrl+B, D to detach
```

#### `fleet logs <branch> [-n LINES]`
View the output logs of an agent.

```bash
fleet logs fix-auth          # Last 50 lines (default)
fleet logs fix-auth -n 200   # Last 200 lines
```

#### `fleet kill <pattern>`
Terminate agents matching the pattern.

```bash
fleet kill fix-auth           # Kill specific agent
fleet kill "auth-*"          # Kill all matching pattern
fleet kill --batch batch123   # Kill entire batch
```

Options:
- `--batch`: Treat pattern as batch ID
- `--force`: Skip confirmation prompt

### Parallel Execution Commands

#### `fleet fanout <count> [prefix] --prompt PROMPT`
Create multiple agents with the same prompt.

```bash
# Auto-generated batch ID
fleet fanout 5 --prompt "Refactor the authentication module"
# Creates: fanout-a7b9c2d4-A, fanout-a7b9c2d4-B, ...

# Custom branch prefix
fleet fanout 5 auth-refactor --prompt "Refactor the authentication module"
# Creates: auth-refactor-A, auth-refactor-B, ...
```

Options:
- `--agent, -a`: AI agent to use
- `--quick`: Skip setup commands

#### `fleet multi <branch:prompt> [branch:prompt ...]`
Create multiple agents with different prompts.

```bash
fleet multi \
  fix-auth:"Fix login bug" \
  add-tests:"Add unit tests for auth" \
  update-docs:"Update API documentation"
```

Each agent gets:
- Its own branch
- Its own worktree
- Its own tmux session
- A different initial prompt

### Configuration Commands

#### `fleet init [--type TYPE] [--migrate-legacy]`
Initialize AI Fleet in the current project.

```bash
fleet init                    # Auto-detect project type
fleet init --type rails       # Initialize as Rails project
fleet init --migrate-legacy   # Import from old global config
```

#### `fleet config [--edit] [--validate] [--show-origin]`
Manage AI Fleet configuration.

```bash
fleet config              # Show current project config
fleet config --edit       # Edit project config in $EDITOR
fleet config --validate   # Check configuration validity
fleet config --show-origin # Show where each setting comes from
```

#### `fleet update [--check] [--force]`
Check for and install updates to AI Fleet.

```bash
fleet update           # Check and install updates
fleet update --check   # Only check for updates
fleet update --force   # Force check (bypass cache)
```

The update command automatically detects your installation method (pipx, pip, uv, or source) and uses the appropriate update mechanism.

---

## Configuration

AI Fleet uses project-based configuration. Each project has its own `.aifleet/config.toml` file.

### Initializing a Project

```bash
# Navigate to your git repository
cd /path/to/your/project

# Initialize AI Fleet
fleet init

# Or initialize with a specific project type
fleet init --type rails  # Rails project with sensible defaults
fleet init --type node   # Node.js project
fleet init --type python # Python project
```

### Configuration Structure

```toml
# .aifleet/config.toml - Project configuration
[project]
name = "my-awesome-project"
worktree_root = "~/.aifleet/worktrees/my-awesome-project"

[agent]
default = "claude"
claude_flags = "--dangerously-skip-permissions"

[setup]
credential_files = [
    "config/master.key",
    ".env",
    ".env.local"
]
commands = [
    "bundle install",
    "npm install",
    "bundle exec rails db:create db:migrate"
]
```

---

## Development Setup

### Prerequisites

- Python 3.9+
- Git
- tmux
- uv (recommended) or pip

### Setting Up From Source

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-org/ai-fleet.git
   cd ai-fleet
   ```

2. **Install with uv (recommended)**
   ```bash
   # Install uv if you haven't already
   curl -LsSf https://astral.sh/uv/install.sh | sh
   
   # Create virtual environment and install dependencies
   uv venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   uv pip install -e ".[dev,test]"
   ```

   **Or with pip**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   pip install -e ".[dev,test]"
   ```

3. **Run tests**
   ```bash
   # Run all tests with coverage
   pytest
   
   # Run specific test file
   pytest tests/test_cli.py
   
   # Run with verbose output
   pytest -v
   ```

4. **Run linting and type checking**
   ```bash
   # Linting with Ruff
   ruff check .
   ruff check . --fix  # Auto-fix issues
   
   # Type checking with mypy
   mypy src/
   ```

5. **Install pre-commit hooks (optional)**
   ```bash
   lefthook install
   ```

### Project Structure

```
ai-fleet/
├── src/
│   └── aifleet/
│       ├── cli.py           # Main CLI entry point
│       ├── commands/        # Command implementations
│       │   ├── create.py
│       │   ├── list.py
│       │   ├── prompt.py
│       │   ├── attach.py
│       │   ├── logs.py
│       │   ├── kill.py
│       │   ├── fanout.py
│       │   └── multi.py
│       ├── config.py        # Configuration management
│       ├── state.py         # Agent state tracking
│       ├── tmux.py          # Tmux integration
│       ├── worktree.py      # Git worktree management
│       └── utils.py         # Utility functions
├── tests/                   # Test suite
├── pyproject.toml          # Project configuration
└── README.md               # This file
```

### Making Changes

1. Create a new branch
   ```bash
   git checkout -b feature/your-feature
   ```

2. Make your changes and add tests

3. Run tests and linting
   ```bash
   pytest
   ruff check .
   mypy src/
   ```

4. Commit with descriptive message
   ```bash
   git add .
   git commit -m "Add feature: description"
   ```

---

## Examples

### Example 1: Working on a Bug Fix

```bash
# Create agent for bug fix
fleet create fix-login-bug --prompt "Fix the bug where users can't login with email addresses containing '+' symbol"

# Monitor progress
fleet logs fix-login-bug -n 100

# Add clarification
fleet prompt fix-login-bug "Make sure to handle URL encoding properly"

# Review the changes
fleet attach fix-login-bug

# Clean up
fleet kill fix-login-bug
```

### Example 2: Exploring Multiple Solutions

```bash
# Launch 3 agents to explore different approaches
fleet fanout 3 refactor-auth --prompt "Refactor the authentication system to use JWT tokens instead of sessions"

# Monitor all agents
fleet list --grouped

# Check specific agent
fleet logs refactor-auth-B

# Keep the best solution, kill the rest
fleet kill refactor-auth-A
fleet kill refactor-auth-C
```

### Example 3: Parallel Sprint Work

```bash
# Work on multiple tickets simultaneously
fleet multi \
  fix-432:"Fix user profile image upload bug" \
  feat-433:"Add dark mode toggle to settings" \
  test-434:"Add integration tests for payment flow" \
  docs-435:"Update API documentation for v2 endpoints"

# Check progress on all
fleet list

# Focus on one that needs help
fleet attach feat-433
fleet prompt feat-433 "Use CSS variables for theme colors"

# Clean up completed tasks
fleet kill fix-432
fleet kill test-434
```

### Example 4: Quick Experimentation

```bash
# Skip setup commands for faster iteration
fleet create experiment --prompt "Try using Redis for session storage" --quick

# Quick cleanup of all experimental branches
fleet kill "experiment*"
```

---

## Migration Guide

### Migrating from Global Configuration

If you've been using an older version of AI Fleet with global configuration (`~/.ai_fleet/config.toml`), follow these steps:

1. **Navigate to your project**
   ```bash
   cd /path/to/your/project
   ```

2. **Run migration**
   ```bash
   fleet init --migrate-legacy
   ```

3. **Review the migrated configuration**
   ```bash
   fleet config
   ```

4. **Remove old global config (optional)**
   ```bash
   rm ~/.ai_fleet/config.toml.backup  # After verifying everything works
   ```

### What's Changed

- **Old**: Single global config at `~/.ai_fleet/config.toml`
- **New**: Per-project config at `.aifleet/config.toml`
- **Benefit**: Work on multiple projects without config switching

---

## Troubleshooting

### Common Issues

#### "No agent found for branch"
- Check if the agent is running: `fleet list`
- Ensure you typed the branch name correctly
- The agent might have crashed - check `tmux ls`

#### "Failed to create worktree"
- Ensure `repo_root` in config points to a valid git repository
- Check if the branch name already exists: `git branch -a`
- Verify you have write permissions to `worktree_root`

#### "Command not found: fleet"
- Ensure the package is installed: `pip show ai-fleet`
- Check if the scripts directory is in your PATH
- Try using `python -m aifleet.cli` instead

#### Setup commands failing
- Run `fleet config --validate` to check configuration
- Try creating an agent with `--quick` to skip setup commands
- Check setup command output in logs: `fleet logs <branch>`

### Debug Mode

For verbose output, set the environment variable:
```bash
export AI_FLEET_DEBUG=1
fleet create test-branch --prompt "Test"
```

### Manual Cleanup

If agents get orphaned:

```bash
# List all tmux sessions
tmux ls | grep ai_

# Manual cleanup
tmux kill-session -t ai_branch-name
rm -rf ~/.ai_fleet/worktrees/branch-name

# Reconcile state file
fleet list --repair  # Coming in next version
```

---

## Product Requirements Document

### 0 · Elevator pitch

One CLI lets you launch **N** Claude Code, Codecs, or future LLM agents on isolated git work-trees, stream their logs, and kill them when done.  
Perfect for parallel idea exploration (same prompt) **or** shotgun ticket tackling (different prompts).

**Core Building Block**: Every agent runs in its own isolated environment:
- 1 agent = 1 git worktree + 1 branch + 1 tmux session
- Automatic setup of credentials and dependencies
- Full isolation between agents (no conflicts)

---

### 1 · Problem

* Manual setup of `git worktree + tmux + agent` is slow and error-prone.  
* Juggling many branches/ panes breaks flow.
* No lightweight tool tracks which agent is on which task.

---

### 2 · Goal (MVP scope)

| ✔ Must-have                            | ❌ Out-of-scope for MVP          |
|---------------------------------------|---------------------------------|
| `create <branch> [--prompt]`          | Any GUI / dashboard             |
| `prompt <branch> "<msg>"`             | Docker / Nomad orchestration    |
| `attach <branch>` (tmux)              | Prometheus / alerting           |
| `logs <branch>` tail                  | Winner-picking, auto-merge      |
| `kill <branch>`                       | Fine-grained RBAC               |
| `list` with CPU/RAM %                 | Multiple machines               |
| **fan-out**: `fanout N --prompt`      | Deep Linear automation (phase 2)  |
| **multi**: `multi branch:prompt...`   | Issue tracker integration (phase 2) |

State is persisted in `~/.ai_fleet/state.json`.

---

### 3 · CLI design

| Command                    | Action |
|----------------------------|--------|
| `fleet create fix-42 --prompt "write failing test"` | new work-tree, new tmux session, send prompt |
| `fleet fanout 5 --prompt "refactor auth"`          | spin 5 agents (auto-generates unique batch ID), creates branches `fanout-<UUID>-A1..A5`, each with own worktree + tmux session |
| `fleet fanout 5 auth-refactor --prompt "refactor auth"` | spin 5 agents with custom branch prefix, creates branches `auth-refactor-A1..A5`, each with own worktree + tmux session |
| `fleet multi fix-auth:"Fix login bug" add-tests:"Add auth tests" refactor-db:"Clean up DB layer"` | spin 3 agents with different tasks, creates branches `fix-auth`, `add-tests`, `refactor-db` each with own prompt |
| `fleet prompt fix-42 "green it"`                   | send extra instruction |
| `fleet logs fix-42 [-n 1000]`                      | tail last lines |
| `fleet attach fix-42`                              | attach interactive |
| `fleet kill fix-42`                                | terminate session & delete work-tree |
| `fleet list [--grouped]`                           | show table, optionally group by batch |

*Alias*: `flt` executes the same entry-point for muscle-memory speed.

---

### 3.1 · Fanout Command Details

The `fleet fanout` command is the core building block for parallel agent orchestration. It supports two modes:

#### Mode 1: Auto-generated batch ID (default)
```bash
fleet fanout 5 --prompt "refactor auth"
```
- **Generates a unique batch ID** (e.g., `a7b9c2d4`)
- Creates branches: `fanout-a7b9c2d4-A1` through `fanout-a7b9c2d4-A5`

#### Mode 2: Custom branch prefix
```bash
fleet fanout 5 auth-refactor --prompt "refactor auth"
```
- Uses your specified prefix
- Creates branches: `auth-refactor-A1` through `auth-refactor-A5`

Both modes:
1. **Create N independent agents**, each with:
   - A dedicated git worktree
   - A new branch with the appropriate naming pattern
   - A separate tmux session named after the branch
2. **Send the same prompt** to all agents simultaneously
3. **Track all agents** as a batch for easy management

Benefits:
- Auto-generated IDs prevent branch naming conflicts
- Custom prefixes allow meaningful batch names
- Easy batch identification with `fleet list --grouped`
- Simple cleanup of entire batches with pattern matching

---

### 3.2 · Multi Command - Working on Different Tasks in Parallel

The `fleet multi` command is designed for when you have **multiple distinct tasks**, each requiring its own agent and prompt:

```bash
fleet multi fix-auth:"Fix the login bug" add-tests:"Add unit tests for auth module" refactor-db:"Refactor database connections"
```

This single command:
1. **Parses branch:prompt pairs** from your input
2. **Spins up one agent per task**, each with:
   - Its own git worktree
   - A branch with your specified name (e.g., `fix-auth`)
   - A separate tmux session
   - Your custom prompt as its initial instruction
3. **Manages all agents** from one CLI

#### Key Difference: Fanout vs Multi

| Mode | Use Case | Prompts | Example |
|------|----------|---------|---------|
| **fanout** | Same task, multiple approaches | All agents get the SAME prompt | 5 agents all trying different ways to "refactor auth" |
| **multi** | Different tasks in parallel | Each agent gets a DIFFERENT prompt | Agent 1 fixes bug, Agent 2 adds feature, Agent 3 writes tests |

#### Why Multi Mode?

Perfect for:
- Working through a sprint backlog
- Tackling multiple bug fixes simultaneously  
- Exploring different features in parallel
- Letting agents work independently while you review/guide them

The tool handles all the plumbing (worktree setup, credentials, tmux sessions) so you can focus on managing the agents and their progress.

---

### 4 · Internal file layout

*(all paths are overridable in `config.toml`)*

```
~/.ai_fleet/
├─ config.toml  # global settings (generated on first run)
├─ state.json   # live agent registry (CLI updates atomically)
└─ worktrees/   # default parent dir for auto-created worktrees
```

#### 4.1 · `config.toml` keys

| Key | Default | Purpose |
|-----|---------|---------|
| `repo_root`        | `~/code/my-project` | Monorepo root for worktree creation |
| `worktree_root`    | `~/.ai_fleet/worktrees` | Where branches are checked out |
| `tmux_prefix`      | `ai_` | All tmux sessions are named `<prefix><branch>` |
| `default_agent`    | `claude` | `claude` \| `codecs` (future runtimes) |
| `claude_flags`     | `--dangerously-skip-permissions` | Extra flags appended to `claude` |
| `credential_files` | `[]` | Files to copy from main repo to each worktree |
| `setup_commands`   | `[]` | Commands to run after worktree creation |

Create or edit this file by running:
```bash
fleet config edit
```

#### 4.1.1 · Worktree Setup Configuration

For projects that need credentials or setup steps (like Rails apps), configure in `config.toml`:

```toml
# Copy credential files from main repo to each worktree
credential_files = [
    "config/master.key",
    "config/credentials/development.key",
    ".env",
    ".env.local"
]

# Run these commands in each new worktree (executed in order)
setup_commands = [
    "bundle install",
    "npm install",
    "bundle exec rake db:create db:migrate",
    "bundle exec rake assets:precompile"
]

# Optional: Quick setup mode (skip heavy commands)
quick_setup = true  # When true, only copies files, skips setup_commands
```

**Note**: Setup commands run in the worktree directory. Use `&&` to chain commands or check success.

#### 4.2 · `state.json` schema (MVP)

```json
[
  {
    "branch": "fix-42",
    "worktree": "/home/nacho/.ai_fleet/worktrees/fix-42",
    "session": "ai_fix-42",
    "pid": 12345,
    "batch_id": "manual-2025-05-31",
    "agent": "claude",
    "created_at": "2025-05-31T23:05:00Z"
  }
]
```

CLI commands never rely solely on this file: `fleet list --repair` reconciles real tmux sessions against disk if the file gets out of sync.

---

### 5 · Tech stack snapshot (MVP)

| Layer | Choice | Rationale |
|-------|--------|-----------|
| Language | Python 3.11 + Click | fast to iterate, easy to refactor |
| Proc supervisor | tmux | ubiquitous, allows send-keys |
| Data store | Flat JSON + TOML | no DB dependency |
| Metrics | psutil | per-PID CPU/RAM collection |
| Packaging | PyPI ai-fleet | installs fleet + flt binaries |

---

### 6 · Key interactions / happy-path demo

```bash
# install
pipx install ai-fleet
export ANTHROPIC_API_KEY=sk-...

# explore 3 versions of the same idea
fleet fanout 3 auth-refactor --prompt "refactor auth flow"

# parallel sprint - work on different tasks
fleet multi fix-auth:"Fix login bug" add-tests:"Add auth module tests" update-docs:"Update API documentation"

# monitor
fleet list --grouped        # see CPU/RAM per agent
fleet logs fix-auth -n 200  # tail
fleet prompt fix-auth "run tests"

# manual dive-in
fleet attach auth-refactor-A2

# clean everything from a batch
fleet kill auth-refactor-A*    # glob supported
```

---

### 7 · Success metrics

| KPI | Target |
|-----|--------|
| fleet create → first agent reply | ≤ 10 s |
| Fan-out launch (N=5) | ≤ 20 s |
| Orphaned worktrees after kill | 0 % |
| CLI memory footprint | ~0 MB |
| Test suite ✔ on CI | 100 % |

---

### 8 · Roadmap after MVP

- **Ticket integration** – fetch task descriptions from Linear/GitHub/Jira for `fleet multi`
- **REST/WebSocket shim** – expose same ops for a SwiftUI dashboard.
- **Cost tracking** – poll /cost (Claude) & usage logs; Prometheus exporter.
- **Linear / GitHub webhooks** – auto-spawn agents on ticket creation.
- **Container mode** – optional Docker/Nomad backend for hard CPU/RAM caps.
- **Winner-picker** – batch command to run tests, rank branches, highlight best.
- **Merge-assistant** – create PRs automatically and comment results.

---

### 9 · Open questions

| Area | Question |
|------|---------|
| Concurrency | Hard cap on simultaneous Claude/Codecs sessions per org? |
| Isolation | When to require Docker to avoid RAM blow-ups? |
| Auth | Stick with env vars or integrate doppler/1Password secrets? |
| Branch hygiene | Enforce prefix patterns (fix-*, feature-*), auto-delete merged? |

---

### 10 · Namespace & packaging

| Thing | Value |
|-------|---------|
| PyPI | ai-fleet |
| Import path | aifleet.* |
| Executables | fleet, flt |
| GitHub repo | github.com/your-org/ai-fleet |

**Tip**: publish a 0.0.0 stub to reserve the PyPI name before going public.

---

### 11 · Project-Specific Setup Examples

#### Rails Project
```toml
credential_files = [
    "config/master.key",
    "config/credentials/development.key"
]

setup_commands = [
    "bundle install",
    "RAILS_ENV=test bundle exec rails db:create db:migrate",
    "RAILS_ENV=test bundle exec rails assets:precompile"
]
```

#### Node.js Project
```toml
credential_files = [".env", ".env.local"]

setup_commands = [
    "npm install",
    "npm run build"
]
```

#### Python Project
```toml
credential_files = [".env", "secrets.json"]

setup_commands = [
    "uv sync",  # or "pip install -r requirements.txt"
    "python manage.py migrate"  # for Django
]
```

**Tip**: Use `fleet config validate` to check your setup configuration before creating agents.

---

### 12 · License
MIT – do what you want, just don't sue.
(Change if you prefer Apache-2.0 or GPL.)