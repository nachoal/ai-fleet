"""Tests for the attach command."""

from datetime import datetime
from unittest.mock import patch

from click.testing import CliRunner

from aifleet.commands.attach import attach
from aifleet.state import Agent


class TestAttachCommand:
    """Test the attach command."""

    def test_attach_success(self, temp_dir):
        """Test attaching to existing agent session."""
        with patch(
            "aifleet.commands.base.ensure_project_config"
        ) as mock_ensure_config_base:
            with patch(
                "aifleet.commands.attach.ensure_project_config"
            ) as mock_ensure_config_attach:
                with patch("aifleet.commands.attach.StateManager") as mock_state:
                    with patch("aifleet.commands.attach.TmuxManager") as mock_tmux:
                        # Setup mocks - patch both base and attach module
                        mock_config = mock_ensure_config_base.return_value
                        mock_ensure_config_attach.return_value = mock_config
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

                        # Run command
                        runner = CliRunner()
                        result = runner.invoke(attach, ["test-branch"])
                        if result.exit_code != 0:
                            print(f"Command failed with output: {result.output}")
                            print(f"Exception: {result.exception}")
                        assert result.exit_code == 0

                        # Verify calls
                        mock_state.return_value.get_agent.assert_called_once_with(
                            "test-branch"
                        )
                        mock_tmux.return_value.session_exists.assert_called_once_with(
                            "test-branch"
                        )
                        mock_tmux.return_value.attach_session.assert_called_once_with(
                            "test-branch"
                        )

    def test_attach_agent_not_found(self, temp_dir):
        """Test attach when agent doesn't exist."""
        with patch(
            "aifleet.commands.base.ensure_project_config"
        ) as mock_ensure_config_base:
            with patch(
                "aifleet.commands.attach.ensure_project_config"
            ) as mock_ensure_config_attach:
                with patch("aifleet.commands.attach.StateManager") as mock_state:
                    with patch("aifleet.commands.attach.TmuxManager") as _:
                        # Setup mocks - patch both base and attach module
                        mock_config = mock_ensure_config_base.return_value
                        mock_ensure_config_attach.return_value = mock_config
                        mock_config.repo_root = temp_dir
                        mock_config.project_root = temp_dir
                        mock_state.return_value.get_agent.return_value = None

                        # Run command and expect exit
                        runner = CliRunner()
                        result = runner.invoke(attach, ["nonexistent"])
                        assert result.exit_code == 1
                        mock_state.return_value.get_agent.assert_called_once_with(
                            "nonexistent"
                        )

    def test_attach_session_not_found(self, temp_dir):
        """Test attach when tmux session doesn't exist."""
        with patch(
            "aifleet.commands.base.ensure_project_config"
        ) as mock_ensure_config_base:
            with patch(
                "aifleet.commands.attach.ensure_project_config"
            ) as mock_ensure_config_attach:
                with patch("aifleet.commands.attach.StateManager") as mock_state:
                    with patch("aifleet.commands.attach.TmuxManager") as mock_tmux:
                        # Setup mocks - patch both base and attach module
                        mock_config = mock_ensure_config_base.return_value
                        mock_ensure_config_attach.return_value = mock_config
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
                        result = runner.invoke(attach, ["test-branch"])
                        assert result.exit_code == 1
                        # Should clean up state
                        mock_state.return_value.remove_agent.assert_called_once_with(
                            "test-branch"
                        )
