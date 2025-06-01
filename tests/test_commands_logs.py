"""Tests for the logs command."""

from datetime import datetime
from unittest.mock import patch

from click.testing import CliRunner

from aifleet.commands.logs import logs
from aifleet.state import Agent


class TestLogsCommand:
    """Test the logs command."""

    def test_logs_success(self, temp_dir):
        """Test getting logs from existing agent."""
        with patch(
            "aifleet.commands.base.ensure_project_config"
        ) as mock_ensure_config_base:
            with patch(
                "aifleet.commands.logs.ensure_project_config"
            ) as mock_ensure_config_logs:
                with patch("aifleet.commands.logs.StateManager") as mock_state:
                    with patch("aifleet.commands.logs.TmuxManager") as mock_tmux:
                        # Setup mocks - patch both base and logs module
                        mock_config = mock_ensure_config_base.return_value
                        mock_ensure_config_logs.return_value = mock_config
                        mock_config.repo_root = temp_dir
                        mock_config.project_root = temp_dir
                        mock_config.tmux_prefix = "ai_"

                        # Mock agent
                        agent = Agent(
                            branch="test-branch",
                            worktree="/path/worktree",
                            session="ai_test-branch",
                            batch_id="batch1",
                            agent="claude",
                            created_at=datetime.now().isoformat(),
                            pid=12345,
                        )
                        mock_state.return_value.get_agent.return_value = agent

                        # Mock tmux operations
                        mock_tmux.return_value.session_exists.return_value = True
                        mock_tmux.return_value.get_session_output.return_value = (
                            "Log output here"
                        )

                        # Run command
                        runner = CliRunner()
                        result = runner.invoke(logs, ["test-branch", "--lines", "50"])
                        assert result.exit_code == 0

                        # Verify calls
                        mock_state.return_value.get_agent.assert_called_once_with(
                            "test-branch"
                        )
                        mock_tmux.return_value.session_exists.assert_called_once_with(
                            "test-branch"
                        )
                        mock_tmux.return_value.get_session_output.assert_called_once_with(
                            "test-branch", 50
                        )

    def test_logs_custom_lines(self, temp_dir):
        """Test getting logs with custom line count."""
        with patch(
            "aifleet.commands.base.ensure_project_config"
        ) as mock_ensure_config_base:
            with patch(
                "aifleet.commands.logs.ensure_project_config"
            ) as mock_ensure_config_logs:
                with patch("aifleet.commands.logs.StateManager") as mock_state:
                    with patch("aifleet.commands.logs.TmuxManager") as mock_tmux:
                        # Setup mocks - patch both base and logs module
                        mock_config = mock_ensure_config_base.return_value
                        mock_ensure_config_logs.return_value = mock_config
                        mock_config.repo_root = temp_dir
                        mock_config.project_root = temp_dir
                        mock_config.tmux_prefix = "ai_"

                        # Mock agent
                        agent = Agent(
                            branch="test-branch",
                            worktree="/path/worktree",
                            session="ai_test-branch",
                            batch_id="batch1",
                            agent="claude",
                            created_at=datetime.now().isoformat(),
                            pid=12345,
                        )
                        mock_state.return_value.get_agent.return_value = agent

                        # Mock tmux operations
                        mock_tmux.return_value.session_exists.return_value = True
                        mock_tmux.return_value.get_session_output.return_value = (
                            "Log output"
                        )

                        # Run command with custom lines
                        runner = CliRunner()
                        result = runner.invoke(logs, ["test-branch", "--lines", "100"])
                        assert result.exit_code == 0

                        # Verify calls
                        mock_tmux.return_value.get_session_output.assert_called_once_with(
                            "test-branch", 100
                        )

    def test_logs_agent_not_found(self, temp_dir):
        """Test logs when agent doesn't exist."""
        with patch(
            "aifleet.commands.base.ensure_project_config"
        ) as mock_ensure_config_base:
            with patch(
                "aifleet.commands.logs.ensure_project_config"
            ) as mock_ensure_config_logs:
                with patch("aifleet.commands.logs.StateManager") as mock_state:
                    with patch("aifleet.commands.logs.TmuxManager") as _:
                        # Setup mocks - patch both base and logs module
                        mock_config = mock_ensure_config_base.return_value
                        mock_ensure_config_logs.return_value = mock_config
                        mock_config.repo_root = temp_dir
                        mock_config.project_root = temp_dir
                        mock_state.return_value.get_agent.return_value = None

                        # Run command and expect exit
                        runner = CliRunner()
                        result = runner.invoke(logs, ["nonexistent", "--lines", "50"])
                        assert result.exit_code == 1
                        mock_state.return_value.get_agent.assert_called_once_with(
                            "nonexistent"
                        )

    def test_logs_session_not_found(self, temp_dir):
        """Test logs when tmux session doesn't exist."""
        with patch(
            "aifleet.commands.base.ensure_project_config"
        ) as mock_ensure_config_base:
            with patch(
                "aifleet.commands.logs.ensure_project_config"
            ) as mock_ensure_config_logs:
                with patch("aifleet.commands.logs.StateManager") as mock_state:
                    with patch("aifleet.commands.logs.TmuxManager") as mock_tmux:
                        # Setup mocks - patch both base and logs module
                        mock_config = mock_ensure_config_base.return_value
                        mock_ensure_config_logs.return_value = mock_config
                        mock_config.repo_root = temp_dir
                        mock_config.project_root = temp_dir
                        mock_config.tmux_prefix = "ai_"

                        # Mock agent
                        agent = Agent(
                            branch="test-branch",
                            worktree="/path/worktree",
                            session="ai_test-branch",
                            batch_id="batch1",
                            agent="claude",
                            created_at=datetime.now().isoformat(),
                            pid=12345,
                        )
                        mock_state.return_value.get_agent.return_value = agent

                        # Session doesn't exist
                        mock_tmux.return_value.session_exists.return_value = False

                        # Run command and expect exit
                        runner = CliRunner()
                        result = runner.invoke(logs, ["test-branch", "--lines", "50"])
                        assert result.exit_code == 1
                        # Should clean up state
                        mock_state.return_value.remove_agent.assert_called_once_with(
                            "test-branch"
                        )

    def test_logs_no_output(self, temp_dir):
        """Test logs when no output available."""
        with patch(
            "aifleet.commands.base.ensure_project_config"
        ) as mock_ensure_config_base:
            with patch(
                "aifleet.commands.logs.ensure_project_config"
            ) as mock_ensure_config_logs:
                with patch("aifleet.commands.logs.StateManager") as mock_state:
                    with patch("aifleet.commands.logs.TmuxManager") as mock_tmux:
                        # Setup mocks - patch both base and logs module
                        mock_config = mock_ensure_config_base.return_value
                        mock_ensure_config_logs.return_value = mock_config
                        mock_config.repo_root = temp_dir
                        mock_config.project_root = temp_dir
                        mock_config.tmux_prefix = "ai_"

                        # Mock agent
                        agent = Agent(
                            branch="test-branch",
                            worktree="/path/worktree",
                            session="ai_test-branch",
                            batch_id="batch1",
                            agent="claude",
                            created_at=datetime.now().isoformat(),
                            pid=12345,
                        )
                        mock_state.return_value.get_agent.return_value = agent

                        # Mock tmux operations
                        mock_tmux.return_value.session_exists.return_value = True
                        # No output
                        mock_tmux.return_value.get_session_output.return_value = None

                        # Run command
                        runner = CliRunner()
                        result = runner.invoke(logs, ["test-branch", "--lines", "50"])
                        assert result.exit_code == 0

                        # Should still succeed but with different message
                        mock_tmux.return_value.get_session_output.assert_called_once()
