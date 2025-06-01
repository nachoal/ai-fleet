"""Tests for state management."""

from datetime import datetime

from aifleet.state import Agent, StateManager


class TestAgent:
    """Test Agent dataclass."""

    def test_agent_creation(self):
        """Test creating an agent."""
        agent = Agent(
            branch="test-branch",
            worktree="/path/to/worktree",
            session="ai_test-branch",
            pid=12345,
            batch_id="test-batch",
            agent="claude",
            created_at=datetime.now().isoformat(),
            prompt="Test prompt",
        )

        assert agent.branch == "test-branch"
        assert agent.pid == 12345
        assert agent.prompt == "Test prompt"

    def test_agent_to_dict(self):
        """Test converting agent to dict."""
        agent = Agent(
            branch="test-branch",
            worktree="/path/to/worktree",
            session="ai_test-branch",
            pid=None,  # Should be excluded
            batch_id="test-batch",
            agent="claude",
            created_at=datetime.now().isoformat(),
        )

        data = agent.to_dict()
        assert "branch" in data
        assert "pid" not in data  # None values excluded

    def test_agent_from_dict(self):
        """Test creating agent from dict."""
        data = {
            "branch": "test-branch",
            "worktree": "/path/to/worktree",
            "session": "ai_test-branch",
            "pid": None,
            "batch_id": "test-batch",
            "agent": "claude",
            "created_at": datetime.now().isoformat(),
        }

        agent = Agent.from_dict(data)
        assert agent.branch == "test-branch"
        assert agent.pid is None

    def test_agent_from_dict_missing_pid(self):
        """Test creating agent from dict without pid field (as saved by to_dict)."""
        # This simulates what happens when to_dict() filters out None values
        data = {
            "branch": "test-branch",
            "worktree": "/path/to/worktree",
            "session": "ai_test-branch",
            # pid is intentionally missing
            "batch_id": "test-batch",
            "agent": "claude",
            "created_at": datetime.now().isoformat(),
        }

        agent = Agent.from_dict(data)
        assert agent.branch == "test-branch"
        assert agent.pid is None  # Should default to None

    def test_agent_round_trip_serialization(self):
        """Test that to_dict -> from_dict preserves the agent correctly."""
        # Create agent with None pid
        original = Agent(
            branch="test-branch",
            worktree="/path/to/worktree",
            session="ai_test-branch",
            pid=None,  # This will be filtered out by to_dict
            batch_id="test-batch",
            agent="claude",
            created_at=datetime.now().isoformat(),
            prompt="Test prompt",
        )

        # Convert to dict and back
        data = original.to_dict()
        restored = Agent.from_dict(data)

        # Verify all fields are preserved
        assert restored.branch == original.branch
        assert restored.worktree == original.worktree
        assert restored.session == original.session
        assert restored.pid == original.pid
        assert restored.batch_id == original.batch_id
        assert restored.agent == original.agent
        assert restored.created_at == original.created_at
        assert restored.prompt == original.prompt


class TestStateManager:
    """Test StateManager functionality."""

    def test_add_agent(self, temp_dir):
        """Test adding an agent."""
        # Create project structure
        project_dir = temp_dir / "test-project"
        project_dir.mkdir()
        state = StateManager(project_dir)

        agent = Agent(
            branch="test-branch",
            worktree="/path/to/worktree",
            session="ai_test-branch",
            pid=12345,
            batch_id="test-batch",
            agent="claude",
            created_at=datetime.now().isoformat(),
        )

        state.add_agent(agent)

        # Verify agent was added
        agents = state.list_agents()
        assert len(agents) == 1
        assert agents[0].branch == "test-branch"

    def test_remove_agent(self, temp_dir):
        """Test removing an agent."""
        # Create project structure
        project_dir = temp_dir / "test-project"
        project_dir.mkdir()
        state = StateManager(project_dir)

        # Add agent
        agent = Agent(
            branch="test-branch",
            worktree="/path/to/worktree",
            session="ai_test-branch",
            pid=12345,
            batch_id="test-batch",
            agent="claude",
            created_at=datetime.now().isoformat(),
        )
        state.add_agent(agent)

        # Remove agent
        removed = state.remove_agent("test-branch")
        assert removed is True

        # Verify removed
        agents = state.list_agents()
        assert len(agents) == 0

        # Try removing non-existent
        removed = state.remove_agent("nonexistent")
        assert removed is False

    def test_get_agent(self, temp_dir):
        """Test getting a specific agent."""
        # Create project structure
        project_dir = temp_dir / "test-project"
        project_dir.mkdir()
        state = StateManager(project_dir)

        # Add agents
        agent1 = Agent(
            branch="branch1",
            worktree="/path1",
            session="ai_branch1",
            pid=12345,
            batch_id="batch1",
            agent="claude",
            created_at=datetime.now().isoformat(),
        )
        agent2 = Agent(
            branch="branch2",
            worktree="/path2",
            session="ai_branch2",
            pid=12346,
            batch_id="batch1",
            agent="claude",
            created_at=datetime.now().isoformat(),
        )

        state.add_agent(agent1)
        state.add_agent(agent2)

        # Get specific agent
        found = state.get_agent("branch1")
        assert found is not None
        assert found.branch == "branch1"
        assert found.pid == 12345

        # Get non-existent
        found = state.get_agent("nonexistent")
        assert found is None

    def test_list_agents_by_batch(self, temp_dir):
        """Test listing agents filtered by batch."""
        # Create project structure
        project_dir = temp_dir / "test-project"
        project_dir.mkdir()
        state = StateManager(project_dir)

        # Add agents in different batches
        for i in range(3):
            agent = Agent(
                branch=f"branch{i}",
                worktree=f"/path{i}",
                session=f"ai_branch{i}",
                pid=12345 + i,
                batch_id="batch1" if i < 2 else "batch2",
                agent="claude",
                created_at=datetime.now().isoformat(),
            )
            state.add_agent(agent)

        # List all
        all_agents = state.list_agents()
        assert len(all_agents) == 3

        # List by batch
        batch1_agents = state.list_agents(batch_id="batch1")
        assert len(batch1_agents) == 2

        batch2_agents = state.list_agents(batch_id="batch2")
        assert len(batch2_agents) == 1

    def test_update_agent_pid(self, temp_dir):
        """Test updating agent PID."""
        # Create project structure
        project_dir = temp_dir / "test-project"
        project_dir.mkdir()
        state = StateManager(project_dir)

        # Add agent without PID
        agent = Agent(
            branch="test-branch",
            worktree="/path",
            session="ai_test-branch",
            pid=None,
            batch_id="batch",
            agent="claude",
            created_at=datetime.now().isoformat(),
        )
        state.add_agent(agent)

        # Update PID
        updated = state.update_agent_pid("test-branch", 99999)
        assert updated is True

        # Verify update
        found = state.get_agent("test-branch")
        assert found.pid == 99999

        # Update non-existent
        updated = state.update_agent_pid("nonexistent", 11111)
        assert updated is False

    def test_get_batches(self, temp_dir):
        """Test getting unique batch IDs."""
        # Create project structure
        project_dir = temp_dir / "test-project"
        project_dir.mkdir()
        state = StateManager(project_dir)

        # Add agents with different batches
        batches = ["batch1", "batch2", "batch1", "batch3"]
        for i, batch_id in enumerate(batches):
            agent = Agent(
                branch=f"branch{i}",
                worktree=f"/path{i}",
                session=f"ai_branch{i}",
                pid=12345 + i,
                batch_id=batch_id,
                agent="claude",
                created_at=datetime.now().isoformat(),
            )
            state.add_agent(agent)

        # Get unique batches
        unique_batches = state.get_batches()
        assert len(unique_batches) == 3
        assert unique_batches == ["batch1", "batch2", "batch3"]

    def test_remove_batch(self, temp_dir):
        """Test removing all agents in a batch."""
        # Create project structure
        project_dir = temp_dir / "test-project"
        project_dir.mkdir()
        state = StateManager(project_dir)

        # Add agents in batches
        for i in range(5):
            agent = Agent(
                branch=f"branch{i}",
                worktree=f"/path{i}",
                session=f"ai_branch{i}",
                pid=12345 + i,
                batch_id="batch1" if i < 3 else "batch2",
                agent="claude",
                created_at=datetime.now().isoformat(),
            )
            state.add_agent(agent)

        # Remove batch1
        removed_count = state.remove_batch("batch1")
        assert removed_count == 3

        # Verify only batch2 remains
        remaining = state.list_agents()
        assert len(remaining) == 2
        assert all(a.batch_id == "batch2" for a in remaining)

    def test_reconcile_with_tmux(self, temp_dir):
        """Test reconciling state with tmux sessions."""
        # Create project structure
        project_dir = temp_dir / "test-project"
        project_dir.mkdir()
        state = StateManager(project_dir)

        # Add agents
        for i in range(3):
            agent = Agent(
                branch=f"branch{i}",
                worktree=f"/path{i}",
                session=f"ai_branch{i}",
                pid=12345 + i,
                batch_id="batch",
                agent="claude",
                created_at=datetime.now().isoformat(),
            )
            state.add_agent(agent)

        # Simulate only some sessions being active
        active_sessions = ["ai_branch0", "ai_branch2"]

        # Reconcile
        removed = state.reconcile_with_tmux(active_sessions)
        assert len(removed) == 1
        assert "branch1" in removed

        # Verify state
        remaining = state.list_agents()
        assert len(remaining) == 2
        assert all(a.branch in ["branch0", "branch2"] for a in remaining)
