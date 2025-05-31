"""Kill command to terminate agents."""

import fnmatch
from pathlib import Path

import click

from ..config import ConfigManager
from ..state import StateManager
from ..tmux import TmuxManager
from ..worktree import WorktreeManager


@click.command()
@click.argument("pattern")
@click.option("--batch", is_flag=True, help="Kill all agents in a batch")
@click.option("--force", is_flag=True, help="Force kill without confirmation")
def kill(pattern: str, batch: bool, force: bool) -> None:
    """Kill agents matching the pattern.

    Args:
        pattern: Branch name or pattern (supports glob)
        batch: If true, pattern is treated as batch ID
        force: Skip confirmation prompt
    """
    config = ConfigManager()
    state = StateManager(config.repo_root)
    tmux = TmuxManager(config.tmux_prefix)
    worktree = WorktreeManager(config.repo_root, config.worktree_root)

    # Find agents to kill
    agents_to_kill = []

    if batch:
        # Kill all agents in batch
        agents = state.list_agents(batch_id=pattern)
        if not agents:
            click.echo(f"No agents found in batch '{pattern}'")
            raise SystemExit(1)
        agents_to_kill = agents
    else:
        # Find agents matching pattern
        all_agents = state.list_agents()
        for agent in all_agents:
            if fnmatch.fnmatch(agent.branch, pattern):
                agents_to_kill.append(agent)

        if not agents_to_kill:
            click.echo(f"No agents found matching pattern '{pattern}'")
            raise SystemExit(1)

    # Show agents to be killed
    click.echo(f"\nAgents to be killed ({len(agents_to_kill)}):")
    for agent in agents_to_kill:
        click.echo(f"  - {agent.branch} (session: {agent.session})")

    # Confirm unless forced
    if not force:
        if not click.confirm("\nKill these agents?"):
            click.echo("Aborted.")
            raise SystemExit(0)

    # Kill each agent
    killed_count = 0
    for agent in agents_to_kill:
        # Kill tmux session
        if tmux.session_exists(agent.session):
            tmux.kill_session(agent.session)

        # Remove worktree
        if agent.worktree:
            worktree.remove_worktree(Path(agent.worktree))

        # Remove from state
        state.remove_agent(agent.branch)
        killed_count += 1
        click.echo(f"Killed agent on branch '{agent.branch}'")

    click.echo(f"\nKilled {killed_count} agent(s).")
