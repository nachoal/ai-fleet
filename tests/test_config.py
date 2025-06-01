"""Tests for configuration management."""

import os
from pathlib import Path

import pytest

from aifleet.config import ConfigManager


class TestConfigManager:
    """Test ConfigManager functionality."""

    def test_project_root_detection(self, tmp_path):
        """Test project root detection from git repository."""
        # Create a git repo
        git_repo = tmp_path / "test-project"
        git_repo.mkdir()
        (git_repo / ".git").mkdir()

        # Change to repo directory
        original_cwd = Path.cwd()
        try:
            os.chdir(git_repo)
            config = ConfigManager()
            assert config.project_root == git_repo
            assert config.is_git_repository
        finally:
            os.chdir(original_cwd)

    def test_project_root_detection_subdirectory(self, tmp_path):
        """Test project root detection from subdirectory."""
        # Create a git repo
        git_repo = tmp_path / "test-project"
        git_repo.mkdir()
        (git_repo / ".git").mkdir()
        subdir = git_repo / "src" / "components"
        subdir.mkdir(parents=True)

        # Change to subdirectory
        original_cwd = Path.cwd()
        try:
            os.chdir(subdir)
            config = ConfigManager()
            assert config.project_root == git_repo
            assert config.is_git_repository
        finally:
            os.chdir(original_cwd)

    def test_not_git_repository(self, tmp_path):
        """Test behavior when not in a git repository."""
        original_cwd = Path.cwd()
        try:
            os.chdir(tmp_path)
            config = ConfigManager()
            assert config.project_root is None
            assert not config.is_git_repository
            assert not config.has_project_config
        finally:
            os.chdir(original_cwd)

    def test_project_config_file_path(self, tmp_path):
        """Test project configuration file path."""
        git_repo = tmp_path / "test-project"
        git_repo.mkdir()
        (git_repo / ".git").mkdir()

        config = ConfigManager(project_root=git_repo)
        expected = git_repo / ".aifleet" / "config.toml"
        assert config.project_config_file == expected

    def test_user_config_file_path(self):
        """Test user configuration file path."""
        config = ConfigManager()

        # Should respect XDG_CONFIG_HOME if set
        with pytest.MonkeyPatch.context() as mp:
            mp.setenv("XDG_CONFIG_HOME", "/custom/config")
            config = ConfigManager()
            assert config.user_config_file == Path("/custom/config/aifleet/config.toml")

    def test_config_hierarchy(self, tmp_path):
        """Test configuration value hierarchy: project > user > defaults."""
        git_repo = tmp_path / "test-project"
        git_repo.mkdir()
        (git_repo / ".git").mkdir()

        config = ConfigManager(project_root=git_repo)

        # Test default value
        assert config.get("agent.default") == "claude"

        # Create project config
        config._project_config = {"agent": {"default": "gpt4"}}
        assert config.get("agent.default") == "gpt4"

        # User config should be overridden by project
        config._user_config = {"agent": {"default": "codex"}}
        assert config.get("agent.default") == "gpt4"

    def test_initialize_project(self, tmp_path):
        """Test project initialization."""
        git_repo = tmp_path / "test-project"
        git_repo.mkdir()
        (git_repo / ".git").mkdir()

        config = ConfigManager(project_root=git_repo)
        config.initialize_project()

        assert config.has_project_config
        assert config.project_config_file.exists()

        # Check config structure
        assert config.get("project.name") == "test-project"
        assert "test-project" in config.get("project.worktree_root")

    def test_initialize_project_rails(self, tmp_path):
        """Test Rails project initialization."""
        git_repo = tmp_path / "rails-app"
        git_repo.mkdir()
        (git_repo / ".git").mkdir()

        config = ConfigManager(project_root=git_repo)
        config.initialize_project("rails")

        # Check Rails-specific defaults
        assert "config/master.key" in config.credential_files
        assert any("bundle install" in cmd for cmd in config.setup_commands)

    def test_initialize_project_already_exists(self, tmp_path):
        """Test initialization fails if already initialized."""
        git_repo = tmp_path / "test-project"
        git_repo.mkdir()
        (git_repo / ".git").mkdir()
        (git_repo / ".aifleet").mkdir()
        (git_repo / ".aifleet" / "config.toml").write_text("")

        config = ConfigManager(project_root=git_repo)

        with pytest.raises(ValueError, match="already initialized"):
            config.initialize_project()

    def test_validate_project_config(self, tmp_path):
        """Test project configuration validation."""
        git_repo = tmp_path / "test-project"
        git_repo.mkdir()
        (git_repo / ".git").mkdir()

        config = ConfigManager(project_root=git_repo)

        # Not initialized yet
        errors = config.validate()
        assert any("No project configuration" in e for e in errors)

        # Initialize and validate
        config.initialize_project()
        errors = config.validate()
        assert len(errors) == 0

    def test_backward_compatibility_properties(self, tmp_path):
        """Test backward compatibility properties."""
        git_repo = tmp_path / "test-project"
        git_repo.mkdir()
        (git_repo / ".git").mkdir()

        config = ConfigManager(project_root=git_repo)
        config.initialize_project()

        # These properties should still work
        assert config.repo_root == git_repo
        assert isinstance(config.worktree_root, Path)
        assert config.tmux_prefix == "ai_"
        assert config.default_agent == "claude"
        assert config.claude_flags == "--dangerously-skip-permissions"
        assert config.credential_files == []
        assert config.setup_commands == []
        assert config.quick_setup is False

    def test_legacy_config_migration(self, tmp_path):
        """Test migration from legacy global config."""
        # Create legacy config
        legacy_dir = tmp_path / ".ai_fleet"
        legacy_dir.mkdir()
        legacy_config = legacy_dir / "config.toml"
        legacy_config.write_text("""
repo_root = "/old/repo"
worktree_root = "/old/worktrees"
tmux_prefix = "old_"
default_agent = "oldclaude"
claude_flags = "--old-flags"
credential_files = ["old.env"]
setup_commands = ["old command"]
quick_setup = true
""")

        # Create new project
        git_repo = tmp_path / "new-project"
        git_repo.mkdir()
        (git_repo / ".git").mkdir()

        # Mock home directory
        with pytest.MonkeyPatch.context() as mp:
            mp.setattr(Path, "home", lambda: tmp_path)

            config = ConfigManager(project_root=git_repo)
            assert config.has_legacy_config()

            config.migrate_legacy_config()

            # Check migration
            assert config.get("agent.default") == "oldclaude"
            assert config.get("tmux.prefix") == "old_"
            assert "old.env" in config.credential_files
            assert legacy_config.with_suffix(".toml.backup").exists()
