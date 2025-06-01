"""Tests for CLI commands."""

from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from aifleet.cli import cli


class TestCLI:
    """Test CLI commands."""

    def test_cli_help(self):
        """Test CLI help."""
        runner = CliRunner()
        result = runner.invoke(cli, ["--help"])

        assert result.exit_code == 0
        assert "AI Fleet" in result.output
        assert "Manage AI coding agents" in result.output

    def test_version(self):
        """Test version display."""
        runner = CliRunner()
        result = runner.invoke(cli, ["--version"])

        assert result.exit_code == 0
        assert "version" in result.output.lower()

    @patch("aifleet.cli.ConfigManager")
    def test_config_show(self, mock_config_class, temp_dir):
        """Test showing configuration."""
        # Mock config
        mock_config = MagicMock()
        mock_config.is_git_repository = True
        mock_config.has_project_config = True
        mock_config.project_root = temp_dir
        mock_config.project_config_file = temp_dir / ".aifleet" / "config.toml"
        mock_config_class.return_value = mock_config

        # Create config file
        mock_config.project_config_file.parent.mkdir(parents=True, exist_ok=True)
        mock_config.project_config_file.write_text("test = true")

        runner = CliRunner()
        result = runner.invoke(cli, ["config"])

        assert result.exit_code == 0
        assert "Configuration file:" in result.output
        assert "test = true" in result.output

    @patch("aifleet.cli.ConfigManager")
    def test_config_validate(self, mock_config_class):
        """Test validating configuration."""
        # Mock config with no errors
        mock_config = MagicMock()
        mock_config.is_git_repository = True
        mock_config.has_project_config = True
        mock_config.validate.return_value = []
        mock_config_class.return_value = mock_config

        runner = CliRunner()
        result = runner.invoke(cli, ["config", "--validate"])

        assert result.exit_code == 0
        assert "Configuration is valid" in result.output

    @patch("aifleet.cli.ConfigManager")
    def test_config_validate_errors(self, mock_config_class):
        """Test validating configuration with errors."""
        # Mock config with errors
        mock_config = MagicMock()
        mock_config.validate.return_value = [
            "repo_root does not exist",
            "Credential file not found: .env",
        ]
        mock_config_class.return_value = mock_config

        runner = CliRunner()
        result = runner.invoke(cli, ["config", "--validate"])

        assert result.exit_code == 1
        assert "Configuration errors:" in result.output
        assert "repo_root does not exist" in result.output

    @patch("subprocess.run")
    @patch("aifleet.cli.ConfigManager")
    def test_config_edit(self, mock_config_class, mock_subprocess_run, temp_dir):
        """Test editing configuration."""
        # Mock config
        mock_config = MagicMock()
        mock_config.has_project_config = True
        mock_config.project_config_file = temp_dir / ".aifleet" / "config.toml"
        mock_config_class.return_value = mock_config

        runner = CliRunner()
        result = runner.invoke(cli, ["config", "--edit"])

        assert result.exit_code == 0
        mock_subprocess_run.assert_called_once()
        # Check editor was called with config file
        call_args = mock_subprocess_run.call_args[0][0]
        assert str(mock_config.project_config_file) in call_args


class TestCreateCommand:
    """Test create command."""

    @patch("aifleet.commands.create.verify_agent_command")
    @patch("aifleet.commands.create.TmuxManager")
    @patch("aifleet.commands.create.WorktreeManager")
    @patch("aifleet.commands.create.StateManager")
    @patch("aifleet.commands.create.ensure_project_config")
    @patch("aifleet.commands.base.ensure_project_config")
    def test_create_basic(
        self,
        mock_ensure_config_base,
        mock_ensure_config_create,
        mock_state_class,
        mock_worktree_class,
        mock_tmux_class,
        mock_verify_agent,
        temp_dir,
    ):
        """Test basic agent creation."""
        # Mock config - set both patches to return the same config
        mock_config = MagicMock()
        mock_config.repo_root = temp_dir / "repo"
        mock_config.worktree_root = temp_dir / "worktrees"
        mock_config.tmux_prefix = "ai_"
        mock_config.default_agent = "claude"
        mock_config.claude_flags = "--test"
        mock_config.credential_files = []
        mock_config.setup_commands = []
        mock_config.quick_setup = False
        mock_config.project_root = temp_dir / "repo"

        mock_ensure_config_base.return_value = mock_config
        mock_ensure_config_create.return_value = mock_config

        # Mock agent verification
        mock_verify_agent.return_value = True

        # Mock state
        mock_state = MagicMock()
        mock_state.get_agent.return_value = None  # No existing agent
        mock_state_class.return_value = mock_state

        # Mock worktree
        mock_worktree = MagicMock()
        mock_worktree.setup_worktree.return_value = (
            temp_dir / "worktrees" / "test-branch"
        )
        mock_worktree_class.return_value = mock_worktree

        # Mock tmux
        mock_tmux = MagicMock()
        mock_session = MagicMock()
        mock_tmux.create_session.return_value = mock_session
        mock_tmux._session_name.return_value = "ai_test-branch"
        mock_tmux.send_command.return_value = True
        mock_tmux.get_session_info.return_value = {"pid": 12345}
        mock_tmux_class.return_value = mock_tmux

        runner = CliRunner()
        result = runner.invoke(
            cli, ["create", "test-branch", "--prompt", "Test prompt"]
        )

        assert result.exit_code == 0
        assert "Agent created successfully" in result.output

        # Verify calls
        mock_worktree.setup_worktree.assert_called_once()
        mock_tmux.create_session.assert_called_once()
        mock_tmux.send_command.assert_called_once()
        mock_state.add_agent.assert_called_once()

    @patch("aifleet.commands.create.verify_agent_command")
    @patch("aifleet.commands.create.StateManager")
    @patch("aifleet.commands.create.ensure_project_config")
    @patch("aifleet.commands.base.ensure_project_config")
    def test_create_existing_agent(
        self,
        mock_ensure_config_base,
        mock_ensure_config_create,
        mock_state_class,
        mock_verify_agent,
        temp_dir,
    ):
        """Test creating agent that already exists."""
        # Mock config
        mock_config = MagicMock()
        mock_config.project_root = temp_dir
        mock_config.repo_root = temp_dir
        mock_config.default_agent = "claude"
        mock_ensure_config_base.return_value = mock_config
        mock_ensure_config_create.return_value = mock_config

        # Mock agent verification
        mock_verify_agent.return_value = True

        # Mock existing agent
        mock_state = MagicMock()
        mock_state.get_agent.return_value = MagicMock()  # Agent exists
        mock_state_class.return_value = mock_state

        runner = CliRunner()
        result = runner.invoke(cli, ["create", "existing-branch"])

        assert result.exit_code == 1
        assert "Agent already exists" in result.output


class TestListCommand:
    """Test list command."""

    @patch("aifleet.commands.list.TmuxManager")
    @patch("aifleet.commands.list.StateManager")
    @patch("aifleet.commands.list.ensure_project_config")
    @patch("aifleet.commands.base.ensure_project_config")
    def test_list_empty(
        self,
        mock_ensure_config_base,
        mock_ensure_config_list,
        mock_state_class,
        mock_tmux_class,
        temp_dir,
    ):
        """Test listing with no agents."""
        # Mock config
        mock_config = MagicMock()
        mock_config.project_root = temp_dir
        mock_ensure_config_base.return_value = mock_config
        mock_ensure_config_list.return_value = mock_config

        # Mock empty state
        mock_state = MagicMock()
        mock_state.list_agents.return_value = []
        mock_state_class.return_value = mock_state

        # Mock tmux
        mock_tmux = MagicMock()
        mock_tmux.list_sessions.return_value = []
        mock_tmux_class.return_value = mock_tmux

        runner = CliRunner()
        result = runner.invoke(cli, ["list"])

        assert result.exit_code == 0
        assert "No active agents" in result.output

    @patch("aifleet.commands.list.psutil")
    @patch("aifleet.commands.list.TmuxManager")
    @patch("aifleet.commands.list.StateManager")
    @patch("aifleet.commands.list.ensure_project_config")
    @patch("aifleet.commands.base.ensure_project_config")
    def test_list_agents(
        self,
        mock_ensure_config_base,
        mock_ensure_config_list,
        mock_state_class,
        mock_tmux_class,
        mock_psutil,
        temp_dir,
    ):
        """Test listing active agents."""
        from datetime import datetime

        from aifleet.state import Agent

        # Mock config
        mock_config = MagicMock()
        mock_config.project_root = temp_dir
        mock_ensure_config_base.return_value = mock_config
        mock_ensure_config_list.return_value = mock_config

        # Mock agents
        agents = [
            Agent(
                branch="branch1",
                worktree="/path1",
                session="ai_branch1",
                batch_id="batch1",
                agent="claude",
                created_at=datetime.now().isoformat(),
                pid=12345,
            ),
            Agent(
                branch="branch2",
                worktree="/path2",
                session="ai_branch2",
                batch_id="batch1",
                agent="claude",
                created_at=datetime.now().isoformat(),
                pid=12346,
            ),
        ]

        mock_state = MagicMock()
        mock_state.list_agents.return_value = agents
        mock_state_class.return_value = mock_state

        # Mock tmux sessions
        mock_tmux = MagicMock()
        mock_tmux.list_sessions.return_value = [
            ("ai_branch1", 12345),
            ("ai_branch2", 12346),
        ]
        mock_tmux_class.return_value = mock_tmux

        # Mock process stats
        mock_process = MagicMock()
        mock_process.cpu_percent.return_value = 10.5
        mock_process.memory_info.return_value.rss = 100 * 1024 * 1024  # 100 MB
        mock_psutil.Process.return_value = mock_process

        runner = CliRunner()
        result = runner.invoke(cli, ["list"])

        assert result.exit_code == 0
        assert "BRANCH" in result.output
        assert "branch1" in result.output
        assert "branch2" in result.output
        assert "active" in result.output
        assert "10.5" in result.output  # CPU
        assert "100" in result.output  # Memory

    @patch("aifleet.commands.list.psutil")
    @patch("aifleet.commands.list.TmuxManager")
    @patch("aifleet.commands.list.StateManager")
    @patch("aifleet.commands.list.ensure_project_config")
    @patch("aifleet.commands.base.ensure_project_config")
    def test_list_grouped(
        self,
        mock_ensure_config_base,
        mock_ensure_config_list,
        mock_state_class,
        mock_tmux_class,
        mock_psutil,
        temp_dir,
    ):
        """Test listing agents grouped by batch."""
        from datetime import datetime

        from aifleet.state import Agent

        # Mock config
        mock_config = MagicMock()
        mock_config.project_root = temp_dir
        mock_ensure_config_base.return_value = mock_config
        mock_ensure_config_list.return_value = mock_config

        # Mock agents in different batches
        agents = [
            Agent(
                branch=f"branch{i}",
                worktree=f"/path{i}",
                session=f"ai_branch{i}",
                batch_id="batch1" if i < 2 else "batch2",
                agent="claude",
                created_at=datetime.now().isoformat(),
                pid=12345 + i,
            )
            for i in range(4)
        ]

        mock_state = MagicMock()
        mock_state.list_agents.return_value = agents
        mock_state_class.return_value = mock_state

        # Mock tmux
        mock_tmux = MagicMock()
        mock_tmux.list_sessions.return_value = [
            (f"ai_branch{i}", 12345 + i) for i in range(4)
        ]
        mock_tmux_class.return_value = mock_tmux

        # Mock process stats
        mock_psutil.Process.side_effect = lambda pid: MagicMock(
            cpu_percent=lambda interval: 5.0,
            memory_info=lambda: MagicMock(rss=50 * 1024 * 1024),
        )

        runner = CliRunner()
        result = runner.invoke(cli, ["list", "--grouped"])

        assert result.exit_code == 0
        assert "batch1" in result.output
        assert "batch2" in result.output
        assert "Batches: 2" in result.output
