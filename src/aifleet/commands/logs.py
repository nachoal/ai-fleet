"""Logs command to view agent output."""

import click

from ..state import StateManager
from ..tmux import TmuxManager
from .base import ensure_project_config


@click.command()
@click.argument("branch")
@click.option("-n", "--lines", default=50, help="Number of lines to show")
def logs(branch: str, lines: int) -> None:
    """Tail the logs of a running agent.

    Args:
        branch: The branch name of the agent
        lines: Number of lines to show (default: 50)
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

    # Get session output
    output = tmux.get_session_output(branch, lines)
    if output:
        click.echo(output)
    else:
        click.echo(f"No output available from session '{agent.session}'")
