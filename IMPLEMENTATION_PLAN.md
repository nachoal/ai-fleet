# AI Fleet Implementation Plan

## Overview

This document outlines the implementation plan for the AI Fleet MVP - a CLI tool to manage multiple AI coding agents in parallel using git worktrees and tmux sessions.

## Core Principles

1. **Simplicity First**: Start with the minimal viable features
2. **No Over-Engineering**: Flat files (JSON/TOML) instead of databases
3. **Unix Philosophy**: Do one thing well, compose with other tools
4. **Fast Iteration**: Get basic commands working, then enhance

## Architecture Overview

```
ai-fleet/
├── src/aifleet/
│   ├── __init__.py          # Package initialization
│   ├── cli.py               # Click CLI entry point
│   ├── config.py            # Configuration management (TOML)
│   ├── state.py             # Agent state tracking (JSON)
│   ├── agent.py             # Agent lifecycle management
│   ├── worktree.py          # Git worktree operations
│   ├── tmux.py              # Tmux session management
│   ├── commands/            # CLI command implementations
│   │   ├── __init__.py
│   │   ├── create.py        # fleet create
│   │   ├── fanout.py        # fleet fanout
│   │   ├── multi.py         # fleet multi
│   │   ├── control.py       # prompt, attach, logs, kill
│   │   └── list.py          # fleet list
│   └── utils.py             # Shared utilities
```

## Implementation Phases

### Phase 1: Foundation (Core Infrastructure)

#### 1.1 Configuration Management (`config.py`)
```python
# Key features:
- Load/save config from ~/.ai_fleet/config.toml
- Default values with override capability
- Validate configuration
- Create config directory structure on first run
```

**Tasks:**
- [ ] Create ConfigManager class
- [ ] Implement TOML loading/saving
- [ ] Define default configuration schema
- [ ] Add validation logic
- [ ] Create `fleet config edit` command

#### 1.2 State Management (`state.py`)
```python
# Key features:
- Track active agents in ~/.ai_fleet/state.json
- Atomic updates to prevent corruption
- Query agents by branch, batch_id, etc.
- Reconcile with actual tmux sessions
```

**Tasks:**
- [ ] Create StateManager class
- [ ] Implement JSON persistence with file locking
- [ ] Add CRUD operations for agent records
- [ ] Implement state reconciliation with tmux
- [ ] Add query/filter methods

#### 1.3 Git Worktree Operations (`worktree.py`)
```python
# Key features:
- Create worktrees with new or existing branches
- Copy credential files from main repo
- Run setup commands
- Clean up worktrees
```

**Tasks:**
- [ ] Create WorktreeManager class
- [ ] Implement worktree creation
- [ ] Add credential file copying
- [ ] Implement setup command execution
- [ ] Add worktree deletion with safety checks

#### 1.4 Tmux Integration (`tmux.py`)
```python
# Key features:
- Create tmux sessions with consistent naming
- Send commands to sessions
- Capture output/logs
- Monitor session status
- Clean up sessions
```

**Tasks:**
- [ ] Create TmuxManager class using libtmux
- [ ] Implement session creation
- [ ] Add command sending functionality
- [ ] Implement log capture
- [ ] Add session monitoring (PID, status)
- [ ] Add session cleanup

### Phase 2: Core Commands

#### 2.1 Create Command (`commands/create.py`)
```bash
fleet create fix-auth --prompt "Fix the authentication bug"
```

**Tasks:**
- [ ] Parse arguments (branch, prompt)
- [ ] Create worktree
- [ ] Copy credentials
- [ ] Run setup commands
- [ ] Create tmux session
- [ ] Launch agent with prompt
- [ ] Update state

#### 2.2 Fanout Command (`commands/fanout.py`)
```bash
fleet fanout 3 --prompt "Refactor auth module"
fleet fanout 3 auth-refactor --prompt "Refactor auth module"
```

**Tasks:**
- [ ] Generate batch ID if not provided
- [ ] Create N branches with naming pattern
- [ ] Parallel worktree creation
- [ ] Launch N agents with same prompt
- [ ] Track as batch in state

#### 2.3 Multi Command (`commands/multi.py`)
```bash
fleet multi fix-auth:"Fix login" add-tests:"Add test coverage"
```

**Tasks:**
- [ ] Parse branch:prompt pairs
- [ ] Create worktrees for each task
- [ ] Launch agents with different prompts
- [ ] Track as batch in state

### Phase 3: Management Commands

#### 3.1 Control Commands (`commands/control.py`)
```bash
fleet prompt fix-auth "Run the tests"
fleet attach fix-auth
fleet logs fix-auth -n 100
fleet kill fix-auth
```

**Tasks:**
- [ ] Implement prompt sending via tmux
- [ ] Add interactive attach functionality
- [ ] Implement log tailing
- [ ] Add kill with cleanup (tmux + worktree)

#### 3.2 List Command (`commands/list.py`)
```bash
fleet list
fleet list --grouped
```

**Tasks:**
- [ ] Query active agents from state
- [ ] Reconcile with actual tmux sessions
- [ ] Get CPU/RAM metrics via psutil
- [ ] Format as table
- [ ] Add grouping by batch_id

### Phase 4: Polish & Testing

#### 4.1 Error Handling
- [ ] Add proper error messages
- [ ] Implement rollback on partial failures
- [ ] Add --force flags where appropriate
- [ ] Handle edge cases (branch exists, session exists, etc.)

#### 4.2 User Experience
- [ ] Add progress indicators
- [ ] Implement --verbose flag
- [ ] Add confirmation prompts for destructive actions
- [ ] Improve command output formatting

#### 4.3 Testing
- [ ] Unit tests for core modules
- [ ] Integration tests for commands
- [ ] Test credential file handling
- [ ] Test parallel operations
- [ ] Test error scenarios

## Implementation Order

1. **Week 1**: Foundation
   - config.py (Day 1-2)
   - state.py (Day 2-3)
   - tmux.py (Day 3-4)
   - worktree.py (Day 4-5)

2. **Week 2**: Core Commands
   - create command (Day 1-2)
   - fanout command (Day 2-3)
   - multi command (Day 3-4)
   - Basic list command (Day 4-5)

3. **Week 3**: Management & Polish
   - Control commands (Day 1-2)
   - Enhanced list with metrics (Day 2-3)
   - Error handling (Day 3-4)
   - Testing & bug fixes (Day 4-5)

## Key Technical Decisions

### 1. Subprocess vs Libraries
- Use `subprocess` for git operations (simple, reliable)
- Use `libtmux` for tmux integration (better control)
- Use `psutil` for process metrics

### 2. Parallel Execution
- Use Python's `threading` for parallel worktree setup
- Limit parallelism to avoid resource exhaustion
- Show progress for long operations

### 3. State Management
- Use file locking for atomic updates
- Reconcile state on every list operation
- State file is advisory, not authoritative

### 4. Error Recovery
- Each command should be idempotent where possible
- Partial failures should clean up resources
- Clear error messages with suggested fixes

## MVP Success Criteria

1. Can create and manage 5+ agents simultaneously
2. Worktree setup completes in <10s per agent
3. No orphaned resources after kill
4. Commands feel responsive (<1s for most operations)
5. Clear error messages when things go wrong

## Post-MVP Enhancements

1. **Configuration Templates**: Project-specific setup templates
2. **Agent Templates**: Pre-configured prompts for common tasks
3. **Metrics Dashboard**: Web UI for monitoring agents
4. **Cost Tracking**: Track token usage per agent
5. **Integration**: Linear/GitHub issue fetching
6. **Advanced Features**: Winner picking, auto-merge

## Development Workflow

1. Start with CLI skeleton using Click
2. Implement one module at a time with tests
3. Manual testing with real git repos
4. Document each command with examples
5. Package and test installation via pip

## Notes

- Keep dependencies minimal (click, psutil, toml, libtmux)
- Make operations resumable (handle Ctrl+C gracefully)
- Log operations for debugging (--verbose flag)
- Consider Windows compatibility (tmux alternatives)