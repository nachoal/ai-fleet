"""Prompt command to send messages to running agents."""

import click

from ..config import ConfigManager
from ..state import StateManager
from ..tmux import TmuxManager


@click.command()
@click.argument("branch")
@click.argument("message")
def prompt(branch: str, message: str) -> None:
    """Send an additional prompt to a running agent.

    Args:
        branch: The branch name of the agent
        message: The prompt message to send
    """
    config = ConfigManager()
    state = StateManager(config.repo_root)
    tmux = TmuxManager(config.tmux_prefix)

    # Get the agent
    agent = state.get_agent(branch)
    if not agent:
        click.echo(f"No agent found for branch '{branch}'")
        raise SystemExit(1)

    # Check if session exists
    if not tmux.session_exists(agent.session):
        click.echo(f"Session '{agent.session}' not found")
        # Clean up state
        state.remove_agent(branch)
        raise SystemExit(1)

    # Send the prompt
    success = tmux.send_command(agent.session, message)
    if success:
        click.echo(f"Sent prompt to agent on branch '{branch}'")
    else:
        click.echo(f"Failed to send prompt to agent on branch '{branch}'")
        raise SystemExit(1)
