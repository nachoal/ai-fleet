# ai-fleet 🚀

*“Spin up and command a **fleet** of AI developer agents from your terminal.”*

---

## Product-Requirements Document (MVP + Fan-Out Add-On)

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
MIT – do what you want, just don’t sue.
(Change if you prefer Apache-2.0 or GPL.)

