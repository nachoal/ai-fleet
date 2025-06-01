"""Create command for AI Fleet."""

import subprocess
import sys
import time
from datetime import datetime

import click

from ..state import Agent, StateManager
from ..tmux import TmuxManager
from ..worktree import WorktreeManager
from .base import ensure_project_config


def verify_agent_command(agent: str) -> bool:
    """Verify that the agent command exists and is executable.

    Args:
        agent: The agent command (e.g., 'claude')

    Returns:
        True if command exists and is executable
    """
    try:
        result = subprocess.run(["which", agent], capture_output=True, text=True)
        return result.returncode == 0
    except Exception:
        return False


@click.command()
@click.argument("branch")
@click.option("--prompt", "-p", help="Initial prompt to send to the agent")
@click.option("--agent", "-a", help="Agent to use (default: from config)")
def create(branch: str, prompt: str, agent: str):
    """Create a new AI agent on a branch.

    Creates a git worktree, sets up the environment, launches a tmux session,
    and starts the AI agent with an optional prompt.
    """
    # Load configuration
    config = ensure_project_config()
    state = StateManager(config.repo_root)

    # Use configured agent if not specified
    if not agent:
        agent = config.default_agent

    # Verify agent command exists
    if not verify_agent_command(agent):
        click.echo(f"Error: Agent command '{agent}' not found in PATH", err=True)
        click.echo("Please ensure the agent is installed and accessible", err=True)
        sys.exit(1)

    # Initialize managers
    worktree_mgr = WorktreeManager(config.repo_root, config.worktree_root)
    tmux_mgr = TmuxManager(config.tmux_prefix)

    # Check if agent already exists
    if state.get_agent(branch):
        click.echo(f"Agent already exists for branch: {branch}", err=True)
        sys.exit(1)

    click.echo(f"Creating agent on branch '{branch}'...")

    # Create and setup worktree
    click.echo("Setting up worktree...")
    worktree_path = worktree_mgr.setup_worktree(
        branch, config.credential_files, config.setup_commands, config.quick_setup
    )

    if not worktree_path:
        click.echo("Failed to create worktree", err=True)
        sys.exit(1)

    # Create tmux session
    click.echo("Creating tmux session...")
    session = tmux_mgr.create_session(branch, str(worktree_path))

    if not session:
        click.echo("Failed to create tmux session", err=True)
        # Clean up worktree
        worktree_mgr.remove_worktree(worktree_path, force=True)
        sys.exit(1)

    # Build agent command
    agent_cmd = agent
    if config.claude_flags and agent == "claude":
        agent_cmd = f"{agent} {config.claude_flags}"

    # Send agent startup command
    click.echo(f"Starting {agent} agent...")
    if prompt:
        # Start agent with prompt
        full_command = f"{agent_cmd} '{prompt}'"
    else:
        # Just start agent
        full_command = agent_cmd

    if not tmux_mgr.send_command(branch, full_command):
        click.echo("Failed to start agent", err=True)
        # Clean up
        tmux_mgr.kill_session(branch)
        worktree_mgr.remove_worktree(worktree_path, force=True)
        sys.exit(1)

    # Wait a moment for the agent to start
    time.sleep(3)

    # Get session info for PID
    session_info = tmux_mgr.get_session_info(branch)
    pid = session_info.get("pid") if session_info else None

    # Check if session is still alive
    if not session_info:
        click.echo("\nError: Session died immediately after creation", err=True)

        # Try to capture any error output
        output = tmux_mgr.get_session_output(branch, lines=50)
        if output:
            click.echo("\nSession output before crash:")
            click.echo("-" * 50)
            click.echo(output)
            click.echo("-" * 50)

        # Clean up
        worktree_mgr.remove_worktree(worktree_path, force=True)
        click.echo("\nPossible causes:")
        click.echo("- The agent command crashed or exited immediately")
        click.echo("- Missing dependencies or environment variables")
        click.echo("- The agent may have processed the prompt and exited")
        click.echo("\nTry running without a prompt first:")
        click.echo(f"  fleet create {branch}")
        sys.exit(1)

    # Save to state
    agent_record = Agent(
        branch=branch,
        worktree=str(worktree_path),
        session=tmux_mgr._session_name(branch),
        batch_id=f"manual-{datetime.now().strftime('%Y%m%d')}",
        agent=agent,
        created_at=datetime.now().isoformat(),
        pid=pid,
        prompt=prompt,
    )
    state.add_agent(agent_record)

    click.echo("\n✅ Agent created successfully!")
    click.echo(f"   Branch: {branch}")
    click.echo(f"   Worktree: {worktree_path}")
    click.echo(f"   Session: {agent_record.session}")

    click.echo("\n📺 To attach to the agent:")
    click.echo(f"   fleet attach {branch}")

    click.echo("\n📝 To send additional prompts:")
    click.echo(f'   fleet prompt {branch} "your prompt here"')

    click.echo("\n🔍 To view logs:")
    click.echo(f"   fleet logs {branch}")

    # Final check that session is still alive
    time.sleep(1)
    if not tmux_mgr.get_session_info(branch):
        click.echo("\n⚠️  Warning: Agent session appears to have died")
        click.echo("   The agent may have exited after processing the initial prompt")
        click.echo("   Check 'tmux list-sessions' to verify")
