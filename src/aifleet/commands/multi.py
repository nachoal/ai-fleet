"""Multi command to create agents with different prompts."""

from datetime import datetime

import click

from ..state import Agent, StateManager
from ..tmux import TmuxManager
from ..utils import generate_batch_id, parse_branch_prompt_pairs
from ..worktree import WorktreeManager
from .base import ensure_project_config


@click.command()
@click.argument("pairs", nargs=-1, required=True)
@click.option("--agent", "-a", help="AI agent to use (overrides config)")
@click.option("--quick", is_flag=True, help="Skip setup commands")
def multi(pairs: tuple, agent: str, quick: bool) -> None:
    """Create multiple agents with different prompts.

    Usage: aim multi branch1:"prompt 1" branch2:"prompt 2" ...

    Args:
        pairs: Branch:prompt pairs
        agent: AI agent to use
        quick: Skip setup commands
    """
    if not pairs:
        click.echo("No branch:prompt pairs provided")
        raise SystemExit(1)

    config = ensure_project_config()
    state = StateManager(config.repo_root)
    tmux = TmuxManager(config.tmux_prefix)
    worktree = WorktreeManager(config.repo_root, config.worktree_root)

    # Parse branch:prompt pairs
    try:
        branch_prompts = parse_branch_prompt_pairs(list(pairs))
    except Exception as e:
        click.echo(f"Error parsing pairs: {e}")
        raise SystemExit(1) from e

    # Generate batch ID
    batch_id = generate_batch_id()
    agent_name = agent or config.default_agent

    # Create agents
    created_agents = []
    total = len(branch_prompts)

    for i, (branch_name, prompt) in enumerate(branch_prompts):
        click.echo(f"\nCreating agent {i + 1}/{total}: {branch_name}")

        # Check if agent already exists
        if state.get_agent(branch_name):
            click.echo(f"Agent already exists on branch '{branch_name}', skipping")
            continue

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
            click.echo(
                f"✓ Started agent on branch '{branch_name}' with prompt: "
                f"{prompt[:50]}..."
            )
        else:
            click.echo(f"Failed to create session for branch '{branch_name}'")
            worktree.remove_worktree(worktree_path)

    # Summary
    click.echo(f"\nCreated {len(created_agents)} agent(s) in batch '{batch_id}'")
    if created_agents:
        click.echo("\nAgents created:")
        for branch in created_agents:
            click.echo(f"  - {branch}")
        click.echo("\nTo see all agents: fleet list")
        click.echo(f"To kill all agents: fleet kill --batch {batch_id}")
