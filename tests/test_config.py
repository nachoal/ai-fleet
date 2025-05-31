"""Tests for configuration management."""

from pathlib import Path

import pytest

from aifleet.config import ConfigManager


class TestConfigManager:
    """Test ConfigManager functionality."""

    def test_default_config(self, config_dir):
        """Test default configuration values."""
        config = ConfigManager(config_dir)
        
        assert config.tmux_prefix == "ai_"
        assert config.default_agent == "claude"
        assert config.claude_flags == "--dangerously-skip-permissions"
        assert config.credential_files == []
        assert config.setup_commands == []
        assert config.quick_setup is False

    def test_load_and_save(self, config_dir):
        """Test loading and saving configuration."""
        config = ConfigManager(config_dir)
        
        # Modify configuration
        config.set("tmux_prefix", "test_")
        config.set("credential_files", ["config/master.key", ".env"])
        config.save()
        
        # Load in new instance
        config2 = ConfigManager(config_dir)
        assert config2.tmux_prefix == "test_"
        assert config2.credential_files == ["config/master.key", ".env"]

    def test_get_nested(self, config_dir):
        """Test getting nested configuration values."""
        config = ConfigManager(config_dir)
        
        # Set nested value
        config.set("linear.token", "test-token")
        config.save()
        
        # Get nested value
        assert config.get("linear.token") == "test-token"
        assert config.get("linear.missing", "default") == "default"

    def test_validate_missing_repo(self, config_dir):
        """Test validation with missing repo."""
        config = ConfigManager(config_dir)
        config.set("repo_root", "/nonexistent/path")
        
        errors = config.validate()
        assert len(errors) == 1
        assert "does not exist" in errors[0]

    def test_validate_not_git_repo(self, temp_dir, config_dir):
        """Test validation with non-git directory."""
        # Create directory that's not a git repo
        fake_repo = temp_dir / "not-a-repo"
        fake_repo.mkdir()
        
        config = ConfigManager(config_dir)
        config.set("repo_root", str(fake_repo))
        
        errors = config.validate()
        assert len(errors) == 1
        assert "not a git repository" in errors[0]

    def test_validate_missing_credential_files(self, git_repo, config_dir):
        """Test validation with missing credential files."""
        config = ConfigManager(config_dir)
        config.set("repo_root", str(git_repo))
        config.set("credential_files", ["missing.key", ".env"])
        
        errors = config.validate()
        assert len(errors) == 2
        assert all("not found" in error for error in errors)

    def test_create_default_config(self, config_dir, git_repo, monkeypatch):
        """Test creating default configuration."""
        # Mock git command to return our test repo
        import subprocess
        original_run = subprocess.run
        
        def mock_run(cmd, *args, **kwargs):
            if cmd[0] == "git" and "rev-parse" in cmd:
                result = type('Result', (), {
                    'stdout': str(git_repo),
                    'returncode': 0
                })()
                return result
            return original_run(cmd, *args, **kwargs)
        
        monkeypatch.setattr(subprocess, "run", mock_run)
        
        config = ConfigManager(config_dir)
        config.create_default_config()
        
        # Should detect git repo
        assert config.repo_root == git_repo