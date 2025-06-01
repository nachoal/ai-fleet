"""Attach command to connect to agent tmux sessions."""

import click

from ..state import StateManager
from ..tmux import TmuxManager
from .base import ensure_project_config


@click.command()
@click.argument("branch")
def attach(branch: str) -> None:
    """Attach to a running agent's tmux session.

    Args:
        branch: The branch name of the agent
    """
    config = ensure_project_config()
    state = StateManager(config.repo_root)
    tmux = TmuxManager(config.tmux_prefix)

    # Get the agent
    agent = state.get_agent(branch)
    if not agent:
        click.echo(f"No agent found for branch '{branch}'")
        raise SystemExit(1)

    # Check if session exists
    if not tmux.session_exists(branch):
        click.echo(f"Session '{agent.session}' not found")
        # Clean up state
        state.remove_agent(branch)
        raise SystemExit(1)

    # Attach to the session
    click.echo(f"Attaching to session '{agent.session}'...")
    click.echo("Press Ctrl+B, D to detach")
    tmux.attach_session(branch)
