"""Kill command to terminate AI agents."""

import fnmatch
from pathlib import Path
from typing import List

import click

from ..state import Agent, StateManager
from ..tmux import TmuxManager
from ..worktree import WorktreeManager
from .base import ensure_project_config


@click.command()
@click.argument("pattern", required=False)
@click.option("--batch", "-b", help="Kill all agents in a batch")
@click.option("--force", "-f", is_flag=True, help="Skip confirmation")
@click.option("--delete-branch", "-d", is_flag=True, help="Also delete the git branch")
def kill(pattern: str, batch: str, force: bool, delete_branch: bool) -> None:
    """Kill agents matching the pattern.

    Pattern can be a branch name or a glob pattern (e.g., 'feature-*').
    If no pattern is provided and --batch is not specified, shows an error.
    """
    config = ensure_project_config()
    state = StateManager(config.repo_root)
    tmux = TmuxManager(config.tmux_prefix)
    worktree = WorktreeManager(config.repo_root, config.worktree_root)

    # Get agents to kill
    all_agents = state.list_agents()
    agents_to_kill: List[Agent] = []

    if batch:
        # Kill by batch ID
        agents_to_kill = [a for a in all_agents if a.batch_id == batch]
        if not agents_to_kill:
            click.echo(f"No agents found in batch '{batch}'")
            raise SystemExit(1)
    elif pattern:
        # Kill by pattern
        for agent in all_agents:
            if fnmatch.fnmatch(agent.branch, pattern):
                agents_to_kill.append(agent)
        if not agents_to_kill:
            click.echo(f"No agents found matching pattern '{pattern}'")
            raise SystemExit(1)
    else:
        click.echo("Error: Specify a pattern or use --batch")
        raise SystemExit(1)

    # Show what will be killed
    click.echo(f"Will kill {len(agents_to_kill)} agent(s):")
    for agent in agents_to_kill:
        click.echo(f"  - {agent.branch} (session: {agent.session})")

    # Confirm unless forced
    if not force:
        if not click.confirm("Continue?"):
            click.echo("Aborted.")
            raise SystemExit(0)

    # Kill each agent
    killed_count = 0
    failed_agents = []

    for agent in agents_to_kill:
        click.echo(f"\nProcessing agent '{agent.branch}'...")

        # First, try to remove the worktree (this is the most likely to fail)
        if agent.worktree and Path(agent.worktree).exists():
            if not worktree.remove_worktree(Path(agent.worktree), force=False):
                # Try to get more info about why it failed
                click.echo(f"  ⚠️  Failed to remove worktree at {agent.worktree}")
                click.echo("  This usually happens when there are uncommitted changes.")

                prompt = "  Force remove worktree (will lose uncommitted changes)?"
                if force or click.confirm(prompt):
                    if not worktree.remove_worktree(Path(agent.worktree), force=True):
                        click.echo("  ❌ Failed to force remove worktree")
                        failed_agents.append(agent)
                        continue
                else:
                    click.echo("  Skipping this agent")
                    failed_agents.append(agent)
                    continue

        # Only proceed if worktree was successfully removed
        # Kill tmux session
        if tmux.session_exists(agent.branch):
            if tmux.kill_session(agent.branch):
                click.echo("  ✓ Killed tmux session")
            else:
                click.echo("  ⚠️  Failed to kill tmux session")

        # Delete branch if requested
        if delete_branch:
            # Check if we're not on this branch
            success, current_branch, _ = worktree._run_git(["branch", "--show-current"])
            if success and current_branch.strip() == agent.branch:
                click.echo(
                    f"  ⚠️  Cannot delete branch '{agent.branch}' "
                    "(currently checked out)"
                )
            else:
                success, _, stderr = worktree._run_git(["branch", "-D", agent.branch])
                if success:
                    click.echo(f"  ✓ Deleted branch '{agent.branch}'")
                else:
                    click.echo(f"  ⚠️  Failed to delete branch: {stderr.strip()}")

        # Remove from state
        state.remove_agent(agent.branch)
        killed_count += 1
        click.echo(f"  ✅ Agent '{agent.branch}' killed successfully")

    # Summary
    click.echo(f"\n{'=' * 50}")
    click.echo(f"Killed {killed_count} agent(s) successfully.")

    if failed_agents:
        click.echo(f"\n⚠️  Failed to kill {len(failed_agents)} agent(s):")
        for agent in failed_agents:
            click.echo(f"  - {agent.branch}")
        click.echo("\nTo force kill these agents, run:")
        click.echo(f"  fleet kill --force {' '.join(a.branch for a in failed_agents)}")

    if not delete_branch and killed_count > 0:
        click.echo("\n💡 Tip: Use --delete-branch/-d to also delete the git branches")
