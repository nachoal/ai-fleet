"""List command for AI Fleet."""

import sys
import time
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Union

import click
import psutil

from ..config import ConfigManager
from ..state import StateManager
from ..tmux import TmuxManager
from ..utils import format_duration
from .base import ensure_project_config


def get_process_stats(pid: Optional[int]) -> Tuple[float, float]:
    """Get CPU and memory usage for a process.

    Returns:
        (cpu_percent, memory_mb)
    """
    if not pid:
        return 0.0, 0.0

    try:
        process = psutil.Process(pid)
        cpu = process.cpu_percent(interval=0.1)
        memory = process.memory_info().rss / 1024 / 1024  # MB
        return cpu, memory
    except Exception:
        return 0.0, 0.0


def display_agents(
    config: ConfigManager,
    state: StateManager,
    tmux_mgr: TmuxManager,
    grouped: bool,
    all: bool,
) -> None:
    """Display agent list once."""

    # Get active tmux sessions
    active_sessions = [name for name, _ in tmux_mgr.list_sessions()]

    # Reconcile state with tmux
    if not all:
        removed = state.reconcile_with_tmux(active_sessions)
        if removed:
            click.echo(f"Cleaned up {len(removed)} dead agents from state", err=True)

    # Get all agents
    agents = state.list_agents()

    if not agents:
        click.echo("No active agents")
        return

    # Collect agent data
    agent_data: List[Dict[str, Union[str, float]]] = []
    for agent in agents:
        # Get agent status using new detection method
        status = tmux_mgr.get_agent_status(agent.branch)

        # Get process stats
        cpu, memory = get_process_stats(agent.pid)

        # Calculate uptime
        created = datetime.fromisoformat(agent.created_at)
        uptime = datetime.now() - created

        agent_data.append(
            {
                "branch": agent.branch,
                "batch_id": agent.batch_id,
                "agent": agent.agent,
                "status": status,
                "cpu": cpu,
                "memory": memory,
                "uptime": format_duration(uptime.total_seconds()),
                "created": created.strftime("%Y-%m-%d %H:%M"),
            }
        )

    # Sort by batch_id if grouped, otherwise by created time
    if grouped:
        agent_data.sort(key=lambda x: (x["batch_id"], x["branch"]))
    else:
        agent_data.sort(key=lambda x: x["created"])

    # Display header
    click.echo(
        "\n{:<25} {:<15} {:<8} {:<8} {:<8} {:<8} {:<16}".format(
            "BRANCH", "BATCH", "AGENT", "STATUS", "CPU%", "MEM(MB)", "UPTIME"
        )
    )
    click.echo("-" * 100)

    # Display agents
    current_batch = None
    for data in agent_data:
        # Add batch separator if grouped
        if grouped and data["batch_id"] != current_batch:
            if current_batch is not None:
                click.echo()
            current_batch = data["batch_id"]

        # Format row with status color coding
        status_colors = {
            "ready": "green",
            "running": "yellow",
            "idle": "blue",
            "dead": "red",
            "unknown": "white",
        }
        status_color = status_colors.get(str(data["status"]), "white")
        status_text = click.style(str(data["status"]), fg=status_color)

        click.echo(
            "{:<25} {:<15} {:<8} {} {:<8.1f} {:<8.0f} {:<16}".format(
                str(data["branch"])[:25],
                str(data["batch_id"])[:15],
                str(data["agent"]),
                status_text,
                float(data["cpu"]),
                float(data["memory"]),
                str(data["uptime"]),
            )
        )

    # Summary
    click.echo("\n" + "-" * 100)
    # Count by status
    status_counts: Dict[str, int] = {}
    for d in agent_data:
        status = str(d["status"])
        status_counts[status] = status_counts.get(status, 0) + 1

    active_count = sum(
        count for status, count in status_counts.items() if status != "dead"
    )
    total_cpu = sum(float(d["cpu"]) for d in agent_data)
    total_memory = sum(float(d["memory"]) for d in agent_data)

    click.echo(f"Total: {len(agent_data)} agents ({active_count} active)")
    click.echo(f"Resources: {total_cpu:.1f}% CPU, {total_memory:.0f} MB RAM")

    # Show status breakdown
    if status_counts:
        status_parts = []
        for status in ["ready", "running", "idle", "dead", "unknown"]:
            if status in status_counts:
                count = status_counts[status]
                status_colors = {
                    "ready": "green",
                    "running": "yellow",
                    "idle": "blue",
                    "dead": "red",
                    "unknown": "white",
                }
                color = status_colors.get(status, "white")
                status_parts.append(click.style(f"{status}: {count}", fg=color))
        click.echo("Status: " + ", ".join(status_parts))

    if grouped:
        batch_counts: Dict[str, int] = {}
        for data in agent_data:
            batch_id = str(data["batch_id"])
            batch_counts[batch_id] = batch_counts.get(batch_id, 0) + 1
        batches_summary = ", ".join(f"{b}: {c}" for b, c in batch_counts.items())
        click.echo(f"Batches: {len(batch_counts)} ({batches_summary})")


@click.command()
@click.option("--grouped", "-g", is_flag=True, help="Group by batch ID")
@click.option(
    "--all", "-a", is_flag=True, help="Show all agents (including dead sessions)"
)
@click.option("--watch", "-w", is_flag=True, help="Watch mode - refresh every second")
def list(grouped: bool, all: bool, watch: bool):
    """List all active AI agents."""
    config = ensure_project_config()
    state = StateManager(config.repo_root)
    tmux_mgr = TmuxManager(config.tmux_prefix)

    if watch:
        # Run in watch mode
        try:
            while True:
                # Clear screen
                print("\033[H\033[2J", end="")

                # Display agents
                display_agents(config, state, tmux_mgr, grouped, all)

                # Add timestamp
                print(f"\nLast updated: {datetime.now().strftime('%H:%M:%S')}")
                print("Press Ctrl+C to exit watch mode")

                time.sleep(1)
        except KeyboardInterrupt:
            print("\nExiting watch mode")
            sys.exit(0)
    else:
        # Display once
        display_agents(config, state, tmux_mgr, grouped, all)
