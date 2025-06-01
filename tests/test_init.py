"""Tests for the init command."""

from pathlib import Path

from click.testing import CliRunner

from aifleet.cli import cli


def test_init_not_in_git_repo():
    """Test init fails when not in a git repository."""
    runner = CliRunner()

    with runner.isolated_filesystem():
        result = runner.invoke(cli, ["init"])

        assert result.exit_code == 1
        assert "Not in a git repository" in result.output


def test_init_basic():
    """Test basic initialization."""
    runner = CliRunner()

    with runner.isolated_filesystem():
        # Create a git repo
        Path(".git").mkdir()

        result = runner.invoke(cli, ["init"], input="y\n")

        assert result.exit_code == 0
        assert "Initializing AI Fleet" in result.output
        assert Path(".aifleet/config.toml").exists()


def test_init_with_project_type():
    """Test initialization with specific project type."""
    runner = CliRunner()

    with runner.isolated_filesystem():
        # Create a git repo
        Path(".git").mkdir()

        # Create package.json for Node.js detection
        Path("package.json").write_text("{}")

        result = runner.invoke(cli, ["init", "--type", "node"], input="y\n")

        assert result.exit_code == 0
        assert "Node.js" in result.output
        assert Path(".aifleet/config.toml").exists()


def test_init_already_initialized():
    """Test init fails when already initialized."""
    runner = CliRunner()

    with runner.isolated_filesystem():
        # Create a git repo
        Path(".git").mkdir()
        Path(".aifleet").mkdir()
        Path(".aifleet/config.toml").write_text("")

        result = runner.invoke(cli, ["init"])

        assert result.exit_code == 1
        assert "Project already initialized" in result.output


def test_init_auto_detect():
    """Test project type auto-detection."""
    runner = CliRunner()

    with runner.isolated_filesystem():
        # Create a git repo
        Path(".git").mkdir()

        # Create requirements.txt for Python detection
        Path("requirements.txt").write_text("click\n")

        result = runner.invoke(cli, ["init"], input="y\n")

        assert result.exit_code == 0
        assert "Detected project type: python" in result.output


def test_init_updates_gitignore():
    """Test that init updates .gitignore."""
    runner = CliRunner()

    with runner.isolated_filesystem():
        # Create a git repo
        Path(".git").mkdir()

        # Create existing .gitignore
        Path(".gitignore").write_text("*.pyc\n")

        result = runner.invoke(cli, ["init"], input="y\n")

        assert result.exit_code == 0

        gitignore_content = Path(".gitignore").read_text()
        assert ".aifleet/worktrees/" in gitignore_content
