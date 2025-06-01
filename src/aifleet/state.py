"""State management for AI Fleet agents."""

import fcntl
import json
import os
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class Agent:
    """Represents an AI agent."""

    branch: str
    worktree: str
    session: str
    batch_id: str
    agent: str
    created_at: str
    pid: Optional[int] = None
    prompt: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {k: v for k, v in asdict(self).items() if v is not None}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Agent":
        """Create from dictionary."""
        return cls(**data)


class StateManager:
    """Manages AI Fleet agent state."""

    def __init__(self, project_root: Optional[Path] = None):
        """Initialize state manager.

        Args:
            project_root: Project root directory
                (will store state in .aifleet/state.json)
        """
        if project_root:
            # Project-based state (new behavior)
            self.state_dir = project_root / ".aifleet"
        else:
            # Legacy global state (for backward compatibility)
            self.state_dir = Path.home() / ".ai_fleet"
        self.state_file = self.state_dir / "state.json"
        self._ensure_state_dir()

    def _ensure_state_dir(self) -> None:
        """Ensure state directory exists."""
        self.state_dir.mkdir(parents=True, exist_ok=True)

    def _load_state(self) -> List[Dict[str, Any]]:
        """Load state from disk with file locking."""
        if not self.state_file.exists():
            return []

        try:
            with open(self.state_file, "r") as f:
                # Acquire shared lock for reading
                fcntl.flock(f.fileno(), fcntl.LOCK_SH)
                try:
                    data = json.load(f)
                    return data if isinstance(data, list) else []
                finally:
                    fcntl.flock(f.fileno(), fcntl.LOCK_UN)
        except Exception as e:
            print(f"Error loading state: {e}")
            return []

    def _save_state(self, agents: List[Dict[str, Any]]) -> None:
        """Save state to disk with file locking."""
        temp_file = self.state_file.with_suffix(".tmp")

        try:
            with open(temp_file, "w") as f:
                # Acquire exclusive lock for writing
                fcntl.flock(f.fileno(), fcntl.LOCK_EX)
                try:
                    json.dump(agents, f, indent=2)
                    f.flush()
                    os.fsync(f.fileno())
                finally:
                    fcntl.flock(f.fileno(), fcntl.LOCK_UN)

            # Atomic rename
            temp_file.rename(self.state_file)
        except Exception as e:
            print(f"Error saving state: {e}")
            if temp_file.exists():
                temp_file.unlink()
            raise

    def add_agent(self, agent: Agent) -> None:
        """Add an agent to state."""
        agents = self._load_state()

        # Remove any existing agent with same branch
        agents = [a for a in agents if a.get("branch") != agent.branch]

        # Add new agent
        agents.append(agent.to_dict())

        self._save_state(agents)

    def remove_agent(self, branch: str) -> bool:
        """Remove an agent from state.

        Args:
            branch: Branch name

        Returns:
            True if agent was removed, False if not found
        """
        agents = self._load_state()
        original_count = len(agents)

        agents = [a for a in agents if a.get("branch") != branch]

        if len(agents) < original_count:
            self._save_state(agents)
            return True
        return False

    def get_agent(self, branch: str) -> Optional[Agent]:
        """Get agent by branch name."""
        agents = self._load_state()

        for agent_data in agents:
            if agent_data.get("branch") == branch:
                return Agent.from_dict(agent_data)

        return None

    def list_agents(self, batch_id: Optional[str] = None) -> List[Agent]:
        """List all agents, optionally filtered by batch_id."""
        agents = self._load_state()

        if batch_id:
            agents = [a for a in agents if a.get("batch_id") == batch_id]

        return [Agent.from_dict(a) for a in agents]

    def update_agent_pid(self, branch: str, pid: int) -> bool:
        """Update agent PID.

        Args:
            branch: Branch name
            pid: Process ID

        Returns:
            True if updated, False if not found
        """
        agents = self._load_state()
        updated = False

        for agent in agents:
            if agent.get("branch") == branch:
                agent["pid"] = pid
                updated = True
                break

        if updated:
            self._save_state(agents)

        return updated

    def get_batches(self) -> List[str]:
        """Get list of unique batch IDs."""
        agents = self._load_state()
        batch_ids = set()

        for agent in agents:
            batch_id = agent.get("batch_id")
            if batch_id:
                batch_ids.add(batch_id)

        return sorted(batch_ids)

    def remove_batch(self, batch_id: str) -> int:
        """Remove all agents in a batch.

        Args:
            batch_id: Batch ID

        Returns:
            Number of agents removed
        """
        agents = self._load_state()
        original_count = len(agents)

        agents = [a for a in agents if a.get("batch_id") != batch_id]
        removed_count = original_count - len(agents)

        if removed_count > 0:
            self._save_state(agents)

        return removed_count

    def reconcile_with_tmux(self, active_sessions: List[str]) -> List[str]:
        """Reconcile state with actual tmux sessions.

        Args:
            active_sessions: List of active tmux session names

        Returns:
            List of branches that were removed from state
        """
        agents = self._load_state()
        removed_branches: List[str] = []

        # Filter out agents whose sessions no longer exist
        active_agents = []
        for agent in agents:
            if agent.get("session") in active_sessions:
                active_agents.append(agent)
            else:
                branch = agent.get("branch")
                if branch is not None:
                    removed_branches.append(branch)

        if removed_branches:
            self._save_state(active_agents)

        return removed_branches
