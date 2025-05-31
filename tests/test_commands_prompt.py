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
        with patch("aifleet.commands.prompt.ConfigManager") as mock_config:
            with patch("aifleet.commands.prompt.StateManager") as mock_state:
                with patch("aifleet.commands.prompt.TmuxManager") as mock_tmux:
                    # Setup mocks
                    mock_config.return_value.repo_root = temp_dir
                    mock_config.return_value.tmux_prefix = "ai_"

                    # Mock agent
                    agent = Agent(
                        branch="test-branch",
                        worktree="/path/worktree",
                        session="ai_test-branch",
                        pid=12345,
                        batch_id="batch1",
                        agent="claude",
                        created_at=datetime.now().isoformat(),
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
                    mock_state.return_value.get_agent.assert_called_once_with("test-branch")
                    mock_tmux.return_value.session_exists.assert_called_once_with("ai_test-branch")
                    mock_tmux.return_value.send_command.assert_called_once_with(
                        "ai_test-branch", "New prompt message"
                    )

    def test_prompt_agent_not_found(self, temp_dir):
        """Test prompt when agent doesn't exist."""
        with patch("aifleet.commands.prompt.ConfigManager") as mock_config:
            with patch("aifleet.commands.prompt.StateManager") as mock_state:
                with patch("aifleet.commands.prompt.TmuxManager") as _:
                    # Setup mocks
                    mock_config.return_value.repo_root = temp_dir
                    mock_state.return_value.get_agent.return_value = None

                    # Run command and expect exit
                    runner = CliRunner()
                    result = runner.invoke(prompt, ["nonexistent", "Message"])
                    assert result.exit_code == 1
                    mock_state.return_value.get_agent.assert_called_once_with("nonexistent")

    def test_prompt_session_not_found(self, temp_dir):
        """Test prompt when tmux session doesn't exist."""
        with patch("aifleet.commands.prompt.ConfigManager") as mock_config:
            with patch("aifleet.commands.prompt.StateManager") as mock_state:
                with patch("aifleet.commands.prompt.TmuxManager") as mock_tmux:
                    # Setup mocks
                    mock_config.return_value.repo_root = temp_dir
                    mock_config.return_value.tmux_prefix = "ai_"

                    # Mock agent
                    agent = Agent(
                        branch="test-branch",
                        worktree="/path/worktree",
                        session="ai_test-branch",
                        pid=12345,
                        batch_id="batch1",
                        agent="claude",
                        created_at=datetime.now().isoformat(),
                    )
                    mock_state.return_value.get_agent.return_value = agent

                    # Session doesn't exist
                    mock_tmux.return_value.session_exists.return_value = False

                    # Run command and expect exit
                    runner = CliRunner()
                    result = runner.invoke(prompt, ["test-branch", "Message"])
                    assert result.exit_code == 1
                    # Should clean up state
                    mock_state.return_value.remove_agent.assert_called_once_with("test-branch")

    def test_prompt_send_failed(self, temp_dir):
        """Test prompt when send command fails."""
        with patch("aifleet.commands.prompt.ConfigManager") as mock_config:
            with patch("aifleet.commands.prompt.StateManager") as mock_state:
                with patch("aifleet.commands.prompt.TmuxManager") as mock_tmux:
                    # Setup mocks
                    mock_config.return_value.repo_root = temp_dir
                    mock_config.return_value.tmux_prefix = "ai_"

                    # Mock agent
                    agent = Agent(
                        branch="test-branch",
                        worktree="/path/worktree",
                        session="ai_test-branch",
                        pid=12345,
                        batch_id="batch1",
                        agent="claude",
                        created_at=datetime.now().isoformat(),
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
