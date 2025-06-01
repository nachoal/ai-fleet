"""Tests for the kill command."""

from datetime import datetime
from pathlib import Path
from unittest.mock import patch

from click.testing import CliRunner

from aifleet.commands.kill import kill
from aifleet.state import Agent


class TestKillCommand:
    """Test the kill command."""

    def test_kill_single_agent(self, temp_dir):
        """Test killing a single agent."""
        with patch(
            "aifleet.commands.base.ensure_project_config"
        ) as mock_ensure_config_base:
            with patch(
                "aifleet.commands.kill.ensure_project_config"
            ) as mock_ensure_config_kill:
                with patch("aifleet.commands.kill.StateManager") as mock_state:
                    with patch("aifleet.commands.kill.TmuxManager") as mock_tmux:
                        with patch(
                            "aifleet.commands.kill.WorktreeManager"
                        ) as mock_worktree:
                            with patch(
                                "aifleet.commands.kill.click.confirm", return_value=True
                            ):
                                # Setup mocks - patch both base and kill module
                                mock_config = mock_ensure_config_base.return_value
                                mock_ensure_config_kill.return_value = mock_config
                                mock_config.repo_root = temp_dir
                                mock_config.project_root = temp_dir
                                mock_config.worktree_root = temp_dir / "worktrees"
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
                                mock_state.return_value.list_agents.return_value = [
                                    agent
                                ]

                                # Mock tmux operations
                                mock_tmux.return_value.session_exists.return_value = (
                                    True
                                )
                                mock_tmux.return_value.kill_session.return_value = True
                                mock_worktree_rm = (
                                    mock_worktree.return_value.remove_worktree
                                )
                                mock_worktree_rm.return_value = True

                                # Mock Path.exists() to return True
                                with patch("pathlib.Path.exists", return_value=True):
                                    # Run command with --force flag
                                    runner = CliRunner()
                                    result = runner.invoke(
                                        kill, ["--force", "test-branch"]
                                    )
                                    assert result.exit_code == 0

                                    # Verify calls
                                    mock_tmux.return_value.kill_session.assert_called_once_with(
                                        "test-branch"
                                    )
                                    mock_worktree.return_value.remove_worktree.assert_called_once_with(
                                        Path("/path/worktree"), force=False
                                    )
                                    mock_state.return_value.remove_agent.assert_called_once_with(
                                        "test-branch"
                                    )

    def test_kill_with_glob_pattern(self, temp_dir):
        """Test killing agents with glob pattern."""
        with patch(
            "aifleet.commands.base.ensure_project_config"
        ) as mock_ensure_config_base:
            with patch(
                "aifleet.commands.kill.ensure_project_config"
            ) as mock_ensure_config_kill:
                with patch("aifleet.commands.kill.StateManager") as mock_state:
                    with patch("aifleet.commands.kill.TmuxManager") as mock_tmux:
                        with patch(
                            "aifleet.commands.kill.WorktreeManager"
                        ) as mock_worktree:
                            with patch(
                                "aifleet.commands.kill.click.confirm", return_value=True
                            ):
                                # Setup mocks - patch both base and kill module
                                mock_config = mock_ensure_config_base.return_value
                                mock_ensure_config_kill.return_value = mock_config
                                mock_config.repo_root = temp_dir
                                mock_config.project_root = temp_dir
                                mock_config.worktree_root = temp_dir / "worktrees"

                                # Mock multiple agents
                                agents = [
                                    Agent(
                                        branch="auth-refactor-A",
                                        worktree="/path/worktree1",
                                        session="ai_auth-refactor-A",
                                        batch_id="batch1",
                                        agent="claude",
                                        created_at=datetime.now().isoformat(),
                                        pid=12345,
                                    ),
                                    Agent(
                                        branch="auth-refactor-B",
                                        worktree="/path/worktree2",
                                        session="ai_auth-refactor-B",
                                        batch_id="batch1",
                                        agent="claude",
                                        created_at=datetime.now().isoformat(),
                                        pid=12346,
                                    ),
                                    Agent(
                                        branch="other-branch",
                                        worktree="/path/worktree3",
                                        session="ai_other-branch",
                                        batch_id="batch2",
                                        agent="claude",
                                        created_at=datetime.now().isoformat(),
                                        pid=12347,
                                    ),
                                ]
                                mock_state.return_value.list_agents.return_value = (
                                    agents
                                )

                                # Mock tmux operations
                                mock_tmux.return_value.session_exists.return_value = (
                                    True
                                )
                                mock_tmux.return_value.kill_session.return_value = True
                                mock_worktree_rm = (
                                    mock_worktree.return_value.remove_worktree
                                )
                                mock_worktree_rm.return_value = True

                                # Mock Path.exists() to return True
                                with patch("pathlib.Path.exists", return_value=True):
                                    # Run command with glob pattern and --force flag
                                    runner = CliRunner()
                                    result = runner.invoke(
                                        kill, ["--force", "auth-refactor-*"]
                                    )
                                    assert result.exit_code == 0

                                    # Should kill only matching agents
                                    assert (
                                        mock_tmux.return_value.kill_session.call_count
                                        == 2
                                    )
                                    assert (
                                        mock_state.return_value.remove_agent.call_count
                                        == 2
                                    )
                                    mock_state.return_value.remove_agent.assert_any_call(
                                        "auth-refactor-A"
                                    )
                                    mock_state.return_value.remove_agent.assert_any_call(
                                        "auth-refactor-B"
                                    )

    def test_kill_batch(self, temp_dir):
        """Test killing all agents in a batch."""
        with patch(
            "aifleet.commands.base.ensure_project_config"
        ) as mock_ensure_config_base:
            with patch(
                "aifleet.commands.kill.ensure_project_config"
            ) as mock_ensure_config_kill:
                with patch("aifleet.commands.kill.StateManager") as mock_state:
                    with patch("aifleet.commands.kill.TmuxManager") as mock_tmux:
                        with patch(
                            "aifleet.commands.kill.WorktreeManager"
                        ) as mock_worktree:
                            with patch(
                                "aifleet.commands.kill.click.confirm", return_value=True
                            ):
                                # Setup mocks - patch both base and kill module
                                mock_config = mock_ensure_config_base.return_value
                                mock_ensure_config_kill.return_value = mock_config
                                mock_config.repo_root = temp_dir
                                mock_config.project_root = temp_dir
                                mock_config.worktree_root = temp_dir / "worktrees"

                                # Mock agents in batch
                                agents = [
                                    Agent(
                                        branch="branch1",
                                        worktree="/path/worktree1",
                                        session="ai_branch1",
                                        batch_id="batch1",
                                        agent="claude",
                                        created_at=datetime.now().isoformat(),
                                        pid=12345,
                                    ),
                                    Agent(
                                        branch="branch2",
                                        worktree="/path/worktree2",
                                        session="ai_branch2",
                                        batch_id="batch1",
                                        agent="claude",
                                        created_at=datetime.now().isoformat(),
                                        pid=12346,
                                    ),
                                ]
                                mock_state.return_value.list_agents.return_value = (
                                    agents
                                )

                                # Mock tmux operations
                                mock_tmux.return_value.session_exists.return_value = (
                                    True
                                )
                                mock_tmux.return_value.kill_session.return_value = True
                                mock_worktree_rm = (
                                    mock_worktree.return_value.remove_worktree
                                )
                                mock_worktree_rm.return_value = True

                                # Mock Path.exists() to return True
                                with patch("pathlib.Path.exists", return_value=True):
                                    # Run command with batch and --force flags
                                    runner = CliRunner()
                                    result = runner.invoke(
                                        kill, ["--force", "--batch", "batch1"]
                                    )
                                    assert result.exit_code == 0

                                    # Should kill all agents in batch
                                    assert (
                                        mock_tmux.return_value.kill_session.call_count
                                        == 2
                                    )
                                    assert (
                                        mock_state.return_value.remove_agent.call_count
                                        == 2
                                    )

    def test_kill_force_no_confirmation(self, temp_dir):
        """Test force kill without confirmation."""
        with patch(
            "aifleet.commands.base.ensure_project_config"
        ) as mock_ensure_config_base:
            with patch(
                "aifleet.commands.kill.ensure_project_config"
            ) as mock_ensure_config_kill:
                with patch("aifleet.commands.kill.StateManager") as mock_state:
                    with patch("aifleet.commands.kill.TmuxManager") as mock_tmux:
                        with patch(
                            "aifleet.commands.kill.WorktreeManager"
                        ) as mock_worktree:
                            with patch(
                                "aifleet.commands.kill.click.confirm"
                            ) as mock_confirm:
                                # Setup mocks - patch both base and kill module
                                mock_config = mock_ensure_config_base.return_value
                                mock_ensure_config_kill.return_value = mock_config
                                mock_config.repo_root = temp_dir
                                mock_config.project_root = temp_dir
                                mock_config.worktree_root = temp_dir / "worktrees"

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
                                mock_state.return_value.list_agents.return_value = [
                                    agent
                                ]

                                # Mock tmux operations
                                mock_tmux.return_value.session_exists.return_value = (
                                    True
                                )
                                mock_tmux.return_value.kill_session.return_value = True
                                mock_worktree_rm = (
                                    mock_worktree.return_value.remove_worktree
                                )
                                mock_worktree_rm.return_value = True

                                # Mock Path.exists() to return True
                                with patch("pathlib.Path.exists", return_value=True):
                                    # Run command with force flag
                                    runner = CliRunner()
                                    result = runner.invoke(
                                        kill, ["--force", "test-branch"]
                                    )
                                    assert result.exit_code == 0

                                    # Should not ask for confirmation
                                    mock_confirm.assert_not_called()
                                    # But should still kill
                                    mock_tmux.return_value.kill_session.assert_called_once()

    def test_kill_no_agents_found(self, temp_dir):
        """Test kill when no agents match."""
        with patch(
            "aifleet.commands.base.ensure_project_config"
        ) as mock_ensure_config_base:
            with patch(
                "aifleet.commands.kill.ensure_project_config"
            ) as mock_ensure_config_kill:
                with patch("aifleet.commands.kill.StateManager") as mock_state:
                    with patch("aifleet.commands.kill.TmuxManager"):
                        with patch("aifleet.commands.kill.WorktreeManager"):
                            # Setup mocks - patch both base and kill module
                            mock_config = mock_ensure_config_base.return_value
                            mock_ensure_config_kill.return_value = mock_config
                            mock_config.repo_root = temp_dir
                            mock_config.project_root = temp_dir
                            mock_state.return_value.list_agents.return_value = []

                            # Run command with --force flag and expect exit
                            runner = CliRunner()
                            result = runner.invoke(kill, ["--force", "nonexistent"])
                            assert result.exit_code == 1

    def test_kill_cancelled_by_user(self, temp_dir):
        """Test kill cancelled by user confirmation."""
        with patch(
            "aifleet.commands.base.ensure_project_config"
        ) as mock_ensure_config_base:
            with patch(
                "aifleet.commands.kill.ensure_project_config"
            ) as mock_ensure_config_kill:
                with patch("aifleet.commands.kill.StateManager") as mock_state:
                    with patch("aifleet.commands.kill.TmuxManager"):
                        with patch("aifleet.commands.kill.WorktreeManager"):
                            with patch(
                                "aifleet.commands.kill.click.confirm",
                                return_value=False,
                            ):
                                # Setup mocks - patch both base and kill module
                                mock_config = mock_ensure_config_base.return_value
                                mock_ensure_config_kill.return_value = mock_config
                                mock_config.repo_root = temp_dir
                                mock_config.project_root = temp_dir

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
                                mock_state.return_value.list_agents.return_value = [
                                    agent
                                ]

                                # Run command and expect exit
                                runner = CliRunner()
                                result = runner.invoke(kill, ["test-branch"])
                                assert result.exit_code == 0
                                # Should not kill anything since user cancelled
