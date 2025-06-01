"""Tests for tmux module."""

from unittest.mock import MagicMock, patch

from aifleet.tmux import TmuxManager


class TestTmuxManager:
    """Tests for TmuxManager class."""

    def test_get_pane_content_success(self):
        """Test successful pane content capture."""
        tmux_mgr = TmuxManager()

        # Mock subprocess.run to return pane content
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "Human: help me with this code\n$"

        with patch("subprocess.run", return_value=mock_result) as mock_run:
            content = tmux_mgr.get_pane_content("feature-branch")

            # Verify the command was called correctly
            mock_run.assert_called_once()
            args = mock_run.call_args[0][0]
            assert args == ["tmux", "capture-pane", "-t", "ai_feature-branch", "-p"]

            # Verify content was returned
            assert content == "Human: help me with this code\n$"

    def test_get_pane_content_failure(self):
        """Test pane content capture failure."""
        tmux_mgr = TmuxManager()

        # Mock subprocess.run to fail
        mock_result = MagicMock()
        mock_result.returncode = 1

        with patch("subprocess.run", return_value=mock_result):
            content = tmux_mgr.get_pane_content("feature-branch")
            assert content is None

    def test_get_pane_content_exception(self):
        """Test pane content capture with exception."""
        tmux_mgr = TmuxManager()

        # Mock subprocess.run to raise exception
        with patch("subprocess.run", side_effect=Exception("tmux error")):
            content = tmux_mgr.get_pane_content("feature-branch")
            assert content is None

    def test_get_agent_status_dead(self, mock_tmux_server):
        """Test agent status when session doesn't exist."""
        tmux_mgr = TmuxManager()
        tmux_mgr.server = mock_tmux_server

        # Session doesn't exist
        mock_tmux_server.find_where.return_value = None

        status = tmux_mgr.get_agent_status("feature-branch")
        assert status == "dead"

    def test_get_agent_status_unknown(self, mock_tmux_server):
        """Test agent status when pane content can't be captured."""
        tmux_mgr = TmuxManager()
        tmux_mgr.server = mock_tmux_server

        # Session exists
        mock_tmux_server.find_where.return_value = MagicMock()

        # But pane content capture fails
        with patch.object(tmux_mgr, "get_pane_content", return_value=None):
            status = tmux_mgr.get_agent_status("feature-branch")
            assert status == "unknown"

    def test_get_agent_status_ready(self, mock_tmux_server):
        """Test agent status when waiting for input."""
        tmux_mgr = TmuxManager()
        tmux_mgr.server = mock_tmux_server

        # Session exists
        mock_tmux_server.find_where.return_value = MagicMock()

        # Test various ready states
        ready_contents = [
            "Human: help me\n$",
            "some output\n>",
            "prompt:",
            "Human: what's next?",
            "/path/to/project $ ",
        ]

        for content in ready_contents:
            with patch.object(tmux_mgr, "get_pane_content", return_value=content):
                status = tmux_mgr.get_agent_status("feature-branch")
                assert status == "ready", f"Failed for content: {content}"

    def test_get_agent_status_running(self, mock_tmux_server):
        """Test agent status when Claude is running."""
        tmux_mgr = TmuxManager()
        tmux_mgr.server = mock_tmux_server

        # Session exists
        mock_tmux_server.find_where.return_value = MagicMock()

        # Test various running states
        running_contents = [
            "I'll help you with that code\nesc to interrupt",
            "Thinking about the problem...",
            "Let me analyze this",
            "I'm going to check the files",
            "Looking at the codebase",
            "Searching for the issue",
            "Processing your request",
            "Analyzing the error",
        ]

        for content in running_contents:
            with patch.object(tmux_mgr, "get_pane_content", return_value=content):
                status = tmux_mgr.get_agent_status("feature-branch")
                assert status == "running", f"Failed for content: {content}"

    def test_get_agent_status_idle(self, mock_tmux_server):
        """Test agent status when idle."""
        tmux_mgr = TmuxManager()
        tmux_mgr.server = mock_tmux_server

        # Session exists
        mock_tmux_server.find_where.return_value = MagicMock()

        # Test idle state - has content but not running or ready
        idle_content = (
            "Some previous output that doesn't match any patterns\nNo clear prompt here"
        )

        with patch.object(tmux_mgr, "get_pane_content", return_value=idle_content):
            status = tmux_mgr.get_agent_status("feature-branch")
            assert status == "idle"

        # Test idle with minimal content
        with patch.object(tmux_mgr, "get_pane_content", return_value="short"):
            status = tmux_mgr.get_agent_status("feature-branch")
            assert status == "idle"
