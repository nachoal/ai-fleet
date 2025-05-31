"""State management placeholder."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class Agent:
    """Placeholder Agent."""

    branch: str
    worktree: str
    session: str
    pid: Optional[int]
    batch_id: str
    agent: str
    created_at: str
    prompt: Optional[str] = None

    def to_dict(self):
        return {k: v for k, v in self.__dict__.items() if v is not None}

    @classmethod
    def from_dict(cls, data):
        return cls(**data)


class StateManager:
    """Placeholder StateManager."""

    def __init__(self, state_dir=None):
        self.state_dir = state_dir

    def list_agents(self, batch_id=None):
        return []

    def get_agent(self, branch):
        return None

    def add_agent(self, agent):
        pass

    def reconcile_with_tmux(self, active_sessions):
        return []
