"""List command for AI Fleet."""

import sys
import time
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Union

import click
import psutil
from rich.console import Console
from rich.live import Live
from rich.table import Table
from rich.text import Text

from ..config import ConfigManager
from ..state import StateManager
from ..tmux import TmuxManager
from ..utils import format_duration
from .base import ensure_project_config

console = Console()


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


def create_agents_table(
    config: ConfigManager,
    state: StateManager,
    tmux_mgr: TmuxManager,
    grouped: bool,
    all: bool,
) -> Table:
    """Create a Rich table with agent data."""

    # Get active tmux sessions
    active_sessions = [name for name, _ in tmux_mgr.list_sessions()]

    # Reconcile state with tmux
    if not all:
        removed = state.reconcile_with_tmux(active_sessions)
        if removed:
            msg = f"[dim]Cleaned up {len(removed)} dead agents from state[/dim]"
            console.print(msg)

    # Get all agents
    agents = state.list_agents()

    if not agents:
        table = Table(title="No active agents", show_header=False)
        return table

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

    # Create table
    table = Table(
        title="AI Fleet Agents",
        caption=f"Last updated: {datetime.now().strftime('%H:%M:%S')}",
        show_lines=grouped,
    )

    # Add columns
    table.add_column("BRANCH", style="cyan", overflow="fold")
    table.add_column("BATCH", style="magenta")
    table.add_column("AGENT", style="white")
    table.add_column("STATUS", justify="center")
    table.add_column("CPU%", justify="right", style="yellow")
    table.add_column("MEM(MB)", justify="right", style="green")
    table.add_column("UPTIME", style="dim")

    # Add rows
    current_batch = None
    for data in agent_data:
        # Add batch separator if grouped
        if grouped and data["batch_id"] != current_batch:
            if current_batch is not None:
                table.add_section()
            current_batch = data["batch_id"]

        # Format status with color
        status_colors = {
            "ready": "green",
            "running": "yellow",
            "idle": "blue",
            "dead": "red",
            "unknown": "white",
        }
        status_color = status_colors.get(str(data["status"]), "white")
        status_text = Text(str(data["status"]), style=status_color)

        table.add_row(
            str(data["branch"])[:25],
            str(data["batch_id"])[:15],
            str(data["agent"]),
            status_text,
            f"{float(data['cpu']):.1f}",
            f"{float(data['memory']):.0f}",
            str(data["uptime"]),
        )

    # Add summary panel
    status_counts: Dict[str, int] = {}
    for d in agent_data:
        status = str(d["status"])
        status_counts[status] = status_counts.get(status, 0) + 1

    active_count = sum(
        count for status, count in status_counts.items() if status != "dead"
    )
    total_cpu = sum(float(d["cpu"]) for d in agent_data)
    total_memory = sum(float(d["memory"]) for d in agent_data)

    # Create summary text
    summary_lines = [
        f"Total: {len(agent_data)} agents ({active_count} active)",
        f"Resources: {total_cpu:.1f}% CPU, {total_memory:.0f} MB RAM",
    ]

    # Add status breakdown
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
                status_parts.append(f"[{color}]{status}: {count}[/{color}]")
        summary_lines.append("Status: " + ", ".join(status_parts))

    if grouped:
        batch_counts: Dict[str, int] = {}
        for data in agent_data:
            batch_id = str(data["batch_id"])
            batch_counts[batch_id] = batch_counts.get(batch_id, 0) + 1
        batches_summary = ", ".join(f"{b}: {c}" for b, c in batch_counts.items())
        summary_lines.append(f"Batches: {len(batch_counts)} ({batches_summary})")

    # Add summary as a footer
    table.caption_justify = "left"
    table.caption = "\n".join(summary_lines)

    return table


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
        # Run in watch mode with Live display
        console.print("[dim]Press Ctrl+C to exit watch mode[/dim]")
        try:
            with Live(
                create_agents_table(config, state, tmux_mgr, grouped, all),
                refresh_per_second=1,
                screen=True,
                console=console,
            ) as live:
                while True:
                    time.sleep(1)
                    table = create_agents_table(config, state, tmux_mgr, grouped, all)
                    live.update(table)
        except KeyboardInterrupt:
            console.print("\n[dim]Exiting watch mode[/dim]")
            sys.exit(0)
    else:
        # Display once
        table = create_agents_table(config, state, tmux_mgr, grouped, all)
        console.print(table)
