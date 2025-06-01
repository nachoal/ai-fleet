"""Tests for list command."""

from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import click.testing
import pytest

from aifleet.commands.list import display_agents, list
from aifleet.config import ConfigManager
from aifleet.state import Agent, StateManager
from aifleet.tmux import TmuxManager


class TestListCommand:
    """Tests for list command."""

    @pytest.fixture
    def sample_agents(self):
        """Create sample agents for testing."""
        now = datetime.now()
        return [
            Agent(
                branch="feature-1",
                session="ai_feature-1",
                agent="claude",
                batch_id="batch1",
                created_at=(now - timedelta(hours=2)).isoformat(),
                worktree="/path/to/worktree1",
                pid=1234,
                prompt="Fix the bug",
            ),
            Agent(
                branch="feature-2",
                session="ai_feature-2",
                agent="claude",
                batch_id="batch1",
                created_at=(now - timedelta(hours=1)).isoformat(),
                worktree="/path/to/worktree2",
                pid=5678,
                prompt="Add new feature",
            ),
        ]

    def test_display_agents_with_new_statuses(self, sample_agents, capsys):
        """Test display_agents shows new status types with colors."""
        # Mock dependencies
        config = MagicMock(spec=ConfigManager)
        config.repo_root = "/test/repo"
        config.tmux_prefix = "ai_"
        state = MagicMock(spec=StateManager)
        state.list_agents.return_value = sample_agents
        state.reconcile_with_tmux.return_value = []

        tmux_mgr = MagicMock(spec=TmuxManager)
        tmux_mgr.list_sessions.return_value = [
            ("ai_feature-1", 1234),
            ("ai_feature-2", 5678),
        ]

        # Mock status detection
        def mock_get_agent_status(branch):
            if branch == "feature-1":
                return "ready"
            elif branch == "feature-2":
                return "running"
            return "unknown"

        tmux_mgr.get_agent_status.side_effect = mock_get_agent_status

        # Mock process stats
        with patch("aifleet.commands.list.get_process_stats") as mock_stats:
            mock_stats.return_value = (25.5, 1024.0)  # CPU%, Memory MB

            # Display agents
            display_agents(config, state, tmux_mgr, grouped=False, all=False)

        # Check output
        captured = capsys.readouterr()
        output = captured.out

        # Check headers
        assert "BRANCH" in output
        assert "STATUS" in output

        # Check that status values are displayed
        assert "ready" in output
        assert "running" in output

        # Check summary includes status breakdown
        assert "Status:" in output
        assert "ready: 1" in output
        assert "running: 1" in output

    def test_display_agents_grouped(self, sample_agents, capsys):
        """Test display_agents with grouping by batch."""
        # Mock dependencies
        config = MagicMock(spec=ConfigManager)
        config.repo_root = "/test/repo"
        config.tmux_prefix = "ai_"
        state = MagicMock(spec=StateManager)
        state.list_agents.return_value = sample_agents
        state.reconcile_with_tmux.return_value = []

        tmux_mgr = MagicMock(spec=TmuxManager)
        tmux_mgr.list_sessions.return_value = [
            ("ai_feature-1", 1234),
            ("ai_feature-2", 5678),
        ]
        tmux_mgr.get_agent_status.return_value = "ready"

        with patch("aifleet.commands.list.get_process_stats", return_value=(0, 0)):
            display_agents(config, state, tmux_mgr, grouped=True, all=False)

        captured = capsys.readouterr()
        output = captured.out

        # Check batches are shown
        assert "batch1" in output
        assert "Batches: 1" in output

    def test_list_command_normal_mode(self):
        """Test list command in normal mode."""
        runner = click.testing.CliRunner()

        with (
            patch("aifleet.commands.list.ensure_project_config") as mock_config,
            patch("aifleet.commands.list.StateManager"),
            patch("aifleet.commands.list.TmuxManager"),
            patch("aifleet.commands.list.display_agents") as mock_display,
        ):
            # Setup mocks
            config = MagicMock(spec=ConfigManager)
            config.repo_root = "/test/repo"
            config.tmux_prefix = "ai_"
            mock_config.return_value = config

            # Run command
            result = runner.invoke(list, [])

            # Check it ran successfully
            assert result.exit_code == 0

            # Check display_agents was called once
            mock_display.assert_called_once()

    def test_list_command_watch_mode(self):
        """Test list command in watch mode."""
        runner = click.testing.CliRunner()

        with (
            patch("aifleet.commands.list.ensure_project_config") as mock_config,
            patch("aifleet.commands.list.StateManager"),
            patch("aifleet.commands.list.TmuxManager"),
            patch("aifleet.commands.list.display_agents") as mock_display,
            patch("time.sleep") as mock_sleep,
        ):
            # Setup mocks
            config = MagicMock(spec=ConfigManager)
            config.repo_root = "/test/repo"
            config.tmux_prefix = "ai_"
            mock_config.return_value = config

            # Simulate KeyboardInterrupt after 2 iterations
            mock_sleep.side_effect = [None, KeyboardInterrupt]

            # Run command with --watch
            result = runner.invoke(list, ["--watch"])

            # Check it exited with code 0 (handled KeyboardInterrupt)
            assert result.exit_code == 0

            # Check display_agents was called multiple times
            assert mock_display.call_count == 2

            # Check output mentions exiting watch mode
            assert "Exiting watch mode" in result.output

    def test_list_command_all_statuses(self, sample_agents):
        """Test that all status types are handled correctly."""
        statuses = ["ready", "running", "idle", "dead", "unknown"]

        config = MagicMock(spec=ConfigManager)
        config.repo_root = "/test/repo"
        config.tmux_prefix = "ai_"
        state = MagicMock(spec=StateManager)
        tmux_mgr = MagicMock(spec=TmuxManager)

        # Create one agent for each status
        agents = []
        for i, status in enumerate(statuses):
            agent = Agent(
                branch=f"feature-{status}",
                session=f"ai_feature-{status}",
                agent="claude",
                batch_id="batch1",
                created_at=datetime.now().isoformat(),
                worktree=f"/path/to/worktree{i}",
                pid=1000 + i,
            )
            agents.append(agent)

        state.list_agents.return_value = agents
        state.reconcile_with_tmux.return_value = []
        tmux_mgr.list_sessions.return_value = [
            (a.session, a.pid) for a in agents if a.branch != "feature-dead"
        ]

        # Mock status detection to return each status type
        def mock_get_status(branch):
            for status in statuses:
                if f"feature-{status}" in branch:
                    return status
            return "unknown"

        tmux_mgr.get_agent_status.side_effect = mock_get_status

        with patch("aifleet.commands.list.get_process_stats", return_value=(0, 0)):
            with patch("click.echo") as mock_echo:
                display_agents(config, state, tmux_mgr, grouped=False, all=False)

                # Verify all statuses appear in output
                output = " ".join(str(call) for call in mock_echo.call_args_list)
                for status in statuses:
                    assert status in output
