"""Tests for the update command."""

from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from aifleet.cli import cli
from aifleet.updater import UpdateChecker, get_installation_method


def test_update_check_command():
    """Test the update --check command."""
    runner = CliRunner()

    # Mock the UpdateChecker
    with patch("aifleet.commands.update.UpdateChecker") as mock_checker:
        mock_instance = MagicMock()
        mock_instance.check_for_updates.return_value = (True, "1.0.0")
        mock_checker.return_value = mock_instance

        result = runner.invoke(cli, ["update", "--check"])

        assert result.exit_code == 0
        assert "Update available" in result.output
        assert "Run 'fleet update' to install" in result.output


def test_update_no_update_available():
    """Test when no update is available."""
    runner = CliRunner()

    with patch("aifleet.commands.update.UpdateChecker") as mock_checker:
        mock_instance = MagicMock()
        mock_instance.check_for_updates.return_value = (False, "0.1.0")
        mock_checker.return_value = mock_instance

        result = runner.invoke(cli, ["update"])

        assert result.exit_code == 0
        assert "AI Fleet is up to date" in result.output


def test_update_via_pipx():
    """Test update via pipx."""
    runner = CliRunner()

    with (
        patch("aifleet.commands.update.UpdateChecker") as mock_checker,
        patch("aifleet.commands.update.get_installation_method") as mock_method,
        patch("aifleet.commands.update.update_via_pipx") as mock_update,
    ):
        mock_instance = MagicMock()
        mock_instance.check_for_updates.return_value = (True, "1.0.0")
        mock_checker.return_value = mock_instance

        mock_method.return_value = "pipx"
        mock_update.return_value = True

        result = runner.invoke(cli, ["update"])

        assert result.exit_code == 0
        assert "Updating via pipx..." in result.output
        assert "Successfully updated AI Fleet" in result.output


def test_update_from_source():
    """Test update from source."""
    runner = CliRunner()

    with (
        patch("aifleet.commands.update.UpdateChecker") as mock_checker,
        patch("aifleet.commands.update.get_installation_method") as mock_method,
    ):
        mock_instance = MagicMock()
        mock_instance.check_for_updates.return_value = (True, "1.0.0")
        mock_checker.return_value = mock_instance

        mock_method.return_value = "source"

        result = runner.invoke(cli, ["update"])

        assert result.exit_code == 0
        assert "running from source" in result.output
        assert "git pull origin main" in result.output


def test_update_force_check():
    """Test force update check."""
    runner = CliRunner()

    with patch("aifleet.commands.update.UpdateChecker") as mock_checker:
        mock_instance = MagicMock()
        mock_instance.check_for_updates.return_value = (False, "0.1.0")
        mock_checker.return_value = mock_instance

        result = runner.invoke(cli, ["update", "--force"])

        assert result.exit_code == 0
        mock_instance.check_for_updates.assert_called_once_with(force=True)


def test_updater_cache():
    """Test the UpdateChecker cache functionality."""
    checker = UpdateChecker("0.1.0")

    # Test cache file doesn't exist
    assert not checker._is_cache_valid()

    # Test saving and loading cache
    test_data = {"latest_version": "1.0.0", "timestamp": 1234567890}
    checker._save_cache(test_data)

    # Cache should be invalid due to old timestamp
    assert not checker._is_cache_valid()


def test_get_installation_method():
    """Test installation method detection."""
    # Test with different sys.prefix values
    with (
        patch("sys.prefix", "/home/user/.local/pipx/venvs/ai-fleet"),
        patch("pathlib.Path.exists") as mock_exists,
    ):
        # Mock that .git doesn't exist to avoid source detection
        mock_exists.return_value = False
        assert get_installation_method() == "pipx"

    with patch("sys.prefix", "/usr/local"), patch("pathlib.Path.exists") as mock_exists:
        mock_exists.return_value = False
        method = get_installation_method()
        assert method == "pip"  # Should default to pip when not source
