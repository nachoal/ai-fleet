"""Fanout command to create multiple agents with the same prompt."""

import string
from datetime import datetime

import click

from ..state import Agent, StateManager
from ..tmux import TmuxManager
from ..utils import generate_batch_id, safe_branch_name
from ..worktree import WorktreeManager
from .base import ensure_project_config


def generate_suffix(index: int) -> str:
    """Generate a suffix for branch names (A, B, C, ..., AA, AB, ...)."""
    suffix = ""
    while index >= 0:
        suffix = string.ascii_uppercase[index % 26] + suffix
        index = index // 26 - 1
    return suffix


@click.command()
@click.argument("count", type=int)
@click.argument("prefix", required=False)
@click.option("--prompt", "-p", required=True, help="Prompt to send to all agents")
@click.option("--agent", "-a", help="AI agent to use (overrides config)")
@click.option("--quick", is_flag=True, help="Skip setup commands")
def fanout(count: int, prefix: str, prompt: str, agent: str, quick: bool) -> None:
    """Create multiple agents with the same prompt.

    Args:
        count: Number of agents to create
        prefix: Branch name prefix (optional)
        prompt: The prompt to send to all agents
        agent: AI agent to use
        quick: Skip setup commands
    """
    if count < 1:
        click.echo("Count must be at least 1")
        raise SystemExit(1)

    if count > 100:
        click.echo("Count cannot exceed 100")
        raise SystemExit(1)

    config = ensure_project_config()
    state = StateManager(config.repo_root)
    tmux = TmuxManager(config.tmux_prefix)
    worktree = WorktreeManager(config.repo_root, config.worktree_root)

    # Use default prefix if not provided
    if not prefix:
        # Generate prefix from prompt (first few words)
        words = prompt.split()[:3]
        prefix = safe_branch_name("-".join(words))

    # Generate batch ID
    batch_id = generate_batch_id()
    agent_name = agent or config.default_agent

    # Create agents
    created_agents = []
    for i in range(count):
        suffix = generate_suffix(i)
        branch_name = f"{prefix}-{suffix}"

        click.echo(f"\nCreating agent {i + 1}/{count}: {branch_name}")

        # Setup worktree
        worktree_path = worktree.setup_worktree(
            branch=branch_name,
            credential_files=config.credential_files,
            setup_commands=config.setup_commands,
            quick_setup=quick,
        )

        if not worktree_path:
            click.echo(f"Failed to create worktree for branch '{branch_name}'")
            continue

        # Create tmux session
        session_name = f"{config.tmux_prefix}{branch_name}"
        if tmux.create_session(branch_name, str(worktree_path)):
            # Send initial command
            cmd = f"{agent_name} {config.claude_flags} '{prompt}'"
            tmux.send_command(branch_name, cmd)

            # Create agent record
            agent_obj = Agent(
                branch=branch_name,
                worktree=str(worktree_path),
                session=session_name,
                batch_id=batch_id,
                agent=agent_name,
                created_at=datetime.now().isoformat(),
                pid=None,  # Will be updated later
                prompt=prompt,
            )
            state.add_agent(agent_obj)
            created_agents.append(branch_name)
            click.echo(f"✓ Started agent on branch '{branch_name}'")
        else:
            click.echo(f"Failed to create session for branch '{branch_name}'")
            worktree.remove_worktree(worktree_path)

    # Summary
    click.echo(f"\nCreated {len(created_agents)} agent(s) in batch '{batch_id}'")
    if created_agents:
        click.echo("\nBranches created:")
        for branch in created_agents:
            click.echo(f"  - {branch}")
        click.echo("\nTo see all agents: fleet list")
        click.echo(f"To kill all agents: fleet kill --batch {batch_id}")
