"""Pytest configuration and fixtures."""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock

import pytest


@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def mock_home(temp_dir, monkeypatch):
    """Mock home directory for tests."""
    monkeypatch.setenv("HOME", str(temp_dir))
    return temp_dir


@pytest.fixture
def git_repo(temp_dir):
    """Create a temporary git repository."""
    repo_path = temp_dir / "test-repo"
    repo_path.mkdir()

    # Initialize git repo
    import subprocess

    subprocess.run(["git", "init"], cwd=repo_path, capture_output=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo_path)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo_path)

    # Create initial commit
    (repo_path / "README.md").write_text("# Test Repo")
    subprocess.run(["git", "add", "."], cwd=repo_path)
    subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=repo_path)

    return repo_path


@pytest.fixture
def config_dir(temp_dir):
    """Create a temporary config directory."""
    config_path = temp_dir / ".ai_fleet"
    config_path.mkdir()
    return config_path


@pytest.fixture
def mock_tmux_server():
    """Mock libtmux Server."""
    server = MagicMock()
    server.list_sessions.return_value = []
    server.find_where.return_value = None
    return server
