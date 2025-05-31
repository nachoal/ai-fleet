"""List command for AI Fleet."""

import psutil
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Union
import click

from ..config import ConfigManager
from ..state import StateManager
from ..tmux import TmuxManager
from ..utils import format_duration


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


@click.command()
@click.option("--grouped", "-g", is_flag=True, help="Group by batch ID")
@click.option("--all", "-a", is_flag=True, help="Show all agents (including dead sessions)")
def list(grouped: bool, all: bool):
    """List all active AI agents."""
    config = ConfigManager()
    state = StateManager()
    tmux_mgr = TmuxManager(config.tmux_prefix)
    
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
        # Check if session is active
        session_active = agent.session in active_sessions
        
        # Get process stats
        cpu, memory = get_process_stats(agent.pid)
        
        # Calculate uptime
        created = datetime.fromisoformat(agent.created_at)
        uptime = datetime.now() - created
        
        agent_data.append({
            "branch": agent.branch,
            "batch_id": agent.batch_id,
            "agent": agent.agent,
            "status": "active" if session_active else "dead",
            "cpu": cpu,
            "memory": memory,
            "uptime": format_duration(uptime.total_seconds()),
            "created": created.strftime("%Y-%m-%d %H:%M"),
        })
    
    # Sort by batch_id if grouped, otherwise by created time
    if grouped:
        agent_data.sort(key=lambda x: (x["batch_id"], x["branch"]))
    else:
        agent_data.sort(key=lambda x: x["created"])
    
    # Display header
    click.echo("\n{:<25} {:<15} {:<8} {:<8} {:<8} {:<8} {:<16}".format(
        "BRANCH", "BATCH", "AGENT", "STATUS", "CPU%", "MEM(MB)", "UPTIME"
    ))
    click.echo("-" * 100)
    
    # Display agents
    current_batch = None
    for data in agent_data:
        # Add batch separator if grouped
        if grouped and data["batch_id"] != current_batch:
            if current_batch is not None:
                click.echo()
            current_batch = data["batch_id"]
        
        # Format row
        status_color = "green" if data["status"] == "active" else "red"
        status_text = click.style(str(data["status"]), fg=status_color)
        
        click.echo("{:<25} {:<15} {:<8} {} {:<8.1f} {:<8.0f} {:<16}".format(
            str(data["branch"])[:25],
            str(data["batch_id"])[:15],
            str(data["agent"]),
            status_text,
            float(data["cpu"]),
            float(data["memory"]),
            str(data["uptime"])
        ))
    
    # Summary
    click.echo("\n" + "-" * 100)
    active_count = sum(1 for d in agent_data if d["status"] == "active")
    total_cpu = sum(float(d["cpu"]) for d in agent_data)
    total_memory = sum(float(d["memory"]) for d in agent_data)
    
    click.echo(f"Total: {len(agent_data)} agents ({active_count} active)")
    click.echo(f"Resources: {total_cpu:.1f}% CPU, {total_memory:.0f} MB RAM")
    
    if grouped:
        batch_counts: Dict[str, int] = {}
        for data in agent_data:
            batch_id = str(data["batch_id"])
            batch_counts[batch_id] = batch_counts.get(batch_id, 0) + 1
        click.echo(f"Batches: {len(batch_counts)} ({', '.join(f'{b}: {c}' for b, c in batch_counts.items())})")