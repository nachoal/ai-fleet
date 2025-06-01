"""Tests for the prompt command."""

from datetime import datetime
from unittest.mock import patch

from click.testing import CliRunner

from aifleet.commands.prompt import prompt
from aifleet.state import Agent


class TestPromptCommand:
    """Test the prompt command."""

    def test_prompt_success(self, temp_dir):
        """Test sending prompt to existing agent."""
        # Patch at the source where it's defined, not where it's imported
        with patch(
            "aifleet.commands.base.ensure_project_config"
        ) as mock_ensure_config_base:
            with patch(
                "aifleet.commands.prompt.ensure_project_config"
            ) as mock_ensure_config_prompt:
                with patch("aifleet.commands.prompt.StateManager") as mock_state:
                    with patch("aifleet.commands.prompt.TmuxManager") as mock_tmux:
                        # Setup mocks - patch both base and prompt module
                        mock_config = mock_ensure_config_base.return_value
                        mock_ensure_config_prompt.return_value = mock_config
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
                        mock_tmux.return_value.send_command.return_value = True

                        # Run command
                        runner = CliRunner()
                        result = runner.invoke(
                            prompt, ["test-branch", "New prompt message"]
                        )
                        assert result.exit_code == 0

                        # Verify calls
                    mock_state.return_value.get_agent.assert_called_once_with(
                        "test-branch"
                    )
                    mock_tmux.return_value.session_exists.assert_called_once_with(
                        "test-branch"
                    )
                    mock_tmux.return_value.send_command.assert_called_once_with(
                        "test-branch", "New prompt message"
                    )

    def test_prompt_agent_not_found(self, temp_dir):
        """Test prompt when agent doesn't exist."""
        with patch(
            "aifleet.commands.base.ensure_project_config"
        ) as mock_ensure_config_base:
            with patch(
                "aifleet.commands.prompt.ensure_project_config"
            ) as mock_ensure_config_prompt:
                with patch("aifleet.commands.prompt.StateManager") as mock_state:
                    with patch("aifleet.commands.prompt.TmuxManager") as _:
                        # Setup mocks - patch both base and prompt module
                        mock_config = mock_ensure_config_base.return_value
                        mock_ensure_config_prompt.return_value = mock_config
                        mock_config.repo_root = temp_dir
                        mock_config.project_root = temp_dir
                        mock_state.return_value.get_agent.return_value = None

                        # Run command and expect exit
                        runner = CliRunner()
                        result = runner.invoke(prompt, ["nonexistent", "Message"])
                        assert result.exit_code == 1
                        mock_state.return_value.get_agent.assert_called_once_with(
                            "nonexistent"
                        )

    def test_prompt_session_not_found(self, temp_dir):
        """Test prompt when tmux session doesn't exist."""
        with patch(
            "aifleet.commands.base.ensure_project_config"
        ) as mock_ensure_config_base:
            with patch(
                "aifleet.commands.prompt.ensure_project_config"
            ) as mock_ensure_config_prompt:
                with patch("aifleet.commands.prompt.StateManager") as mock_state:
                    with patch("aifleet.commands.prompt.TmuxManager") as mock_tmux:
                        # Setup mocks - patch both base and prompt module
                        mock_config = mock_ensure_config_base.return_value
                        mock_ensure_config_prompt.return_value = mock_config
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
                    result = runner.invoke(prompt, ["test-branch", "Message"])
                    assert result.exit_code == 1
                    # Should clean up state
                    mock_state.return_value.remove_agent.assert_called_once_with(
                        "test-branch"
                    )

    def test_prompt_send_failed(self, temp_dir):
        """Test prompt when send command fails."""
        with patch(
            "aifleet.commands.base.ensure_project_config"
        ) as mock_ensure_config_base:
            with patch(
                "aifleet.commands.prompt.ensure_project_config"
            ) as mock_ensure_config_prompt:
                with patch("aifleet.commands.prompt.StateManager") as mock_state:
                    with patch("aifleet.commands.prompt.TmuxManager") as mock_tmux:
                        # Setup mocks - patch both base and prompt module
                        mock_config = mock_ensure_config_base.return_value
                        mock_ensure_config_prompt.return_value = mock_config
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
                    # Send fails
                    mock_tmux.return_value.send_command.return_value = False

                    # Run command and expect exit
                    runner = CliRunner()
                    result = runner.invoke(prompt, ["test-branch", "Message"])
                    assert result.exit_code == 1
